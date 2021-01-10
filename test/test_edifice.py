import unittest
import unittest.mock
import edifice.component as component
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

class MockApp(engine.RenderEngine):
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

class MockRenderContext(engine._RenderContext):

    def need_rerender(self, component):
        return True


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

class WidgetTreeTestCase(unittest.TestCase):

    def test_button(self):
        def on_click():
            pass
        button_str = "asdf"
        button = base_components.Button(title=button_str, on_click=on_click)
        button_tree = engine._WidgetTree(button, [])
        with engine._storage_manager() as manager:
            commands = button_tree.gen_qt_commands(MockRenderContext(manager))
        qt_button = button.underlying
        self.assertCountEqual(commands, [(qt_button.setText, button_str), (qt_button.setStyleSheet, "QWidget#%s{min-width: 52;min-height: 13}" % id(button)), (button._set_on_click, on_click)])

    def test_view_layout(self):
        view_c = base_components.View(layout="column")
        view_c._initialize()
        self.assertEqual(view_c.underlying_layout.__class__, QtWidgets.QVBoxLayout)
        view_r = base_components.View(layout="row")
        view_r._initialize()
        self.assertEqual(view_r.underlying_layout.__class__, QtWidgets.QHBoxLayout)


    def test_view_change(self):
        label1 = base_components.Label(text="A")
        label2 = base_components.Label(text="B")
        view = base_components.View()(label1)

        def label_tree(label):
            tree = engine._WidgetTree(label, [])
            with engine._storage_manager() as manager:
                return tree, tree.gen_qt_commands(MockRenderContext(manager))

        label1_tree, label1_commands = label_tree(label1)
        label2_tree, label2_commands = label_tree(label2)
        view_tree = engine._WidgetTree(view, [label1_tree])
        with engine._storage_manager() as manager:
            commands = view_tree.gen_qt_commands(MockRenderContext(manager))

        self.assertCountEqual(commands, label1_commands + [(view.underlying.setStyleSheet, "QWidget#%s{min-width: 13;min-height: 13}" % id(view)), (view.underlying_layout.insertWidget, 0, label1.underlying)])

        view_tree = engine._WidgetTree(view, [label1_tree, label2_tree])
        with engine._storage_manager() as manager:
            commands = view_tree.gen_qt_commands(MockRenderContext(manager))
        self.assertCountEqual(commands, label1_commands + label2_commands + [(view.underlying.setStyleSheet, "QWidget#%s{min-width: 26;min-height: 26}" % id(view)), (view.underlying_layout.insertWidget, 1, label2.underlying)])

        inner_view = base_components.View()

        view_tree = engine._WidgetTree(view, [label2_tree, engine._WidgetTree(inner_view, [])])
        with engine._storage_manager() as manager:
            commands = view_tree.gen_qt_commands(MockRenderContext(manager))
        self.assertCountEqual(
            commands, 
            label2_commands + [
                (view.underlying.setStyleSheet, "QWidget#%s{min-width: 13;min-height: 13}" % id(view)),
                (inner_view.underlying.setStyleSheet, "QWidget#%s{min-width: 0;min-height: 0}" % id(inner_view)),
                (view._delete_child, 0),
                (view.underlying_layout.insertWidget, 1, inner_view.underlying)
            ])



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
        app = MockApp(component)
        _, (qt_tree, qt_commands) = app._request_rerender([component], {}, {}, execute=False)[0]

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
        _, (_, qt_commands) = app._request_rerender([component], {}, {}, execute=False)[0]
        self.assertEqual(qt_commands, [])

    def test_state_changes(self):
        component = _TestComponentOuter()
        app = MockApp(component)
        _, (qt_tree, qt_commands) = app._request_rerender([component], {}, {}, execute=False)[0]

        component.state_a = "AChanged"
        _, (_new_qt_tree, qt_commands) = app._request_rerender([component], {}, {}, execute=False)[0]
        # TODO: Make it so that only the label (0, 0) needs to update!
        expected_commands = [(qt_tree._dereference([0, 0]).component.underlying.setText, "AChanged")]
        self.assertEqual(qt_commands, expected_commands)

        component.state_b = "BChanged"
        _, (_, qt_commands) = app._request_rerender([component], {}, {}, execute=False)[0]
        expected_commands = [(qt_tree._dereference([1, 0]).component.underlying.setText, "BChanged")]
        self.assertEqual(qt_commands, expected_commands)

        component.state_c = "CChanged"
        _, (_new_qt_tree, qt_commands) = app._request_rerender([component], {}, {}, execute=False)[0]
        expected_commands = [(qt_tree._dereference([2]).component.underlying.setText, "CChanged")]
        self.assertEqual(qt_commands, expected_commands)

    def test_keyed_list_add(self):
        component = _TestComponentOuterList(True, True)
        app = MockApp(component)
        _, (qt_tree, qt_commands) = app._request_rerender([component], {}, {}, execute=False)[0]

        component.state = ["A", "B", "D", "C"]
        _, (_new_qt_tree, qt_commands) = app._request_rerender([component], {}, {}, execute=False)[0]

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
        app = MockApp(component)
        _, (qt_tree, qt_commands) = app._request_rerender([component], {}, {}, execute=False)[0]

        component.state = ["C", "B", "A"]
        _, (_new_qt_tree, qt_commands) = app._request_rerender([component], {}, {}, execute=False)[0]

        expected_commands = (
                             [(qt_tree.component._soft_delete_child, 0,)]
                             + [(qt_tree.component.underlying_layout.insertWidget, 0, qt_tree.children[2].component.underlying)]
                             + [(qt_tree.component._soft_delete_child, 2,)]
                             + [(qt_tree.component.underlying_layout.insertWidget, 2, qt_tree.children[0].component.underlying)])

        self.assertEqual(qt_commands, expected_commands)

    def test_keyed_list_nochange(self):
        component = _TestComponentOuterList(True, False)
        app = MockApp(component)
        _, (qt_tree, qt_commands) = app._request_rerender([component], {}, {}, execute=False)[0]

        component.state = ["C", "B", "A"]
        _, (_new_qt_tree, qt_commands) = app._request_rerender([component], {}, {}, execute=False)[0]

        expected_commands = [(qt_tree._dereference([0, 0]).component.underlying.setText, "C"), (qt_tree._dereference([2, 0]).component.underlying.setText, "A")]
        self.assertEqual(qt_commands, expected_commands)

    def test_keyed_list_delete_child(self):
        component = _TestComponentOuterList(True, True)
        app = MockApp(component)
        _, (qt_tree, qt_commands) = app._request_rerender([component], {}, {}, execute=False)[0]

        component.state = ["A", "B"]
        _, (_new_qt_tree, qt_commands) = app._request_rerender([component], {}, {}, execute=False)[0]

        expected_commands = [(qt_tree.component._delete_child, 2,)]

        self.assertEqual(qt_commands, expected_commands)


if __name__ == "__main__":
    unittest.main()
