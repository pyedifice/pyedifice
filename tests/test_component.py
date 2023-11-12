import unittest
import unittest.mock
import edifice._component as component
from edifice.app import App
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
    base_components.View()

@component.component
def Bad(self, flag):
    if not hasattr(self, "flag"):
        self.flag = flag
    if self.flag:
        raise ValueError("This should error")
    base_components.View()

class MockElement(component.Element):

    def __init__(self, recursion_level):
        self._register_props({
            "recursion_level": recursion_level,
        })
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

    def __init__(self):
        super().__init__()
        class MockController(object):
            _request_rerender = unittest.mock.MagicMock()
        self._controller = MockController()

class MockBrokenElement(component.Element):

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
        with component.Container() as container:
            comp.render()
        value_component = container.children[0]
        self.assertEqual(value_component.__class__.__name__, "Value")
        # Render to value to update the state
        value_component.render()
        self.assertEqual(value_component.value, 1234)

    def test_make_components(self):

        @component.component
        def Element1234(self, prop1, prop2):
            with base_components.View():
                Value(1337)
                Value(42)
                Value(69)
                Value(420)

        self.assertEqual(Element1234.__name__, "Element1234")
        comp = Element1234(1, 2)
        self.assertEqual(comp.__class__, Element1234)
        self.assertEqual(comp.props._d, {"prop1": 1, "prop2": 2, "children": []})
        with component.Container() as container:
            comp.render()
        view = container.children[0]
        components = view.children
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
        with component.Container() as container:
            comp.render()
        root = container.children[0]
        self.assertEqual(root.__class__.__name__, "A")
        with component.Container() as container:
            root.render()
        nested = container.children[0]
        nested.render()
        self.assertEqual(nested.__class__.__name__, "Value")
        self.assertEqual(nested.value, 13)
        children = root.children
        for child in children:
            child.render()
        values = [comp.value for comp in children]
        self.assertEqual(values, [9])

    def test_raised_errors(self):
        component = Bad(False)
        app = App(component, create_application=False)
        def update():
            try:
                with component.render_changes():
                    component.flag = True
            except ValueError as e:
                self.assertEqual(e.__str__(), "This should error")
        with app.start_loop() as loop:
            loop.call_later(0.1, loop.stop)
            loop.call_soon(update)
            loop.run_forever()
