from __future__ import annotations

import typing as tp

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtWidgets
    from PyQt6.QtCore import Qt
else:
    from PySide6 import QtWidgets
    from PySide6.QtCore import Qt


import edifice as ed
from edifice.engine import CommandType, PropsDict, _ensure_future, _WidgetTree

if tp.TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


class ScrollBar(ed.QtWidgetElement[QtWidgets.QScrollBar]):
    """
    Scroll bar widget.

    Render a scroll bar widget that allows the user to scroll through a range of values.

    - Underlying Qt Widget:
      `QScrollBar <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QScrollBar.html>`_

    Args:
        value: The current value of the scroll bar.
        minimum: The minimum value of the scroll bar.
        maximum: The maximum value of the scroll bar.
        step_single: The step size for arrow keys.
        step_page: The step size for PgUp/PgDown keys.
        orientation: The scroll bar `Orientation <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#Qt.Orientation>`_.
        on_value_changed: Callback for when the value of the scroll bar changes.
        on_slider_pressed: Callback for when the slider is pressed.
        on_slider_released: Callback for when the slider is released.
    """
    def __init__(
        self,
        value: int = 0,
        minimum: int = 0,
        maximum: int = 100,
        step_single: int | None = None,
        step_page: int | None = None,
        orientation: Qt.Orientation = Qt.Orientation.Vertical,
        on_value_changed: Callable[[int], None | Awaitable[None]] | None = None,
        on_slider_pressed: Callable[[], None | Awaitable[None]] | None = None,
        on_slider_released: Callable[[], None | Awaitable[None]] | None = None,
        **kwargs: tp.Any,
    ) -> None:
        super().__init__(**kwargs)
        self._register_props(
            {
                "value": value,
                "minimum": minimum,
                "maximum": maximum,
                "step_single": step_single,
                "step_page": step_page,
                "orientation": orientation,
                "on_value_changed": on_value_changed,
                "on_slider_pressed": on_slider_pressed,
                "on_slider_released": on_slider_released,
            },
        )
        self._register_props(kwargs)

    def _on_value_changed_handler(self, value: int) -> None:
        if self.props.on_value_changed is not None:
            _ensure_future(self.props.on_value_changed)(value)

    def _on_slider_pressed(self) -> None:
        if self.props.on_slider_pressed is not None:
            _ensure_future(self.props.on_slider_pressed)()

    def _on_slider_released(self) -> None:
        if self.props.on_slider_released is not None:
            _ensure_future(self.props.on_slider_released)()

    def _initialize(self) -> None:
        self.underlying = QtWidgets.QScrollBar()
        self.underlying.setObjectName(str(id(self)))
        self.underlying.valueChanged.connect(self._on_value_changed_handler)
        self.underlying.sliderPressed.connect(self._on_slider_pressed)
        self.underlying.sliderReleased.connect(self._on_slider_released)
        # TODO It would be nice if the slider state were a pure function
        # of props. Right now it has internal value which will change
        # independently of the props value.

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
        if "step_single" in newprops and newprops.step_single is not None:
            commands.append(CommandType(self.underlying.setSingleStep, int(newprops.step_single)))
        if "step_page" in newprops and newprops.step_page is not None:
            commands.append(CommandType(self.underlying.setPageStep, int(newprops.step_page)))
        if "orientation" in newprops:
            commands.append(CommandType(self.underlying.setOrientation, newprops.orientation))

        return commands
