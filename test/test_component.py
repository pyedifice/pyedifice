import unittest
import unittest.mock
import edifice.component as component
import edifice.engine as engine
import edifice.base_components as base_components
from PyQt5 import QtWidgets, QtCore

app = QtWidgets.QApplication(["-platform", "offscreen"])

class MockApp(engine.RenderEngine):
    pass


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
