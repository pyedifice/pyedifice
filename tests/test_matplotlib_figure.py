import asyncio as asyncio
import unittest

from edifice import App

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6":
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

if QtWidgets.QApplication.instance() is None:
    app_obj = QtWidgets.QApplication(["-platform", "offscreen"])

from examples.example_matplotlib_figure import Main


class IntegrationTestCase(unittest.TestCase):
    def test_pyqtgraph(self):
        my_app = App(Main(), create_application=False)
        with my_app.start_loop() as loop:
            loop.call_later(0.1, my_app.stop)


if __name__ == "__main__":
    unittest.main()
