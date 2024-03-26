import asyncio as asyncio
import unittest

import edifice.app as app
from edifice import Window
import edifice.base_components as base_components
from edifice.engine import Element

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt6":
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

if QtWidgets.QApplication.instance() is None:
    app_obj = QtWidgets.QApplication(["-platform", "offscreen"])

class TimingAvgTestCase(unittest.TestCase):

    def test_timing(self):
        avg = app._TimingAvg()

        avg.update(2)
        self.assertEqual(avg.count(), 1)
        self.assertEqual(avg.mean(), 2)
        self.assertEqual(avg.max(), 2)

        avg.update(6)
        self.assertEqual(avg.count(), 2)
        self.assertEqual(avg.mean(), 4)
        self.assertEqual(avg.max(), 6)

        avg.update(4)
        self.assertEqual(avg.count(), 3)
        self.assertEqual(avg.mean(), 4)
        self.assertEqual(avg.max(), 6)



class IntegrationTestCase(unittest.TestCase):

    def test_export_widgets(self):
        class TestComp(Element):

            def __init__(self):
                super().__init__()
                self.text = ""

            def _render_element(self):
                return base_components.ExportList()(
                    base_components.Label(f"Hello World: {self.text}"),
                    base_components.TextInput(self.text, on_change=lambda text: setattr(self, "text", text))
                )

        my_app = app.App(TestComp(), create_application=False)
        widgets = my_app.export_widgets()
        self.assertEqual(len(widgets), 2)
        self.assertEqual(widgets[0].__class__, QtWidgets.QLabel)
        self.assertEqual(widgets[1].__class__, QtWidgets.QLineEdit)

    def test_integration(self):
        my_app = app.App(Window()(base_components.Label("Hello World!")), create_application=False)
        with my_app.start_loop() as loop:
            loop.call_later(0.1, my_app.stop)

    def test_integration_with_inspector(self):
        my_app = app.App(Window()(base_components.Label("Hello World!")), inspector=True, create_application=False)
        with my_app.start_loop() as loop:
            loop.call_later(0.1, my_app.stop)

    def test_start_loop(self):
        my_app = app.App(
            Window()(base_components.Label(text="start_loop")),
            create_application=False
        )
        with my_app.start_loop() as loop:
            loop.call_later(0.1, my_app.stop)
