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
    def __init__(self):
        super().__init__()
        class MockController(object):
            _request_rerender = unittest.mock.MagicMock()
        self._controller = MockController()

class MockBrokenComponent(component.Component):

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


class ComponentTestCase(unittest.TestCase):

    def test_render_changes(self):
        a = MockComponent()
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
        a = MockBrokenComponent()
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


class _TestComponentInner(component.Component):

    @component.register_props
    def __init__(self, prop_a):
        self.state_a = "A"

    def render(self):
        return base_components.View()(
            base_components.Label(self.props.prop_a),
            base_components.Label(self.state_a),
        )

class _TestComponentOuter(component.Component):
    """
    The rendered tree should be (with index address):
        View(               # []
            View(           # [0]
                Label,      # [0, 0]
                Label)      # [0, 1]
            View(           # [1]
                Label,      # [1, 0]
                Label)      # [1, 1]
            Label           # [2]
        )
    """

    @component.register_props
    def __init__(self):
        self.state_a = "A"
        self.state_b = "B"
        self.state_c = "C"

    def render(self):
        return base_components.View()(
            _TestComponentInner(self.state_a),
            _TestComponentInner(self.state_b),
            base_components.Label(self.state_c),
        )

class _TestComponentOuterList(component.Component):
    """
    The rendered tree should be (with index address):
        View(               # []
            View(           # [0]
                Label,      # [0, 0]
                Label)      # [0, 1]
            View(           # [1]
                Label,      # [1, 0]
                Label)      # [1, 1]
            ...
        )
    """

    def __init__(self, use_keys, use_state_as_key):
        super().__init__()
        self.use_keys = use_keys
        self.use_state_as_key = use_state_as_key
        self.state = ["A", "B", "C"]

    def render(self):
        if self.use_keys:
            if self.use_state_as_key:
                return base_components.View()(
                    *[_TestComponentInner(text).set_key(text) for text in self.state]
                )
            else:
                return base_components.View()(
                    *[_TestComponentInner(text).set_key(str(i)) for i, text in enumerate(self.state)]
                )
        return base_components.View()(
            *[_TestComponentInner(text) for text in self.state]
        )


def _commands_for_address(qt_tree, address):
    qt_tree = qt_tree._dereference(address)
    if isinstance(qt_tree.component, base_components.View):
        return qt_tree.component._qt_stateless_commands(qt_tree.children, qt_tree.component.props, {})
    return qt_tree.component._qt_update_commands(qt_tree.children, qt_tree.component.props, {})


class RenderTestCase(unittest.TestCase):

    def test_basic_render(self):
        component = _TestComponentOuter()
        app = engine.RenderEngine(component)
        render_result = app._request_rerender([component])
        qt_tree = render_result.trees[0]
        qt_commands = render_result.commands

        def C(*args):
            return _commands_for_address(qt_tree, args)

        def V(*args):
            view = qt_tree._dereference(args)
            return [(view.component.underlying_layout.insertWidget, i, child.component.underlying)
                    for (i, child) in enumerate(view.children)]

        expected_commands = C(0, 0) + C(0, 1) + V(0) + C(0) + C(1, 0) + C(1, 1) + V(1) + C(1) + C(2) + V() + C()
        self.assertEqual(qt_commands, expected_commands)

        # After everything rendered, a rerender shouldn't involve any commands
        # TODO: make sure this is actually true!
        render_result = app._request_rerender([component])
        qt_tree = render_result.trees[0]
        qt_commands = render_result.commands
        self.assertEqual(qt_commands, [])

    def test_state_changes(self):
        component = _TestComponentOuter()
        app = engine.RenderEngine(component)
        render_result = app._request_rerender([component])
        qt_tree = render_result.trees[0]
        qt_commands = render_result.commands

        component.state_a = "AChanged"
        render_result = app._request_rerender([component])
        new_qt_tree = render_result.trees[0]
        qt_commands = render_result.commands
        # TODO: Make it so that only the label (0, 0) needs to update!
        expected_commands = [(qt_tree._dereference([0, 0]).component.underlying.setText, "AChanged")]
        self.assertEqual(qt_commands, expected_commands)

        component.state_b = "BChanged"
        render_result = app._request_rerender([component])
        qt_commands = render_result.commands
        expected_commands = [(qt_tree._dereference([1, 0]).component.underlying.setText, "BChanged")]
        self.assertEqual(qt_commands, expected_commands)

        component.state_c = "CChanged"
        render_result = app._request_rerender([component])
        new_qt_tree = render_result.trees[0]
        qt_commands = render_result.commands
        expected_commands = [(qt_tree._dereference([2]).component.underlying.setText, "CChanged")]
        self.assertEqual(qt_commands, expected_commands)

    def test_keyed_list_add(self):
        component = _TestComponentOuterList(True, True)
        app = engine.RenderEngine(component)
        render_result = app._request_rerender([component])
        qt_tree = render_result.trees[0]
        qt_commands = render_result.commands

        component.state = ["A", "B", "D", "C"]
        render_result = app._request_rerender([component])
        _new_qt_tree = render_result.trees[0]
        qt_commands = render_result.commands

        def new_V(*args):
            view = _new_qt_tree._dereference(args)
            return [(view.component.underlying_layout.insertWidget, i, child.component.underlying)
                    for (i, child) in enumerate(view.children)]

        self.assertEqual(_new_qt_tree._dereference([2, 0]).component.props.text, "D")
        def new_C(*args):
            return _commands_for_address(_new_qt_tree, args)
        expected_commands = (new_C(2, 0) + new_C(2, 1) + new_V(2) + new_C(2) +
                             [(qt_tree.component.underlying_layout.insertWidget, 2, _new_qt_tree.children[2].component.underlying)])

        self.assertEqual(qt_commands, expected_commands)

    def test_keyed_list_reshuffle(self):
        component = _TestComponentOuterList(True, True)
        app = engine.RenderEngine(component)
        render_result = app._request_rerender([component])
        qt_tree = render_result.trees[0]
        qt_commands = render_result.commands

        component.state = ["C", "B", "A"]
        render_result = app._request_rerender([component])
        _new_qt_tree = render_result.trees[0]
        qt_commands = render_result.commands

        expected_commands = (
                             [(qt_tree.component._soft_delete_child, 0,)]
                             + [(qt_tree.component.underlying_layout.insertWidget, 0, qt_tree.children[2].component.underlying)]
                             + [(qt_tree.component._soft_delete_child, 2,)]
                             + [(qt_tree.component.underlying_layout.insertWidget, 2, qt_tree.children[0].component.underlying)])

        self.assertEqual(qt_commands, expected_commands)

    def test_keyed_list_nochange(self):
        component = _TestComponentOuterList(True, False)
        app = engine.RenderEngine(component)
        render_result = app._request_rerender([component])
        qt_tree = render_result.trees[0]
        qt_commands = render_result.commands

        component.state = ["C", "B", "A"]
        render_result = app._request_rerender([component])
        _new_qt_tree = render_result.trees[0]
        qt_commands = render_result.commands

        expected_commands = [(qt_tree._dereference([0, 0]).component.underlying.setText, "C"), (qt_tree._dereference([2, 0]).component.underlying.setText, "A")]
        self.assertEqual(qt_commands, expected_commands)

    def test_keyed_list_delete_child(self):
        component = _TestComponentOuterList(True, True)
        app = engine.RenderEngine(component)
        render_result = app._request_rerender([component])
        qt_tree = render_result.trees[0]
        qt_commands = render_result.commands

        component.state = ["A", "B"]
        render_result = app._request_rerender([component])
        _new_qt_tree = render_result.trees[0]
        qt_commands = render_result.commands

        expected_commands = [(qt_tree.component._delete_child, 2,)]

        self.assertEqual(qt_commands, expected_commands)


if __name__ == "__main__":
    unittest.main()
