import time
import unittest

import edifice
from edifice.components import plotting

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt5":
    from PyQt5 import QtCore, QtWidgets
else:
    from PySide2 import QtCore, QtWidgets


try:
    app_obj = QtWidgets.QApplication(["-platform", "offscreen"])
except:
    app_obj = QtWidgets.QApplication.instance()


class FigureTestCase(unittest.TestCase):
    def test_figure(self):
        my_app = edifice.App(plotting.Figure(lambda x: None), create_application=False)
        class MockQtApp(object):
            def exec_(self):
                pass
        my_app.app = MockQtApp()
        my_app.start()
