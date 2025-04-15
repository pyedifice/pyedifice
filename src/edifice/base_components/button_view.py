from __future__ import annotations

import typing as tp

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import QSize, Qt
    from PyQt6.QtGui import QKeyEvent, QMouseEvent
    from PyQt6.QtWidgets import QHBoxLayout, QPushButton
else:
    from PySide6.QtCore import QSize, Qt
    from PySide6.QtGui import QKeyEvent, QMouseEvent  # noqa: TC002
    from PySide6.QtWidgets import QHBoxLayout, QPushButton

from edifice.base_components import HBoxView
from edifice.engine import CommandType, Element, PropsDiff, _WidgetTree


class _PushButton(QPushButton):
    def __init__(self):
        super().__init__()

    # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLayout.html#detailed-description
    def sizeHint(self) -> QSize:
        return self.layout().sizeHint()  # type: ignore  # noqa: PGH003

    def hasHeightForWidth(self) -> bool:
        return self.layout().hasHeightForWidth()  # type: ignore  # noqa: PGH003

    def heightForWidth(self, arg__1: int) -> int:
        return self.layout().heightForWidth(arg__1)  # type: ignore  # noqa: PGH003

    def minimumSizeHint(self) -> QSize:
        return self.layout().totalMinimumSize()  # type: ignore  # noqa: PGH003


class ButtonView(HBoxView):
    """
    Button with child layout.

    A Button where the label is the Button’s children rendered in a :class:`edifice.HBoxView`.

    .. highlights::

        - Underlying Qt Widget `QPushButton <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QPushButton.html>`_

    .. rubric:: Props

    All **props** from :class:`QtWidgetElement` plus:

    Args:
        on_trigger:
            Event fires when the button is triggered by mouse or
            the Spacebar or Enter key. Event type is either
            `QMouseEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QMouseEvent.html>`_
            or
            `QKeyEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QKeyEvent.html>`_.

            Use either this **prop** or :code:`on_click` **prop**, not both.

    .. rubric:: Usage

    .. code-block:: python
        :caption: Example ButtonView

        with ButtonView(
            on_trigger=lambda _event: print("Button Triggered"),
        ):
            ImageSvg(
                src=str(importlib.resources.files(edifice) / "icons/font-awesome/solid/share.svg"),
                style={"width": 18, "height": 18 },
            )
            Label(text="<i>Share the Content</i>")


    .. figure:: /image/button_view.png

    """

    def __init__(
        self,
        on_trigger: tp.Callable[[QKeyEvent | QMouseEvent], None] | None = None,
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
        diff_props: PropsDiff,
    ):
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None
        commands = super()._qt_update_commands(widget_trees, diff_props)
        match diff_props.get("on_trigger"):
            case _, propnew:
                commands.append(CommandType(self._set_on_trigger, self.underlying, propnew))
                commands.append(CommandType(self.underlying.setCursor, Qt.CursorShape.PointingHandCursor))
        return commands
