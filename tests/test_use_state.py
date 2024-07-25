import asyncio as asyncio
import unittest

from edifice import App, Window, Element, View, Label, Button, component
from edifice.hooks import use_state

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6":
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

if QtWidgets.QApplication.instance() is None:
    app_obj = QtWidgets.QApplication(["-platform", "offscreen"])


class IntegrationTestCase(unittest.TestCase):
    def test_use_state1(self):
        @component
        def Wrapper(self):
            show, set_show = use_state(False)

            with Window():
                if show:
                    with View():
                        Button(title="Hide", on_click=lambda ev: set_show(False))
                        TestComp()
                else:
                    with View():
                        Button(title="Show", on_click=lambda ev: set_show(True))

        class TestComp(Element):
            def __init__(self):
                super().__init__()

            def _render_element(self):
                print("TestComp instance " + str(id(self)))
                x, x_setter = use_state(0)
                return View(style={"align": "top"})(
                    *[Label(text=str(i)) for i in range(x)],
                    Button(title="State " + str(x), on_click=lambda ev: x_setter(x + 1)),
                    Button(title="Exit", on_click=lambda ev: loop.call_soon(my_app.stop)),
                )

        my_app = App(Wrapper(), create_application=False)
        with my_app.start_loop() as loop:
            loop.call_later(0.1, my_app.stop)


if __name__ == "__main__":
    unittest.main()
