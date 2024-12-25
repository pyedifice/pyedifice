import unittest

from edifice import App, Button, Element, Label, VBoxView, Window, component, use_context
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6":
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

if QtWidgets.QApplication.instance() is None:
    app_obj = QtWidgets.QApplication(["-platform", "offscreen"])

class IntegrationTestCase(unittest.TestCase):
    def test_use_context1(self):
        @component
        def Display(self):
            show, _ = use_context("show", False)
            with VBoxView():
                if show:
                    TestComp()

        @component
        def Wrapper(self):
            show, set_show = use_context("show", False)
            with Window():
                if show:
                    with VBoxView():
                        Button(title="Hide", on_click=lambda _ev: set_show(False))
                        Display()
                else:
                    with VBoxView():
                        Button(title="Show", on_click=lambda _ev: set_show(True))

        class TestComp(Element):
            def __init__(self):
                super().__init__()

            def _render_element(self):
                print("TestComp instance " + str(id(self)))
                return VBoxView(style={"align": "top"})(Label(text=str(id(self))))

        my_app = App(Wrapper(), create_application=False)
        with my_app.start_loop() as loop:
            loop.call_later(0.1, my_app.stop)


if __name__ == "__main__":
    unittest.main()
