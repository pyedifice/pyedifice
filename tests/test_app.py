import unittest

import edifice.app as app
import edifice.base_components as base_components
import edifice._component as component

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt6":
    from PyQt6 import QtCore, QtWidgets, QtGui
else:
    from PySide6 import QtCore, QtWidgets, QtGui

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


class TestComp(component.Component):

    @component.register_props
    def __init__(self):
        super().__init__()
        self.text = ""

    def render(self):
        return base_components.List()(
            base_components.Label(f"Hello World: {self.text}"),
            base_components.TextInput(self.text, on_change=lambda text: self.set_state(text=text))
        )


class IntegrationTestCase(unittest.TestCase):

    def test_widget_creation(self):
        my_app = app.App(TestComp(), create_application=False, mount_into_window=False)
        widgets = my_app.export_widgets()
        self.assertEqual(len(widgets), 2)
        self.assertEqual(widgets[0].__class__, QtWidgets.QLabel)
        self.assertEqual(widgets[1].__class__, QtWidgets.QLineEdit)

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
