import unittest
import unittest.mock
import edifice._component as component
import edifice.engine as engine
import edifice.base_components as base_components

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt5":
    from PyQt5 import QtCore, QtWidgets
else:
    from PySide2 import QtCore, QtWidgets

try:
    app = QtWidgets.QApplication(["-platform", "offscreen"])
except:
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
        app = engine.RenderEngine(component)
        render_results = app._request_rerender([component])
        render_results.run()
        component.did_mount.assert_called_once()
