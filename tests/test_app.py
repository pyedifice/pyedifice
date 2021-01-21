import unittest

import edifice.app as app
import edifice.base_components as base_components

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt5":
    from PyQt5 import QtCore, QtWidgets
else:
    from PySide2 import QtCore, QtWidgets


try:
    app_obj = QtWidgets.QApplication(["-platform", "offscreen"])
except:
    app_obj = QtWidgets.QApplication.instance()


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

    def test_integration(self):
        my_app = app.App(base_components.Label("Hello World!"), create_application=False)
        class MockQtApp(object):
            def exec_(self):
                pass
        my_app.app = MockQtApp()
        my_app.start()

    def test_integration_with_inspector(self):
        my_app = app.App(base_components.Label("Hello World!"), create_application=False, inspector=True)
        class MockQtApp(object):
            def exec_(self):
                pass
        my_app.app = MockQtApp()
        my_app.start()
