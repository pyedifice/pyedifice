"""
This is a test of rapidly changing the children of a View based on state.

Seems to work fine.
"""

import logging
import sys
import os
import typing as tp
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
from edifice import App, Window, View, component, Slider, Label, use_state, use_effect, Image, Reference, use_ref, TableGridView

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import Qt
    from PyQt6 import QtWidgets
else:
    from PySide6.QtCore import Qt
    from PySide6 import QtWidgets

logger = logging.getLogger("Edifice")
logger.setLevel(logging.INFO)

# @component
# def MyComponent(self):
#     x, x_set = use_state(0)
#
#     with View(layout="column"):
#         Slider(x, min_value=0, max_value=100, on_change=x_set)
#         with View(layout="row"):
#             for i in range(x):
#                 Label(str(i)).set_key("X"+str(i))

imgpath = os.path.join(os.path.dirname(__file__), "example_calculator.png")

@component
def MyComponent3(self):
    x, x_set = use_state(0)
    x_minus, x_minus_set = use_state(0)

    vref: Reference = use_ref()
    resize_trigger, resize_trigger_set = use_state(False)
    def handle_resize(_event):
        print("resize")
        resize_trigger_set(lambda x: not x)
    def initialize():
        if vref:
            view_element = vref()
            assert type(view_element) == View
            assert isinstance(view_element.underlying, QtWidgets.QWidget)
            view_element.underlying.resizeEvent = handle_resize
            def cleanup():
                assert type(view_element) == View
                assert isinstance(view_element.underlying, QtWidgets.QWidget)
                view_element.underlying.resizeEvent = lambda _event: None
            return cleanup
        else:
            return lambda:None
    use_effect(initialize, [])

    with View(layout="column"):
        with TableGridView() as tgv:
            with tgv.row():
                Slider(x, min_value=0, max_value=100, on_change=x_set).set_key("row1")
            with tgv.row():
                Slider(x_minus, min_value=0, max_value=100, on_change=x_minus_set).set_key("row2")
            with tgv.row():
                with View(layout="row").register_ref(vref).set_key("row3"):
                    for i in range(x_minus, x):
                    # for i in range(x):
                    #     if i < x_minus or i > x_minus + 10 or divmod(i, 2)[1] == 0:
                        with View(layout="column", style={"align":"center"}).set_key("view"+str(i)):
                            Label(str(i))# .set_key("X"+str(i))
                            Image(
                                src=imgpath,
                                aspect_ratio_mode=Qt.AspectRatioMode.KeepAspectRatio,
                                style={
                                    "width":15,
                                    "height": 15,
                                }
                            )# .set_key("img"+str(i))

@component
def MyComponent(self):
    x, x_set = use_state(0)

    with View(layout="column"):
        Slider(x, min_value=0, max_value=100, on_change=x_set)
        InnerComponent(x)

@component
def InnerComponent(self, x:int):
    y, y_set = use_state(x)

    def y_setter():
        y_set(x)
        return lambda:None

    use_effect(y_setter, x)

    with View(layout="row"):
        for i in range(y):
            ItemComponent(i).set_key("X"+str(i))

@component
def ItemComponent(self, i:int):
    with View():
        Label(str(i))


@component
def Main(self):
    with Window():
        MyComponent3()

if __name__ == "__main__":
    App(Main()).start()
