import unittest
import unittest.mock
from edifice.app import App, Window
import edifice.engine as engine
import edifice.base_components as base_components
import edifice as ed

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6":
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

if QtWidgets.QApplication.instance() is None:
    qapp = QtWidgets.QApplication(["-platform", "offscreen"])


@ed.component
def Value(self, value):
    self.value = value
    base_components.VBoxView()


class OtherMockElement(ed.Element):
    def __init__(self):
        super().__init__()

        class MockController(object):
            _request_rerender = unittest.mock.MagicMock()

        self._controller = MockController()


class MockBrokenElement(ed.Element):
    def __init__(self):
        super().__init__()

        class MockController(object):
            def _request_rerender(*args, **kwargs):
                raise ValueError("I am broken")

        self._controller = MockController()


class ElementTestCase(unittest.TestCase):
    def test_render_view_replacement(self):
        """
        Test that when a View row is replaced by a View column, a new View
        is created and the old View is destroyed.
        """

        @ed.component
        def xComponent(self):
            x, x_set = ed.use_state(0)
            if x == 0:
                with ed.HBoxView().set_key("row"):
                    ed.Label("Test")
                x_set(1)
            else:
                with ed.VBoxView().set_key("column"):
                    ed.Label("Test")

        root_element = Window()(xComponent())
        app = App(root_element, create_application=False)
        render_engine = engine.RenderEngine(root_element, app)
        _render_results1 = render_engine._request_rerender([root_element])
        self.assertIsInstance(
            render_engine._widget_tree[root_element].children[0].underlying_layout, QtWidgets.QHBoxLayout
        )
        _render_results2 = render_engine._request_rerender([root_element])
        self.assertIsInstance(
            render_engine._widget_tree[root_element].children[0].underlying_layout, QtWidgets.QVBoxLayout
        )


class MakeElementTestCase(unittest.TestCase):
    def test_make_component(self):
        @ed.component
        def Element1234(self, prop1, prop2):
            Value(1234)

        self.assertEqual(Element1234.__name__, "Element1234")
        comp = Element1234(1, 2)
        self.assertEqual(comp.__class__, Element1234)
        self.assertEqual(comp.props, {"prop1": 1, "prop2": 2, "children": ()})
        with engine.Container() as container:
            comp._render_element()
        value_component = container.children[0]
        self.assertEqual(value_component.__class__.__name__, "Value")
        # Render to value to update the state
        value_component._render_element()
        self.assertEqual(value_component.value, 1234)

    def test_make_components(self):
        @ed.component
        def Element1234(self, prop1, prop2):
            with base_components.VBoxView():
                Value(1337)
                Value(42)
                Value(69)
                Value(420)

        self.assertEqual(Element1234.__name__, "Element1234")
        comp = Element1234(1, 2)
        self.assertEqual(comp.__class__, Element1234)
        self.assertEqual(comp.props, {"prop1": 1, "prop2": 2, "children": ()})
        with engine.Container() as container:
            comp._render_element()
        view = container.children[0]
        components = view.children
        for comp in components:
            self.assertEqual(comp.__class__.__name__, "Value")
        for comp in components:
            # Render to value to update the state
            comp._render_element()
        values = [comp.value for comp in components]
        self.assertEqual(values, [1337, 42, 69, 420])

    def test_make_nested_component(self):
        @ed.component
        def A(self):
            Value(13)

        @ed.component
        def Element1234(self, prop1, prop2):
            with A():
                Value(9)

        self.assertEqual(Element1234.__name__, "Element1234")
        comp = Element1234(1, 2)
        self.assertEqual(comp.__class__, Element1234)
        self.assertEqual(comp.props, {"prop1": 1, "prop2": 2, "children": ()})
        with engine.Container() as container:
            comp._render_element()
        root = container.children[0]
        self.assertEqual(root.__class__.__name__, "A")
        with engine.Container() as container:
            root._render_element()
        nested = container.children[0]
        nested._render_element()
        self.assertEqual(nested.__class__.__name__, "Value")
        self.assertEqual(nested.value, 13)
        children = root.children
        for child in children:
            child._render_element()
        values = [comp.value for comp in children]
        self.assertEqual(values, [9])


if __name__ == "__main__":
    unittest.main()
