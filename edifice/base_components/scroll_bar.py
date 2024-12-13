from collections.abc import Awaitable, Callable
from typing import Any

from PySide6 import QtWidgets
from PySide6.QtCore import Qt

import edifice as ed
from edifice.engine import CommandType, PropsDict, _ensure_future, _WidgetTree


class ScrollBar(ed.QtWidgetElement[QtWidgets.QScrollBar]):
    def __init__(
        self,
        value: int = 0,
        minimum: int = 0,
        maximum: int = 100,
        step: int = 1,
        orientation: Qt.Orientation = Qt.Orientation.Vertical,
        on_value_changed: Callable[[int], None | Awaitable[None]] | None = None,
        on_slider_pressed: Callable[[], None | Awaitable[None]] | None = None,
        on_slider_released: Callable[[], None | Awaitable[None]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._register_props(
            {
                "value": value,
                "minimum": minimum,
                "maximum": maximum,
                "step": step,
                "orientation": orientation,
                "on_value_changed": on_value_changed,
                "on_slider_pressed": on_slider_pressed,
                "on_slider_released": on_slider_released,
            },
        )
        self._register_props(kwargs)

    def _on_value_changed_handler(self: Self, value: int) -> None:
        if self.props.on_value_changed is not None:
            _ensure_future(self.props.on_value_changed)(value)

    def _on_slider_pressed(self: Self) -> None:
        if self.props.on_slider_pressed is not None:
            _ensure_future(self.props.on_slider_pressed)()

    def _on_slider_released(self: Self) -> None:
        if self.props.on_slider_released is not None:
            _ensure_future(self.props.on_slider_released)()

    def _initialize(self: Self) -> None:
        self.underlying = QtWidgets.QScrollBar()
        self.underlying.setObjectName(str(id(self)))
        self.underlying.valueChanged.connect(self._on_value_changed_handler)
        self.underlying.sliderPressed.connect(self._on_slider_pressed)
        self.underlying.sliderReleased.connect(self._on_slider_released)

    def _qt_update_commands(
        self,
        widget_trees: dict[ed.Element, _WidgetTree],
        newprops: PropsDict,
    ) -> list[CommandType]:
        if self.underlying is None:
            self._initialize()
        assert self.underlying is not None

        commands = super()._qt_update_commands_super(widget_trees, newprops, self.underlying)
        if "value" in newprops:
            commands.append(CommandType(self.underlying.setValue, int(newprops.value)))
        if "minimum" in newprops:
            commands.append(CommandType(self.underlying.setMinimum, int(newprops.minimum)))
        if "maximum" in newprops:
            commands.append(CommandType(self.underlying.setMaximum, int(newprops.maximum)))
        if "step" in newprops:
            commands.append(CommandType(self.underlying.setPageStep, int(newprops.step)))
        if "orientation" in newprops:
            commands.append(CommandType(self.underlying.setOrientation, newprops.orientation))

        return commands