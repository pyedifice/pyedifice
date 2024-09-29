from __future__ import annotations

import typing as tp

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import QSize, Qt
    from PyQt6.QtGui import QKeyEvent, QMouseEvent
    from PyQt6.QtWidgets import QHBoxLayout, QPushButton
else:
    from PySide6.QtCore import QSize, Qt
    from PySide6.QtGui import QKeyEvent, QMouseEvent
    from PySide6.QtWidgets import QHBoxLayout, QPushButton

from .base_components import CommandType, Element, HBoxView, _WidgetTree


class _PushButton(QPushButton):
    def __init__(self):
        super().__init__()

    # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLayout.html#detailed-description
    def sizeHint(self) -> QSize:
        return self.layout().sizeHint()

    def hasHeightForWidth(self) -> bool:
        return self.layout().hasHeightForWidth()

    def heightForWidth(self, width: int) -> int:
        return self.layout().heightForWidth(width)

    def minimumSizeHint(self) -> QSize:
        return self.layout().totalMinimumSize()


class ButtonView(HBoxView):
    """
    A Button where the label is the Button’s children rendered in a :class:`edifice.HBoxView`.

    * Underlying Qt Widget
      `QPushButton <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QPushButton.html>`_

    Example::

        with ButtonView(
            on_click=handle_click,
        ):
            Icon(name="share")
            Label(text="<i>Share the Content</i>")

    .. figure:: /image/button_view.png

    Args:
        on_trigger:
            Event fires when the button is triggered by mouse or
            the Spacebar or Enter key. Event type is either :code:`QMouseEvent` or :code:`QKeyEvent`.
            Use either this or :code:`on_click`, not both.
    """

    def __init__(
        self,
        on_trigger: tp.Callable[[QKeyEvent], None] | tp.Callable[[QMouseEvent], None] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props(
            {
                "on_trigger": on_trigger,
            },
        )

    def _initialize(self):
        self.underlying = _PushButton()
        self.underlying_layout = QHBoxLayout()
        self.underlying.setObjectName(str(id(self)))
        self.underlying.setLayout(self.underlying_layout)
        self.underlying_layout.setContentsMargins(0, 0, 0, 0)
        self.underlying_layout.setSpacing(0)

    def _add_child(self, i, child_component):
        super()._add_child(i, child_component)
        # All children must be transparent to mouse events
        child_component.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def _set_on_trigger(self, underlying, on_trigger):
        if on_trigger is not None:

            def on_click(ev: QMouseEvent):
                on_trigger(ev)

            def on_key(ev: QKeyEvent):
                if ev.key() == Qt.Key.Key_Enter or ev.key() == Qt.Key.Key_Return or ev.key() == Qt.Key.Key_Space:
                    on_trigger(ev)
                else:
                    ev.ignore()

            self._set_on_click(underlying, on_click)
            self._set_on_key_up(underlying, on_key)

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        commands = super()._qt_update_commands(widget_trees, newprops)
        for prop in newprops:
            if prop == "on_trigger":
                commands.append(CommandType(self._set_on_trigger, self.underlying, newprops.on_trigger))
            commands.append(CommandType(self.underlying.setCursor, Qt.CursorShape.PointingHandCursor))
        return commands
