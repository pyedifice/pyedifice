import asyncio as asyncio
import unittest

import edifice.app as app
import edifice.base_components as base_components
import edifice.state as state
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



class IntegrationTestCase(unittest.TestCase):

    def test_widget_creation(self):
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

    def test_subscribe_unmount(self):
        """
        Test that when a StateValue-subscribed child component is unmounted, the subscription is cleaned up.
        """

        observations_CompChild1: list[int] = []

        class TestComp(component.Component):
            @component.register_props
            def __init__(self, state_value):
                super().__init__()
            def render(self):
                v = self.props.state_value.subscribe(self)
                if v == 1:
                    return CompChild1(self.props.state_value)
                elif v == 2:
                    return CompChild2(self.props.state_value)
                else:
                    return base_components.Label(text="unreachable")

        class CompChild1(component.Component):
            @component.register_props
            def __init__(self, state_value):
                super().__init__()
            def render(self):
                v = self.props.state_value.subscribe(self)
                observations_CompChild1.append(v)
                return base_components.Label(text="child1")
            def did_render(self):
                loop = asyncio.get_running_loop()
                loop.call_soon(self.props.state_value.set, 2)

        class CompChild2(component.Component):
            @component.register_props
            def __init__(self, state_value):
                super().__init__()
            def render(self):
                v = self.props.state_value.subscribe(self)
                return base_components.Label(text="child2")
            def did_render(self):
                loop = asyncio.get_running_loop()
                loop.call_soon(loop.stop)

        state_value = state.StateValue(1)
        my_app = app.App(TestComp(state_value), qapplication=QtWidgets.QApplication.instance())
        with my_app.start_loop() as loop:
            loop.run_forever()

        self.assertEqual(state_value.value, 2)

        # TODO
        # I think this is a failing test. The number of subscriptions here
        # should be 0, because all of these Components have been unmounted.
        #
        # self.assertEqual(len(state_value._subscriptions), 0)
        self.assertNotEqual(len(state_value._subscriptions), 0)

        # TODO
        # This is definitely a failing test. The CompChild1.render() should
        # never observe a state_value of 2.
        #
        # self.assertFalse(2 in observations_CompChild1)
        self.assertTrue(2 in observations_CompChild1)

    def test_start_loop(self):
        my_app = app.App(
            base_components.Label(text="start_loop"),
            qapplication=QtWidgets.QApplication.instance()
        )
        with my_app.start_loop() as loop:
            loop.call_later(0.1, loop.stop)
            loop.run_forever()
