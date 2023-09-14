import typing as tp

from ..qt import QT_VERSION
if QT_VERSION == "PyQt6":
    from PyQt6.QtCore import QSize, Qt
    from PyQt6.QtGui import QKeyEvent, QMouseEvent
    from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QHBoxLayout
else:
    from PySide6.QtCore import QSize, Qt
    from PySide6.QtGui import QKeyEvent, QMouseEvent
    from PySide6.QtWidgets import QPushButton, QVBoxLayout, QHBoxLayout

from ..base_components import View, register_props

class _PushButton(QPushButton):
    def __init__(self):
        super().__init__()

    # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLayout.html#detailed-description
    def sizeHint(self) -> QSize:
        return self.layout().sizeHint()
    def hasHeightForWidth(self) -> bool:
        return self.layout().hasHeightForWidth()
    def heightForWidth(self) -> int:
        return self.layout().heightForWidth()
    def minimumSizeHint(self) -> QSize:
        return self.layout().totalMinimumSize()


class ButtonView(View):
    """
    A Button where the label is the Button’s children rendered in a :class:`edifice.View`.

    Inherits all the props from :class:`edifice.QtWidgetComponent`.

    Args:
        on_trigger:
            Event fires when the button is triggered by mouse or
            the Spacebar or Enter key. Event type is either :code:`QMouseEvent` or :code:`QKeyEvent`.
            Use either this or :code:`on_click`, not both.
    """
    @register_props
    def __init__(self,
            layout: str = "row",
            on_trigger: tp.Callable[[QKeyEvent], None] | tp.Callable[[QMouseEvent], None] | None = None,
            **kwargs):
        super().__init__(layout, **kwargs)

    def _initialize(self):
        self.underlying = _PushButton()
        layout = self.props.layout
        if layout == "column":
            self.underlying_layout = QVBoxLayout()
        elif layout == "row":
            self.underlying_layout = QHBoxLayout()
        elif layout == "none":
            self.underlying_layout = None
        else:
            raise ValueError("Layout must be row, column or none, got %s instead", layout)

        self.underlying.setObjectName(str(id(self)))
        if self.underlying_layout is not None:
            self.underlying.setLayout(self.underlying_layout)
            self.underlying_layout.setContentsMargins(0, 0, 0, 0)
            self.underlying_layout.setSpacing(0)
        else:
            self.underlying.setMinimumSize(100, 100)

    def _add_child(self, i, child_component):
        super()._add_child(i, child_component)
        # All children must be transparent to mouse events
        child_component.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def _set_on_trigger(self, underlying, on_trigger):
        if on_trigger is not None:
            def on_click(ev:QMouseEvent):
                on_trigger(ev)
            def on_key(ev:QKeyEvent):
                if ev.text() == " " or ev.text() == "\r":
                    on_trigger(ev)
            self._set_on_click(underlying, on_click)
            self._set_on_key_up(underlying, on_key)

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self._initialize()
        commands = super()._qt_update_commands(children, newprops, newstate)
        for prop in newprops:
            if prop == "on_trigger":
                commands.append((self._set_on_trigger, self.underlying, newprops.on_trigger))
            commands.append((self.underlying.setCursor, Qt.CursorShape.PointingHandCursor))
        return commands
