import unittest
import unittest.mock
import edifice.component as component
import edifice.engine as engine
import edifice.base_components as base_components
from PyQt5 import QtWidgets, QtCore

app = QtWidgets.QApplication(["-platform", "offscreen"])

class MockApp(engine.App):
    def __init__(self, component, title="Edifice App"):
        self._component_tree = {}
        self._widget_tree = {}
        self._root = component
        self._title = title

        self._first_render = True
        self._nrenders = 0
        self._render_time = 0
        self._last_render_time = 0
        self._worst_render_time = 0
        # self.app = QtWidgets.QApplication([])


class MockComponent(component.Component):

    @component.register_props
    def __init__(self, recursion_level):
        super().__init__()
        self.will_unmount = unittest.mock.MagicMock()
        self.did_mount = unittest.mock.MagicMock()

    def render(self):
        if self.props.recursion_level == 1:
            return base_components.Label("Test")
        else:
            return base_components.View()(
                MockComponent(self.props.recursion_level + 1)
            )

class ComponentLifeCycleTestCase(unittest.TestCase):

    def test_mount_and_dismount(self):
        component = MockComponent(0)
        app = MockApp(component)
        app._request_rerender([component], {}, {}, execute=False)

        component.did_mount.assert_called_once()
