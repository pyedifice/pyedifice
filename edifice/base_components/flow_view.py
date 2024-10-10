# https://doc.qt.io/qtforpython-6/examples/example_widgets_layouts_flowlayout.html

# Copyright (C) 2013 Riverbank Computing Limited.
# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

"""PySide6 port of the widgets/layouts/flowlayout example from Qt v6.x"""

from __future__ import annotations

import logging
import typing

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not typing.TYPE_CHECKING:
    from PyQt6.QtCore import QPoint, QRect, QSize, Qt
    from PyQt6.QtWidgets import QLayout, QLayoutItem, QSizePolicy, QWidget
else:
    from PySide6.QtCore import QPoint, QRect, QSize, Qt
    from PySide6.QtWidgets import QLayout, QLayoutItem, QSizePolicy, QWidget

from .base_components import Element, QtWidgetElement, _get_widget_children, _LinearView, _WidgetTree

logger = logging.getLogger("Edifice")


class FlowLayout(QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._item_list: list[QLayoutItem] = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]

        return None

    def takeAt(self, index):
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
    # This is crazy, but maybe we won’t do a lot of inserting into the middle
    # of a large FlowLayout?
    def insertWidget(self, index, w: QWidget):
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

    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

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
    Flow-style layout widget.

    Displays its children horizonally left-to-right and wraps into multiple rows.

    The height of each row is determined by the tallest child in that row.

    This component has similar behavior to an `HTML CSS
    wrap flex container <https://developer.mozilla.org/en-US/docs/Web/CSS/flex-wrap>`_.

    .. note::

        The :class:`FlowView` element is implemented in Python because Qt does not provide
        any :code:`QLayout` which behaves this way. Currently the :class:`FlowView`
        has O(N\ :sup:`2`) time complexity for adding children
        because of technical limitation of the Qt API.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.underlying = None

    def _delete_child(self, i, old_child: QtWidgetElement):
        assert self.underlying_layout is not None
        child_node = self.underlying_layout.takeAt(i)
        assert child_node is not None
        child_node.widget().deleteLater()

    def _soft_delete_child(self, i, old_child: QtWidgetElement):
        assert self.underlying_layout is not None
        child_node = self.underlying_layout.takeAt(i)
        assert child_node is not None

    def _add_child(self, i, child_component: QWidget):
        self.underlying_layout.insertWidget(i, child_component)

    def _initialize(self):
        self.underlying = QWidget()
        self.underlying_layout = FlowLayout()

        self.underlying.setObjectName(str(id(self)))
        if self.underlying_layout is not None:
            self.underlying.setLayout(self.underlying_layout)
            self.underlying_layout.setContentsMargins(0, 0, 0, 0)
            self.underlying_layout.setSpacing(0)
        else:
            self.underlying.setMinimumSize(100, 100)

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        children = _get_widget_children(widget_trees, self)
        commands = self._recompute_children(children)
        commands.extend(
            super()._qt_update_commands_super(widget_trees, newprops, self.underlying, self.underlying_layout)
        )
        return commands
