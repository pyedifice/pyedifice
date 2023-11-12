from typing import TYPE_CHECKING
from typing_extensions import Self

from ..qt import QT_VERSION
if QT_VERSION == "PyQt6" and not TYPE_CHECKING:
    from PyQt6.QtWidgets import QGridLayout, QWidget
else:
    from PySide6.QtWidgets import QGridLayout, QWidget

from .._component import Element, BaseElement, _CommandType
from .base_components import QtWidgetElement

def _get_tablerowcolumn(c:Element) -> tuple[int,int]:
    """
    Sometimes it’s on the QtWidgetElement, sometimes on the Element’s _edifice_internal_parent.

    We need it, so crash if we don't find it.
    We can proceed without a _key but not without a _tablerowcolumn
    """
    if hasattr(c, "_tablerowcolumn"):
        return c.__getattribute__("_tablerowcolumn")
    else:
        return c._edifice_internal_parent.__getattribute__("_tablerowcolumn")

def _get_key(c:Element, default:str = "") -> str:
    """
    Sometimes it’s on the QtWidgetElement, sometimes on the Element’s _edifice_internal_parent.
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

class _TableGridViewRow(BaseElement):
    """
    Row Element of a :class:`TableGridView`.

    This Element has no Qt instantiation.

    Hooks cannot be used in this Element.
    """

    def __init__(self, tgv: "TableGridView"):
        super().__init__()
        self._table_grid_view: "TableGridView" = tgv
        self._column_current: int = 0
        """The current column in the context of the TableGridView render"""

    def __enter__(self: Self) -> Self:
        self._column_current = 0
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(args)
        children = self._props.get("children", [])
        for child in children:
            child.__setattr__("_tablerowcolumn", (self._table_grid_view._row_current,self._column_current))
            self._column_current += 1
        self._table_grid_view._row_current += 1


    def _qt_update_commands(
        self,
        children, # : list[_WidgetTree],
        newprops,
        newstate
    ):
        # This element has no Qt underlying so it has nothing to do except store
        # the children of the row.
        # The _qt_update_commands for TableGridView will render the children.
        return []

    # def render(self):

class TableGridView(QtWidgetElement):
    """Table-style grid layout widget. The underlying
    `QGridLayout <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html>`_
    displays its children as aligned rows of columns.

    This component has similar behavior to an `HTML
    table <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/table>`_.
    Each column will be the width of its widest child. Each row will be the
    height of its tallest child.

    The only type of child :class:`Element` allowed in a :class:`TableGridView` is
    the row Element returned by the :func:`row` method. The :func:`row`
    Element establishes a row in the table, and may have children of
    any type of :class:`Element`.

    Every child Element must have a unique key.

    Example::

        with TableGridView() as tgv:
            with tgv.row():
                Label(text="row 0 column 0").set_key("a")
                Label(text="row 0 column 1").set_key("b")
            with tgv.row():
                Label(text="row 1 column 0").set_key("c")
                with ButtonView().set_key("d"):
                    Label(text="row 1 column 1")

    Args:
        row_stretch: Rows stretch size in proportion to the corresponding
            int in this list.
            See `setRowStretch <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.PySide6.QtWidgets.QGridLayout.setRowStretch>`_
        column_stretch: Columns stretch size in proportion to the corresponding
            int in this list.
            See `setColumnStretch <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.PySide6.QtWidgets.QGridLayout.setColumnStretch>`_
        row_minheight: Row minimum height corresponding to the int in this list.
            See `setRowMinimumHeight <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.PySide6.QtWidgets.QGridLayout.setRowMinimumHeight>`_
        column_minwidth: Column minimum width corresponding the int in this list.
            See `setColumnMinimumWidth <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.PySide6.QtWidgets.QGridLayout.setColumnMinimumWidth>`_

    """

    def __init__(
            self,
            row_stretch : list[int] = [], # noqa: B006
            column_stretch : list[int] = [], # noqa: B006
            row_minheight : list[int] = [], # noqa: B006
            column_minwidth : list[int] = [], # noqa: B006
            **kwargs,
        ):
        self._register_props({
            "row_stretch": row_stretch,
            "column_stretch": column_stretch,
            "row_minheight": row_minheight,
            "column_minwidth": column_minwidth,
        })
        self._register_props(kwargs)
        self.underlying = None
        self._widget_children_dict = {}
        """Like _LinearView._widget_children"""
        self._row_stretch = row_stretch
        self._column_stretch = column_stretch
        self._row_minheight = row_minheight
        self._column_minwidth = column_minwidth
        self._row_current: int = 0
        """The current row in the context of the TableGridView render"""
        super().__init__(**kwargs)

    def row(self):
        return _TableGridViewRow(self)

    def __enter__(self: Self) -> Self:
        # Reset the current row to 0 for the current render.
        self._row_current = 0
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(args)

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
        # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.PySide6.QtWidgets.QGridLayout.addWidget
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
        assert layoutitem is not None
        widget = layoutitem.widget()
        assert widget is not None
        widget.deleteLater()
        self.underlying_layout.removeItem(layoutitem)

    def _qt_update_commands(
        self,
        children, # : list[_WidgetTree],
        newprops,
        newstate
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None

        # The direct children of this Element are TableGridViewRow_, but
        # the TableGridViewRow_ doesn't have a Qt instantiation so we
        # want to treat the TableGridViewRow_ children as the children of
        # the TableGridView.
        children_of_rows = list()
        for c in children:
            children_of_rows.extend(c.children)

        newchildren = _childdict(children_of_rows)

        old_keys = self._widget_children_dict.keys()
        new_keys = newchildren.keys()

        old_deletions = old_keys - new_keys
        new_additions = new_keys - old_keys

        commands: list[_CommandType] = []
        for row,column,_key in old_deletions:
            commands.append(_CommandType(self._delete_child, self._widget_children_dict[(row,column,_key)], row, column))
            # Is this del doing anything?
            del self._widget_children_dict[(row,column,_key)]

        for row,column,_key in new_additions:
            commands.append(_CommandType(self._add_child, newchildren[(row,column,_key)], row, column))

        self._widget_children_dict = newchildren

        # Pass the self.underlying_layout if we want it to be styled with the style props?
        # Like this:
        # # commands.extend(super()._qt_update_commands
        # # (children, newprops, newstate, self.underlying, self.underlying_layout))
        commands.extend(super()._qt_update_commands(children_of_rows, newprops, newstate, self.underlying, None))
        for prop in newprops:
            if prop == "row_stretch":
                commands.append(_CommandType(self._set_row_stretch, newprops[prop]))
            elif prop == "column_stretch":
                commands.append(_CommandType(self._set_column_stretch, newprops[prop]))
            elif prop == "row_minheight":
                commands.append(_CommandType(self._set_row_minheight, newprops[prop]))
            elif prop == "column_minwidth":
                commands.append(_CommandType(self._set_column_minwidth, newprops[prop]))

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
