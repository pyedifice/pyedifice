# https://doc.qt.io/qtforpython-6/examples/example_widgets_layouts_flowlayout.html

# Copyright (C) 2013 Riverbank Computing Limited.
# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

"""PySide6 port of the widgets/layouts/flowlayout example from Qt v6.x"""

from __future__ import annotations

import typing

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not typing.TYPE_CHECKING:
    from PyQt6.QtCore import QPoint, QRect, QSize, Qt
    from PyQt6.QtWidgets import QLayout, QLayoutItem, QSizePolicy, QWidget
else:
    from PySide6.QtCore import QPoint, QRect, QSize, Qt
    from PySide6.QtWidgets import QLayout, QLayoutItem, QSizePolicy, QWidget


from edifice.base_components.base_components import QtWidgetElement, _LinearView
from edifice.engine import CommandType, Element, _get_widget_children, _WidgetTree

if typing.TYPE_CHECKING:
    from edifice.engine import PropsDiff


class FlowLayout(QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._item_list: list[QLayoutItem] = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, arg__1: QLayoutItem) -> None:
        self._item_list.append(arg__1)

    def count(self) -> int:
        return len(self._item_list)

    def itemAt(self, index) -> QLayoutItem | None:
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    # Contradiction between the docs and the type.
    # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLayout.html#PySide6.QtWidgets.QLayout.takeAt
    def takeAt(self, index: int) -> QLayoutItem | None:  # type: ignore  # noqa: PGH003
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    # We need insertWidget like the one in QBoxLayout to support Edifice.
    # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QBoxLayout.html#PySide6.QtWidgets.QBoxLayout.insertWidget
    #
    # But the QLayout API gives us only addWidget and removeWidget.
    # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLayout.html
    #
    # So we have to write insertWidget in terms of addWidget and removeWidget.
    #
    # This is O(N) for inserting at the beginning of a FlowLayout.
    def insertWidget(self, index: int, w: QWidget) -> None:
        stack = []
        while len(self._item_list) > index:
            w_ = self._item_list[-1].widget()
            self.removeWidget(w_)
            stack.append(w_)
        self.addWidget(w)
        while len(stack) > 0:
            self.addWidget(stack.pop())

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, arg__1):
        return self._do_layout(QRect(0, 0, arg__1, 0), True)

    def setGeometry(self, arg__1: QRect):
        super().setGeometry(arg__1)
        self._do_layout(arg__1, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()

        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())

        size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._item_list:
            style = item.widget().style()
            layout_spacing_x = style.layoutSpacing(
                QSizePolicy.ControlType.PushButton,
                QSizePolicy.ControlType.PushButton,
                Qt.Orientation.Horizontal,
            )
            layout_spacing_y = style.layoutSpacing(
                QSizePolicy.ControlType.PushButton,
                QSizePolicy.ControlType.PushButton,
                Qt.Orientation.Vertical,
            )
            space_x = spacing + layout_spacing_x
            space_y = spacing + layout_spacing_y
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()


class FlowView(_LinearView[QWidget]):
    """
    Flow-style layout.

    .. highlights::

        - Underlying Qt Widget `QWidget <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html>`_
        - Underlying Qt Layout `QLayout <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLayout.html>`_

    Displays its children horizonally left-to-right and wraps into multiple rows.

    The height of each row is determined by the tallest child in that row.

    This component has similar behavior to an `HTML CSS
    wrap flex container <https://developer.mozilla.org/en-US/docs/Web/CSS/flex-wrap>`_.

    .. note::

        The :class:`FlowView` element is implemented in Python because Qt does not provide
        any native :code:`QLayout` which behaves this way. Currently the :class:`FlowView`
        has *O(N)* time complexity for inserting a child at the beginning
        of *N* children because of technical limitations of the Qt API.

    .. rubric:: Props

    All **props** for :class:`QtWidgetElement`.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _delete_child(self, i, old_child: QtWidgetElement):  # noqa: ARG002
        assert self.underlying_layout is not None
        child_node = self.underlying_layout.takeAt(i)
        assert child_node is not None
        child_node.widget().deleteLater()

    def _soft_delete_child(self, i, old_child: QtWidgetElement):  # noqa: ARG002
        assert self.underlying_layout is not None
        child_node = self.underlying_layout.takeAt(i)
        assert child_node is not None

    def _add_child(self, i, child_component: QWidget):
        self.underlying_layout.insertWidget(i, child_component)

    def _initialize(self):
        self.underlying = QWidget()
        self.underlying_layout = FlowLayout()
        self.underlying.setObjectName(str(id(self)))
        self.underlying.setLayout(self.underlying_layout)
        self.underlying_layout.setContentsMargins(0, 0, 0, 0)
        self.underlying_layout.setSpacing(0)

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        diff_props: PropsDiff,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        children = _get_widget_children(widget_trees, self)
        commands: list[CommandType] = []
        child_commands = self._recompute_children(children)
        commands.extend(child_commands)
        if len(child_commands) > 0:
            # If we have children commands then we update the underlying layout.
            # This is to mitigate a bug in which the FlowLayout does not update
            # sometimes when children are re-ordered.
            #
            # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLayout.html#PySide6.QtWidgets.QLayout.update
            # https://doc.qt.io/qt-6/qlayout.html#update
            #
            # “You should generally not need to call this because it is automatically called at
            # the most appropriate times.”
            commands.append(CommandType(self.underlying_layout.update))
        commands.extend(
            super()._qt_update_commands_super(widget_trees, diff_props, self.underlying, self.underlying_layout),
        )
        return commands
