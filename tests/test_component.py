import unittest
import unittest.mock
import edifice._component as component
import edifice.engine as engine
import edifice.base_components as base_components

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt6":
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

if QtWidgets.QApplication.instance() is None:
    app = QtWidgets.QApplication(["-platform", "offscreen"])

@component.component
def Value(self, value):
    self.value = value

class MockElement(component.Element):

    @component.register_props
    def __init__(self, recursion_level):
        super().__init__()
        self.will_unmount = unittest.mock.MagicMock()
        self.did_mount = unittest.mock.MagicMock()
        self.did_render = unittest.mock.MagicMock()

    def render(self):
        if self.props.recursion_level == 1:
            return base_components.Label("Test")
        else:
            return base_components.View()(
                MockElement(self.props.recursion_level + 1)
            )

class ElementLifeCycleTestCase(unittest.TestCase):

    def test_mount_and_dismount(self):
        component = MockElement(0)
        app = engine.RenderEngine(component)
        render_results = app._request_rerender([component])
        render_results.run()
        component.did_mount.assert_called_once()
        component.did_render.assert_called_once()


class OtherMockElement(component.Element):

    @component.register_props
    def __init__(self):
        super().__init__()
        class MockController(object):
            _request_rerender = unittest.mock.MagicMock()
        self._controller = MockController()

class MockBrokenElement(component.Element):

    @component.register_props
    def __init__(self):
        super().__init__()
        class MockController(object):
            def _request_rerender(*args, **kwargs):
                raise ValueError("I am broken")
        self._controller = MockController()


class StorageManagerTestCase(unittest.TestCase):

    def test_record(self):
        class A(object):
            value = 0
        obj = A()
        with engine._storage_manager() as storage_manager:
            storage_manager.set(obj, "value", 1)
            self.assertEqual(obj.value, 1)
        self.assertEqual(obj.value, 1)

    def test_record(self):
        class A(object):
            value = 0
        obj = A()
        try:
            with engine._storage_manager() as storage_manager:
                storage_manager.set(obj, "value", 1)
                self.assertEqual(obj.value, 1)
                raise ValueError
        except ValueError:
            pass
        self.assertEqual(obj.value, 0)

class ElementTestCase(unittest.TestCase):

    def test_render_changes(self):
        a = OtherMockElement()
        a.foo = 1
        a.bar = 2
        with a.render_changes():
            a.foo = 3
            self.assertEqual(a.foo, 3)
            a.bar = 0
        self.assertEqual(a.foo, 3)
        self.assertEqual(a.bar, 0)
        a._controller._request_rerender.assert_called_once()
        a._controller._request_rerender.reset_mock()
        try:
            with a.render_changes():
                a.bar = 1
                self.assertEqual(a.bar, 1)
                a.foo = 1 / 0
        except ZeroDivisionError:
            pass
        self.assertEqual(a.foo, 3)
        self.assertEqual(a.bar, 0)
        a._controller._request_rerender.assert_not_called()

    def test_state_change_unwind(self):
        a = MockBrokenElement()
        a.foo = 1
        a.bar = 2

        exception_thrown = False
        try:
            with a.render_changes():
                a.foo = 3
                self.assertEqual(a.foo, 3)
                a.bar = 0
        except ValueError as e:
            if str(e) == "I am broken":
                exception_thrown = True

        self.assertTrue(exception_thrown)
        self.assertEqual(a.foo, 1)
        self.assertEqual(a.bar, 2)

        exception_thrown = False
        try:
            a.set_state(foo=3, bar=0)
        except ValueError as e:
            if str(e) == "I am broken":
                exception_thrown = True

        self.assertTrue(exception_thrown)
        self.assertEqual(a.foo, 1)
        self.assertEqual(a.bar, 2)

class MakeElementTestCase(unittest.TestCase):

    def test_make_component(self):

        @component.component
        def Element1234(self, prop1, prop2):
            Value(1234)

        self.assertEqual(Element1234.__name__, "Element1234")
        comp = Element1234(1, 2)
        self.assertEqual(comp.__class__, Element1234)
        self.assertEqual(comp.props._d, {"prop1": 1, "prop2": 2, "children": []})
        value_component = comp.render()
        self.assertEqual(value_component.__class__.__name__, "Value")
        # Render to value to update the state
        value_component.render()
        self.assertEqual(value_component.value, 1234)

    def test_make_components(self):

        @component.component
        def Element1234(self, prop1, prop2):
            Value(1337)
            Value(42)
            Value(69)
            Value(420)

        self.assertEqual(Element1234.__name__, "Element1234")
        comp = Element1234(1, 2)
        self.assertEqual(comp.__class__, Element1234)
        self.assertEqual(comp.props._d, {"prop1": 1, "prop2": 2, "children": []})
        components = comp.render()
        for comp in components:
            self.assertEqual(comp.__class__.__name__, "Value")
        for comp in components:
            # Render to value to update the state
            comp.render()
        values = [comp.value for comp in components]
        self.assertEqual(values, [1337, 42, 69, 420])

    def test_make_nested_component(self):

        @component.component
        def A(self):
            Value(13)

        @component.component
        def Element1234(self, prop1, prop2):
            with A():
                Value(9)

        self.assertEqual(Element1234.__name__, "Element1234")
        comp = Element1234(1, 2)
        self.assertEqual(comp.__class__, Element1234)
        self.assertEqual(comp.props._d, {"prop1": 1, "prop2": 2, "children": []})
        root = comp.render()
        self.assertEqual(root.__class__.__name__, "A")
        nested = root.render()
        nested.render()
        self.assertEqual(nested.__class__.__name__, "Value")
        self.assertEqual(nested.value, 13)
        children = root.children
        for child in children:
            child.render()
        values = [comp.value for comp in children]
        self.assertEqual(values, [9])
