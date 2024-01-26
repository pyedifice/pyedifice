from typing import TYPE_CHECKING
import logging

from ..qt import QT_VERSION
if QT_VERSION == "PyQt6" and not TYPE_CHECKING:
    from PyQt6.QtWidgets import QGridLayout, QWidget
else:
    from PySide6.QtWidgets import QGridLayout, QWidget

from .._component import _CommandType, PropsDict, Element
from .base_components import QtWidgetElement
from ..engine import _WidgetTree, WidgetElement

logger = logging.getLogger("Edifice")

class _TableGridViewRow(WidgetElement):
    """
    Row Element of a :class:`TableGridView`.

    Do not create this Element directly. Instead, use the :func:`TableGridView.row` method.
    """

    def __init__(self, tgv: "TableGridView"):
        super().__init__()

    def _qt_update_commands(
        self,
        children: list[_WidgetTree],
        newprops : PropsDict,
        newstate,
    ) -> list[_CommandType]:
        # This element has no Qt underlying so it has nothing to do except store
        # the children of the row.
        # The _qt_update_commands for TableGridView will render the children.
        return []

class TableGridView(QtWidgetElement):
    """Table-style grid layout displays its children as aligned rows of columns.

    * Underlying Qt Layout
      `QGridLayout <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html>`_

    This component has similar behavior to an `HTML
    table <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/table>`_.
    Each column will be the width of its widest child. Each row will be the
    height of its tallest child.

    The only type of child :class:`Element` allowed in a :class:`TableGridView` is
    the row Element returned by the :func:`row` method. The :func:`row`
    Element establishes a row in the table, and may have children of
    any type of :class:`Element`.

    Example::

        with TableGridView() as tgv:
            with tgv.row():
                Label(text="row 0 column 0")
                Label(text="row 0 column 1")
            with tgv.row():
                Label(text="row 1 column 0")
                with ButtonView():
                    Label(text="row 1 column 1")

    Args:
        row_stretch:
            *n*:sup:`th` row stretch size in proportion to the *n*:sup:`th`
            :code:`int` in this list.
            See `setRowStretch <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.PySide6.QtWidgets.QGridLayout.setRowStretch>`_
        column_stretch:
            *n*:sup:`th` column stretch size in proportion to the *n*:sup:`th`
            :code:`int` in this list.
            See `setColumnStretch <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.PySide6.QtWidgets.QGridLayout.setColumnStretch>`_
        row_minheight:
            *n*:sup:`th` row minimum height is the *n*:sup:`th` :code:`int` in this list.
            See `setRowMinimumHeight <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.PySide6.QtWidgets.QGridLayout.setRowMinimumHeight>`_
        column_minwidth:
            *n*:sup:`th` column minimum width is the *n*:sup:`th` :code:`int` in this list.
            See `setColumnMinimumWidth <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.PySide6.QtWidgets.QGridLayout.setColumnMinimumWidth>`_

    """

    def __init__(
            self,
            row_stretch : list[int] = [],
            column_stretch : list[int] = [],
            row_minheight : list[int] = [],
            column_minwidth : list[int] = [],
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
        self._old_children: dict[QtWidgetElement, tuple[int,int]] = {}
        """Like _LinearView._widget_children"""

        self._row_stretch = row_stretch
        self._column_stretch = column_stretch
        self._row_minheight = row_minheight
        self._column_minwidth = column_minwidth
        super().__init__(**kwargs)

    def row(self) -> Element:
        """
        Returns an :class:`Element` that represents a new row in
        this :class:`TableGridView`. Each child of the new row element
        will be rendered in columns aligned with the other rows.
        """
        return _TableGridViewRow(self)

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

    def _add_child(self, child_component: QtWidgetElement, row:int, column:int):
        # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.PySide6.QtWidgets.QGridLayout.addWidget
        assert child_component.underlying is not None
        self.underlying_layout.addWidget(child_component.underlying, row, column)
        if len(self._row_stretch) > row:
            self.underlying_layout.setRowStretch(row, self._row_stretch[row])
        if len(self._column_stretch) > column:
            self.underlying_layout.setColumnStretch(column, self._column_stretch[column])
        if len(self._row_minheight) > row:
            self.underlying_layout.setRowMinimumHeight(row, self._row_minheight[row])
        if len(self._column_minwidth) > column:
            self.underlying_layout.setColumnMinimumWidth(column, self._column_minwidth[column])

    def _delete_child(self, child_component: QtWidgetElement, row:int, column:int):
        if self.underlying_layout is None:
            logger.warning("_delete_child No underlying_layout " + str(self))
        else:
            if (layoutitem := self.underlying_layout.itemAtPosition(row, column)) is None:
                logger.warning("_delete_child itemAtPosition failed " + str((row,column)) + " " + str(self))
            else:
                if (w := layoutitem.widget()) is None:
                    logger.warning("_delete_child widget is None " + str((row,column)) + " " + str(self))
                else:
                    w.deleteLater()
                self.underlying_layout.removeItem(layoutitem)

    def _soft_delete_child(self, child_component: QtWidgetElement, row:int, column:int):
        if self.underlying_layout is None:
            logger.warning("_delete_child No underlying_layout " + str(self))
        else:
            if (layoutitem := self.underlying_layout.itemAtPosition(row, column)) is None:
                logger.warning("_delete_child itemAtPosition failed " + str((row,column)) + " " + str(self))
            else:
                self.underlying_layout.removeItem(layoutitem)

    def _qt_update_commands(
        self,
        children : list[_WidgetTree],
        newprops,
        newstate
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None

        # The following is equivalent to _LinearView._recompute_children().
        #
        # The direct children of this Element are _TableGridViewRow, but
        # the _TableGridViewRow doesn't have a Qt instantiation so we
        # want to treat the _TableGridViewRow children as the children of
        # the TableGridView.

        new_children: dict[QtWidgetElement, tuple[int,int]] = {}
        children_of_rows: list[_WidgetTree] = list()
        for row,c in enumerate(children):
            children_of_rows.extend(c.children)
            for col,child in enumerate(c.children):
                assert isinstance(child.component, QtWidgetElement)
                new_children[child.component] = (row,col)

        old_deletions = self._old_children.items() - new_children.items()
        new_additions = new_children.items() - self._old_children.items()

        commands: list[_CommandType] = []

        for w,(row,column) in old_deletions:
            if w in new_children:
                commands.append(_CommandType(self._soft_delete_child, w, row, column))
            else:
                commands.append(_CommandType(self._delete_child, w, row, column))

        for w,(row,column) in new_additions:
            commands.append(_CommandType(self._add_child, w, row, column))

        self._old_children = new_children

        if "row_stretch" in newprops:
            commands.append(_CommandType(self._set_row_stretch, newprops["row_stretch"]))
        if "column_stretch" in newprops:
            commands.append(_CommandType(self._set_column_stretch, newprops["column_stretch"]))
        if "row_minheight" in newprops:
            commands.append(_CommandType(self._set_row_minheight, newprops["row_minheight"]))
        if "column_minwidth" in newprops:
            commands.append(_CommandType(self._set_column_minwidth, newprops["column_minwidth"]))

        # Pass the self.underlying_layout if we want it to be styled with the style props?
        # Like this:
        # # commands.extend(super()._qt_update_commands
        # # (children, newprops, newstate, self.underlying, self.underlying_layout))
        commands.extend(super()._qt_update_commands(children_of_rows, newprops, newstate, self.underlying, None))

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
