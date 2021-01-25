import unittest
import unittest.mock
import edifice._component as component
import edifice.engine as engine
import edifice.base_components as base_components

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt5":
    from PyQt5 import QtWidgets
else:
    from PySide2 import QtWidgets

try:
    app = QtWidgets.QApplication(["-platform", "offscreen"])
except:
    pass


class TestReference(unittest.TestCase):

    def test_reference(self):
        class TestComp(component.Component):
            def __init__(self):
                super().__init__()
                self.render_count = 0
                self.ref1 = component.Reference()
                self.ref2 = component.Reference()

            def render(self):
                self.render_count += 1
                if self.render_count == 1:
                    return base_components.Label("Test").register_ref(self.ref1)
                else:
                    return base_components.Label("Test").register_ref(self.ref2)

        class TestCompWrapper(component.Component):

            def __init__(self):
                super().__init__()
                self.render_count = 0

            def render(self):
                self.render_count += 1
                if self.render_count == 3:
                    # We do this to force the dismount of TestComp
                    return base_components.Label("Test")
                else:
                    return TestComp()

        root = TestCompWrapper()
        render_engine = engine.RenderEngine(root)
        render_engine._request_rerender([root])
        sub_comp = render_engine._component_tree[root]
        label_comp = render_engine._component_tree[sub_comp]
        self.assertEqual(sub_comp.ref1(), label_comp)
        self.assertEqual(sub_comp.ref2(), None)

        # Rerender so that ref2 should also point to label
        render_engine._request_rerender([root])
        new_sub_comp = render_engine._component_tree[root]
        new_label = render_engine._component_tree[new_sub_comp]
        self.assertEqual(new_sub_comp, sub_comp)
        self.assertEqual(new_label, label_comp)
        self.assertEqual(sub_comp.ref1(), label_comp)
        self.assertEqual(sub_comp.ref2(), label_comp)

        # Rerender to test dismount behavior
        render_engine._request_rerender([root])
        new_sub_comp = render_engine._component_tree[root]
        assert sub_comp not in render_engine._component_tree
        self.assertEqual(sub_comp.ref1(), None)
        self.assertEqual(sub_comp.ref2(), None)


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
            return [(view.component._add_child, i, child.component.underlying)
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
            return [(view.component._add_child, i, child.component.underlying)
                    for (i, child) in enumerate(view.children)]

        self.assertEqual(_new_qt_tree._dereference([2, 0]).component.props.text, "D")
        def new_C(*args):
            return _commands_for_address(_new_qt_tree, args)
        expected_commands = (new_C(2, 0) + new_C(2, 1) + new_V(2) + new_C(2) +
                             [(qt_tree.component._add_child, 2, _new_qt_tree.children[2].component.underlying)])

        self.assertEqual(qt_commands, expected_commands)

    def test_keyed_list_reshuffle(self):
        component = _TestComponentOuterList(True, True)
        app = engine.RenderEngine(component)
        render_result = app._request_rerender([component])
        qt_tree = render_result.trees[0]
        qt_commands = render_result.commands
        old_child0 = qt_tree.children[0].component
        old_child2 = qt_tree.children[2].component

        component.state = ["C", "B", "A"]
        render_result = app._request_rerender([component])
        _new_qt_tree = render_result.trees[0]
        qt_commands = render_result.commands

        expected_commands = (
                             [(qt_tree.component._soft_delete_child, 0, old_child0)]
                             + [(qt_tree.component._add_child, 0, qt_tree.children[2].component.underlying)]
                             + [(qt_tree.component._soft_delete_child, 2, old_child2)]
                             + [(qt_tree.component._add_child, 2, qt_tree.children[0].component.underlying)])

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
        old_child = qt_tree.children[2].component
        qt_commands = render_result.commands

        component.state = ["A", "B"]
        render_result = app._request_rerender([component])
        _new_qt_tree = render_result.trees[0]
        qt_commands = render_result.commands

        expected_commands = [(qt_tree.component._delete_child, 2, old_child)]

        self.assertEqual(qt_commands, expected_commands)

    def test_one_child_rerender(self):
        class TestCompInner(component.Component):

            @component.register_props
            def __init__(self, val):
                self.count = 0

            def render(self):
                self.count += 1
                return base_components.Label(self.props.val)

        class TestCompOuter(component.Component):
            def render(self):
                return base_components.View()(TestCompInner(self.value))

        test_comp = TestCompOuter()
        test_comp.value = 2
        app = engine.RenderEngine(test_comp)
        render_result = app._request_rerender([test_comp])
        inner_comp = app._component_tree[app._component_tree[test_comp]][0]
        self.assertEqual(inner_comp.count, 1)
        self.assertEqual(inner_comp.props.val, 2)

        test_comp.value = 4
        render_result = app._request_rerender([test_comp])
        inner_comp = app._component_tree[app._component_tree[test_comp]][0]
        self.assertEqual(inner_comp.count, 2)
        self.assertEqual(inner_comp.props.val, 4)

    def test_render_exception(self):
        class TestCompInner1(component.Component):

            @component.register_props
            def __init__(self, val):
                self.count = 0
                self.success_count = 0

            def render(self):
                self.count += 1
                self.success_count += 1
                return base_components.Label(self.props.val)

        class TestCompInner2(component.Component):

            @component.register_props
            def __init__(self, val):
                self.count = 0
                self.success_count = 0

            def render(self):
                self.count += 1
                assert self.props.val == 8
                self.success_count += 1
                return base_components.Label(self.props.val)

        class TestCompOuter(component.Component):
            def render(self):
                return base_components.View()(
                    TestCompInner1(self.value * 2),
                    TestCompInner2(self.value * 4),
                )

        test_comp = TestCompOuter()
        test_comp.value = 2
        app = engine.RenderEngine(test_comp)
        render_result = app._request_rerender([test_comp])
        inner_comp1, inner_comp2 = app._component_tree[app._component_tree[test_comp]]
        self.assertEqual(inner_comp1.count, 1)
        self.assertEqual(inner_comp1.props.val, 4)
        self.assertEqual(inner_comp2.count, 1)
        self.assertEqual(inner_comp2.props.val, 8)

        test_comp.value = 3
        try:
            render_result = app._request_rerender([test_comp])
        except AssertionError:
            pass
        inner_comp1, inner_comp2 = app._component_tree[app._component_tree[test_comp]]
        self.assertEqual(inner_comp1.props.val, 4)
        self.assertEqual(inner_comp2.count, 2)
        self.assertEqual(inner_comp2.success_count, 1)
        self.assertEqual(inner_comp2.props.val, 8)


class RefreshClassTestCase(unittest.TestCase):

    def test_refresh_child(self):
        class OldInnerClass(component.Component):

            @component.register_props
            def __init__(self, val):
                self.count = 0
                self.will_unmount = unittest.mock.MagicMock()

            def render(self):
                self.count += 1
                return base_components.Label(self.props.val)

        class NewInnerClass(component.Component):

            @component.register_props
            def __init__(self, val):
                self.count = 0

            def render(self):
                self.count += 1
                return base_components.Label(self.props.val * 2)

        class OuterClass(component.Component):

            @component.register_props
            def __init__(self):
                self.count = 0

            def render(self):
                self.count += 1
                return base_components.View()(
                    OldInnerClass(5)
                )

        outer_comp = OuterClass()
        app = engine.RenderEngine(outer_comp)
        app._request_rerender([outer_comp])
        old_inner_comp = app._component_tree[app._component_tree[outer_comp]][0]
        assert isinstance(old_inner_comp, OldInnerClass)

        app._refresh_by_class([(OldInnerClass, NewInnerClass)])
        inner_comp = app._component_tree[app._component_tree[outer_comp]][0]
        old_inner_comp.will_unmount.assert_called_once()
        assert isinstance(inner_comp, NewInnerClass)
        self.assertEqual(inner_comp.props.val, 5)

    def test_refresh_child_error(self):
        class OldInnerClass(component.Component):

            @component.register_props
            def __init__(self, val):
                self.count = 0
                self.will_unmount = unittest.mock.MagicMock()

            def render(self):
                self.count += 1
                return base_components.Label(self.props.val)

        class NewInnerClass(component.Component):

            @component.register_props
            def __init__(self, val):
                self.count = 0

            def render(self):
                self.count += 1
                assert False
                return base_components.Label(self.props.val * 2)

        class OuterClass(component.Component):

            @component.register_props
            def __init__(self):
                self.count = 0

            def render(self):
                self.count += 1
                return base_components.View()(
                    OldInnerClass(5)
                )

        outer_comp = OuterClass()
        app = engine.RenderEngine(outer_comp)
        app._request_rerender([outer_comp])
        old_inner_comp = app._component_tree[app._component_tree[outer_comp]][0]
        assert isinstance(old_inner_comp, OldInnerClass)

        try:
            app._refresh_by_class([(OldInnerClass, NewInnerClass)])
        except AssertionError:
            pass
        inner_comp = app._component_tree[app._component_tree[outer_comp]][0]
        old_inner_comp.will_unmount.assert_not_called()
        assert isinstance(inner_comp, OldInnerClass)
        self.assertEqual(inner_comp.props.val, 5)



if __name__ == "__main__":
    unittest.main()
