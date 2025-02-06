"""
This is a test of rapidly changing the children of a View based on state.

Seems to work fine.
"""

import logging
import os
import typing as tp

from edifice import (
    App,
    HBoxView,
    Image,
    Label,
    Slider,
    TableGridRow,
    TableGridView,
    VBoxView,
    Window,
    component,
    use_effect,
    use_state,
)
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtCore, QtGui, QtWidgets
    from PyQt6.QtCore import Qt
else:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import Qt

logger = logging.getLogger("Edifice")
logger.setLevel(logging.INFO)

imgpath = os.path.join(os.path.dirname(__file__), "example_calculator.png")  # noqa: PTH118, PTH120


@component
def MyComponent3(self):
    x, x_set = use_state(0)
    x_minus, x_minus_set = use_state(0)

    resize_event, resize_event_set = use_state(tp.cast(QtCore.QSize | None, None))

    def handle_resize(event: QtGui.QResizeEvent):
        resize_event_set(event.size())

    with VBoxView():
        Label(text=str(resize_event))
        with TableGridView():
            with TableGridRow():
                Slider(x, min_value=0, max_value=100, on_change=x_set).set_key("row1")
            with TableGridRow():
                Slider(x_minus, min_value=0, max_value=100, on_change=x_minus_set).set_key("row2")
            with TableGridRow():
                with HBoxView(on_resize=handle_resize).set_key("row3"):
                    for i in range(x_minus, x):
                        with VBoxView(style={"align": "center"}).set_key("view" + str(i)):
                            Label(str(i))
                            Image(
                                src=imgpath,
                                aspect_ratio_mode=Qt.AspectRatioMode.KeepAspectRatio,
                                style={
                                    "width": 15,
                                    "height": 15,
                                },
                            )


@component
def MyComponent(self):
    x, x_set = use_state(0)

    with VBoxView():
        Slider(x, min_value=0, max_value=100, on_change=x_set)
        InnerComponent(x)


@component
def InnerComponent(self, x: int):
    y, y_set = use_state(x)

    def y_setter():
        y_set(x)
        return lambda: None

    use_effect(y_setter, x)

    with HBoxView():
        for i in range(y):
            ItemComponent(i).set_key("X" + str(i))


@component
def ItemComponent(self, i: int):
    with VBoxView():
        Label(str(i))


@component
def Main(self):
    with Window():
        MyComponent3()


if __name__ == "__main__":
    App(Main()).start()
