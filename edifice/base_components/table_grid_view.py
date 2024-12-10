from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not TYPE_CHECKING:
    from PyQt6.QtWidgets import QGridLayout, QWidget
else:
    from PySide6.QtWidgets import QGridLayout, QWidget

from .base_components import CommandType, Element, PropsDict, QtWidgetElement, _get_widget_children, _WidgetTree

logger = logging.getLogger("Edifice")


class TableGridRow(QtWidgetElement):
    """
    Row Element of a :class:`TableGridView`.

    This Element’s parent must be a :class:`TableGridView`.

    This Element may have children of any type of :class:`Element`.

    This Element has no Qt underlying, and no props.
    """

    def __init__(self):
        super().__init__()

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],  # noqa: ARG002
        newprops: PropsDict,  # noqa: ARG002
    ) -> list[CommandType]:
        # This element has no Qt underlying so it has nothing to do except store
        # the children of the row.
        # The _qt_update_commands for TableGridView will render the children.
        return []


class TableGridView(QtWidgetElement[QWidget]):
    """Table-style grid layout displays its children as aligned rows of columns.

    * Underlying Qt Layout
      `QGridLayout <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html>`_

    This component has similar behavior to an `HTML
    table <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/table>`_.
    Each column will be the width of its widest child. Each row will be the
    height of its tallest child.

    The only type of child :class:`Element` allowed in a :class:`TableGridView` is
    :class:`TableGridRow`.
    Each :class:`TableGridRow` establishes a row in the table, and may have
    children of any type of :class:`Element`.

    .. code-block:: python

        with TableGridView():
            with TableGridRow():
                Label(text="row 0 column 0")
                Label(text="row 0 column 1")
            with TableGridRow():
                Label(text="row 1 column 0")
                with VBoxView():
                    Label(text="row 1 column 1")

    If the :class:`TableGridRow` s are added and removed dynamically then
    it’s a good idea to :func:`Element.set_key` each row.

    Args:
        row_stretch:
            *n*:sup:`th` row stretch size in proportion to the *n*:sup:`th`
            :code:`int` in this list.
            See `setRowStretch <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.QGridLayout.setRowStretch>`_
        column_stretch:
            *n*:sup:`th` column stretch size in proportion to the *n*:sup:`th`
            :code:`int` in this list.
            See `setColumnStretch <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.QGridLayout.setColumnStretch>`_
        row_minheight:
            *n*:sup:`th` row minimum height is the *n*:sup:`th` :code:`int` in this list.
            See `setRowMinimumHeight <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.QGridLayout.setRowMinimumHeight>`_
        column_minwidth:
            *n*:sup:`th` column minimum width is the *n*:sup:`th` :code:`int` in this list.
            See `setColumnMinimumWidth <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.QGridLayout.setColumnMinimumWidth>`_

    """

    def __init__(
        self,
        row_stretch: tuple[int, ...] = (),
        column_stretch: tuple[int, ...] = (),
        row_minheight: tuple[int, ...] = (),
        column_minwidth: tuple[int, ...] = (),
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props(
            {
                "row_stretch": row_stretch,
                "column_stretch": column_stretch,
                "row_minheight": row_minheight,
                "column_minwidth": column_minwidth,
            },
        )
        self.underlying = None
        self._old_children: dict[QtWidgetElement, tuple[int, int]] = {}
        """Like _LinearView._widget_children"""

        self._row_stretch = row_stretch
        self._column_stretch = column_stretch
        self._row_minheight = row_minheight
        self._column_minwidth = column_minwidth

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

    def _add_child(self, child_component: QtWidgetElement, row: int, column: int):
        # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QGridLayout.html#PySide6.QtWidgets.QGridLayout.addWidget
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

    def _delete_child(self, child_component: QtWidgetElement, row: int, column: int):
        if self.underlying_layout is None:
            logger.warning("_delete_child No underlying_layout " + str(self))
        else:
            if (layoutitem := self.underlying_layout.itemAtPosition(row, column)) is None:
                logger.warning("_delete_child itemAtPosition failed " + str((row, column)) + " " + str(self))
            else:
                if (w := layoutitem.widget()) is None:
                    logger.warning("_delete_child widget is None " + str((row, column)) + " " + str(self))
                else:
                    w.deleteLater()
                self.underlying_layout.removeItem(layoutitem)

    def _soft_delete_child(self, child_component: QtWidgetElement, row: int, column: int):
        if self.underlying_layout is None:
            logger.warning("_delete_child No underlying_layout " + str(self))
        else:
            if (layoutitem := self.underlying_layout.itemAtPosition(row, column)) is None:
                logger.warning("_delete_child itemAtPosition failed " + str((row, column)) + " " + str(self))
            else:
                self.underlying_layout.removeItem(layoutitem)

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None

        # The following is equivalent to _LinearView._recompute_children().
        #
        # The direct children of this Element are TableGridRow, but
        # the TableGridRow doesn't have a Qt instantiation so we
        # want to treat the TableGridRow children as the children of
        # the TableGridView.

        children = _get_widget_children(widget_trees, self)
        new_children: dict[QtWidgetElement, tuple[int, int]] = {}
        for row, c in enumerate(children):
            children_of_row = _get_widget_children(widget_trees, c)
            for col, child in enumerate(children_of_row):
                new_children[child] = (row, col)

        old_deletions = self._old_children.items() - new_children.items()
        new_additions = new_children.items() - self._old_children.items()

        commands: list[CommandType] = []

        for w, (row, column) in old_deletions:
            if w in new_children:
                # TODO this condition is never hit
                commands.append(CommandType(self._soft_delete_child, w, row, column))
            else:
                commands.append(CommandType(self._delete_child, w, row, column))

        for w, (row, column) in new_additions:
            commands.append(CommandType(self._add_child, w, row, column))

        self._old_children = new_children

        if "row_stretch" in newprops:
            commands.append(CommandType(self._set_row_stretch, newprops.row_stretch))
        if "column_stretch" in newprops:
            commands.append(CommandType(self._set_column_stretch, newprops.column_stretch))
        if "row_minheight" in newprops:
            commands.append(CommandType(self._set_row_minheight, newprops.row_minheight))
        if "column_minwidth" in newprops:
            commands.append(CommandType(self._set_column_minwidth, newprops.column_minwidth))

        commands.extend(
            super()._qt_update_commands_super(widget_trees, newprops, self.underlying, self.underlying_layout),
        )

        return commands

    def _set_row_stretch(self, row_stretch: tuple[int, ...]):
        self._row_stretch = row_stretch
        for i, stretch in enumerate(row_stretch[: self.underlying_layout.rowCount()]):
            self.underlying_layout.setRowStretch(i, stretch)

    def _set_column_stretch(self, column_stretch: tuple[int, ...]):
        self._column_stretch = column_stretch
        for i, stretch in enumerate(column_stretch[: self.underlying_layout.columnCount()]):
            self.underlying_layout.setColumnStretch(i, stretch)

    def _set_row_minheight(self, row_minheight: tuple[int, ...]):
        self._row_minheight = row_minheight
        for i, minheight in enumerate(row_minheight[: self.underlying_layout.rowCount()]):
            self.underlying_layout.setRowMinimumHeight(i, minheight)

    def _set_column_minwidth(self, column_minwidth: tuple[int, ...]):
        self._column_minwidth = column_minwidth
        for i, minwidth in enumerate(column_minwidth[: self.underlying_layout.columnCount()]):
            self.underlying_layout.setColumnMinimumWidth(i, minwidth)
