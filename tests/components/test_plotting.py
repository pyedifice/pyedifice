import time
import unittest

import edifice
from edifice.components import plotting

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt6":
    from PyQt6 import QtCore, QtWidgets
else:
    from PySide6 import QtCore, QtWidgets


if QtWidgets.QApplication.instance() is None:
    app_obj = QtWidgets.QApplication(["-platform", "offscreen"])


class FigureTestCase(unittest.TestCase):
    def test_figure(self):
        my_app = edifice.App(plotting.Figure(lambda x: None), create_application=False)
        class MockQtApp(object):
            def exec_(self):
                pass
        my_app.app = MockQtApp()
        my_app.start()
