from ..qt import QT_VERSION
if QT_VERSION == "PyQt6":
    from PyQt6.QtWidgets import QGridLayout, QWidget
else:
    from PySide6.QtWidgets import QGridLayout, QWidget

from .._component import Component
from ..base_components import QtWidgetComponent, register_props

def TableChildren(children: list[list[Component]]) -> list[Component]:
    """
    Convert a column list of row lists of :code:`Component` into the
    children list for a :class:`TableGridView`.
    """
    children_ = []
    for row, childrow in enumerate(children):
        for column, child in enumerate(childrow):
            # TODO _tablerowcolumn is terrible and we need a better solution.
            child.__setattr__("_tablerowcolumn", (row,column))
            children_.append(child)
    return children_

def _get_tablerowcolumn(c:Component):
    """
    Sometimes it’s on the QtWidgetComponent, sometimes on the Component’s _edifice_internal_parent.

    We need it, so crash if we don't find it.
    We can proceed without a _key but not without a _tablerowcolumn
    """
    if hasattr(c, "_tablerowcolumn"):
        return c.__getattribute__("_tablerowcolumn")
    else:
        return c._edifice_internal_parent.__getattribute__("_tablerowcolumn")

def _get_key(c:Component, default:str = ""):
    """
    Sometimes it’s on the QtWidgetComponent, sometimes on the Component’s _edifice_internal_parent.
    """
    if hasattr(c, "_key"):
        # We can proceed without a _key but not without a _tablerowcolumn
        return c.__getattribute__("_key")
    elif hasattr(c._edifice_internal_parent, "_key"):
        return c._edifice_internal_parent.__getattribute__("_key")
    else:
        return default

def _childdict(children):
    """
    Produce a dictionary of child components keyed by tuple (row,column,_key).
    """
    d = {}
    for child in children:
        row,column = _get_tablerowcolumn(child.component)
        key = _get_key(child.component)
        d[(row,column,key)] = child.component
    return d

class TableGridView(QtWidgetComponent):
    """Table-style GridLayout widget. Displays its children as aligned rows of columns.

    This component has similar behavior to an `HTML
    table <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/table>`_.
    Each column will be the width of its widest child. Each row will be the
    height of its tallest child.

    The children must be passed with the :func:`TableChildren` function as
    a column list of row lists containing children.

    Example::

        TableGridView()(*TableChildren([
            [Label(text="row 0 column 0").set_key("k1"), Label(text="row 0 column 1").set_key("k2")],
            [Label(text="row 1 column 0").set_key("k3"), Label(text="row 1 column 1").set_key("k4")],
        ]))

    Args:
        row_stretch: See `setRowStretch <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.PySide6.QtWidgets.QGridLayout.setRowStretch>`_
        column_stretch: See `setColumnStretch <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.PySide6.QtWidgets.QGridLayout.setColumnStretch>`_
        row_minheight: See `setRowMinimumHeight <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.PySide6.QtWidgets.QGridLayout.setRowMinimumHeight>`_
        column_minwidth: See `setColumnMinimumWidth <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.PySide6.QtWidgets.QGridLayout.setColumnMinimumWidth>`_

    """

    @register_props
    def __init__(
            self,
            row_stretch : list[int] = [], # noqa: B006
            column_stretch : list[int] = [], # noqa: B006
            row_minheight : list[int] = [], # noqa: B006
            column_minwidth : list[int] = [], # noqa: B006
            **kwargs,
        ):
        self.underlying = None
        self._widget_children_dict = {}
        self._row_stretch = row_stretch
        self._column_stretch = column_stretch
        self._row_minheight = row_minheight
        self._column_minwidth = column_minwidth
        super().__init__(**kwargs)

    def _initialize(self):
        self.underlying = QWidget()
        self.underlying_layout = QGridLayout()
        self.underlying.setObjectName(str(id(self)))
        self.underlying.setLayout(self.underlying_layout)
        self.underlying_layout.setContentsMargins(0, 0, 0, 0)
        self.underlying_layout.setSpacing(0)

    def _clear(self):
        while self.underlying_layout.takeAt(0) is not None:
            pass

    def _add_child(self, child_component, row:int, column:int):
        self.underlying_layout.addWidget(child_component.underlying, row, column)
        if len(self._row_stretch) > row:
            self.underlying_layout.setRowStretch(row, self._row_stretch[row])
        if len(self._column_stretch) > column:
            self.underlying_layout.setColumnStretch(column, self._column_stretch[column])
        if len(self._row_minheight) > row:
            self.underlying_layout.setRowMinimumHeight(row, self._row_minheight[row])
        if len(self._column_minwidth) > column:
            self.underlying_layout.setColumnMinimumWidth(column, self._column_minwidth[column])

    def _delete_child(self, child_component, row:int, column:int):
        layoutitem = self.underlying_layout.itemAtPosition(row, column)
        layoutitem.widget().deleteLater()
        self.underlying_layout.removeItem(layoutitem)

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()

        newchildren = _childdict(children)

        old_keys = self._widget_children_dict.keys()
        new_keys = newchildren.keys()

        old_deletions = old_keys - new_keys
        new_additions = new_keys - old_keys

        commands = []
        for row,column,_key in old_deletions:
            commands.append((self._delete_child, self._widget_children_dict[(row,column,_key)], row, column))
            # Is this del doing anything?
            del self._widget_children_dict[(row,column,_key)]

        for row,column,_key in new_additions:
            commands.append((self._add_child, newchildren[(row,column,_key)], row, column))

        self._widget_children_dict = newchildren

        # Pass the self.underlying_layout if we want it to be styled with the style props?
        # Like this:
        # # commands.extend(super()._qt_update_commands
        # # (children, newprops, newstate, self.underlying, self.underlying_layout))
        commands.extend(super()._qt_update_commands(children, newprops, newstate, self.underlying, None))
        for prop in newprops:
            if prop == "row_stretch":
                commands.append((self._set_row_stretch, newprops[prop]))
            elif prop == "column_stretch":
                commands.append((self._set_column_stretch, newprops[prop]))
            elif prop == "row_minheight":
                commands.append((self._set_row_minheight, newprops[prop]))
            elif prop == "column_minwidth":
                commands.append((self._set_column_minwidth, newprops[prop]))

        return commands

    def _set_row_stretch(self, row_stretch):
        self._row_stretch = row_stretch
        for i,stretch in enumerate(row_stretch[:self.underlying_layout.rowCount()]):
            self.underlying_layout.setRowStretch(i, stretch)

    def _set_column_stretch(self, column_stretch):
        self._column_stretch = column_stretch
        for i,stretch in enumerate(column_stretch[:self.underlying_layout.columnCount()]):
            self.underlying_layout.setColumnStretch(i, stretch)

    def _set_row_minheight(self, row_minheight):
        self._row_minheight = row_minheight
        for i,minheight in enumerate(row_minheight[:self.underlying_layout.rowCount()]):
            self.underlying_layout.setRowMinimumHeight(i, minheight)

    def _set_column_minwidth(self, column_minwidth):
        self._column_minwidth = column_minwidth
        for i,minwidth in enumerate(column_minwidth[:self.underlying_layout.columnCount()]):
            self.underlying_layout.setColumnMinimumWidth(i, minwidth)
