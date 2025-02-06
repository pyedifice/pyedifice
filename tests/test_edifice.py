import unittest
import unittest.mock

from edifice import Element, Reference, base_components, component, engine, use_ref
from edifice.engine import CommandType, PropsDict, QtWidgetElement, _dereference_tree, _WidgetTree
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6":
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

if QtWidgets.QApplication.instance() is None:
    app = QtWidgets.QApplication(["-platform", "offscreen"])


class TestReference(unittest.TestCase):
    def test_reference(self):
        class TestComp(Element):
            def __init__(self, parent_render_count):
                super().__init__()
                super()._register_props({"parent_render_count": parent_render_count})
                self.render_count = 0
                self.ref1 = Reference()
                self.ref2 = Reference()

            def _render_element(self):
                self.render_count += 1
                if self.render_count == 1:
                    return base_components.Label("Test").register_ref(self.ref1)
                else:
                    return base_components.Label("Test").register_ref(self.ref2)

        class TestCompWrapper(Element):
            def __init__(self):
                super().__init__()
                self.render_count = 0

            def _render_element(self):
                self.render_count += 1
                if self.render_count == 3:
                    # We do this to force the dismount of TestComp
                    return base_components.Label("Test")
                else:
                    return TestComp(self.render_count)

        root = TestCompWrapper()
        render_engine = engine.RenderEngine(root)
        render_engine._request_rerender([root])
        sub_comp = render_engine._component_tree[root][0]
        label_comp = render_engine._component_tree[sub_comp][0]
        self.assertEqual(sub_comp.ref1(), label_comp)
        self.assertEqual(sub_comp.ref2(), None)

        # Rerender so that ref2 should also point to label
        render_engine._request_rerender([root])
        new_sub_comp = render_engine._component_tree[root][0]
        new_label = render_engine._component_tree[new_sub_comp][0]
        self.assertEqual(new_sub_comp, sub_comp)
        self.assertEqual(new_label, label_comp)
        self.assertEqual(sub_comp.ref1(), label_comp)
        self.assertEqual(sub_comp.ref2(), label_comp)

        # Rerender to test dismount behavior
        render_engine._request_rerender([root])
        new_sub_comp = render_engine._component_tree[root][0]
        self.assertNotIn(sub_comp, render_engine._component_tree)
        self.assertEqual(sub_comp.ref1(), None)
        self.assertEqual(sub_comp.ref2(), None)

    def test_reference2(self):
        """test_reference ported to with-hooks style"""

        sub_comp_ref = []

        @component
        def TestComp(self, parent_render_count):
            if hasattr(self, "render_count"):
                self.render_count += 1
            else:
                self.render_count = 1

            ref0 = use_ref()
            ref1 = use_ref()
            sub_comp_ref.append(ref0)
            sub_comp_ref.append(ref1)

            if self.render_count == 1:
                base_components.Label("Test").register_ref(ref0)
            else:
                base_components.Label("Test").register_ref(ref1)
            return

        @component
        def TestCompWrapper(self):
            if hasattr(self, "render_count"):
                self.render_count += 1
            else:
                self.render_count = 1

            if self.render_count == 3:
                # We do this to force the dismount of TestComp
                base_components.Label("Test")
            else:
                TestComp(self.render_count)

        root = TestCompWrapper()
        render_engine = engine.RenderEngine(root)
        render_engine._request_rerender([root])
        sub_comp = render_engine._component_tree[root][0]
        label_comp = render_engine._component_tree[sub_comp][0]
        self.assertEqual(sub_comp_ref[0](), label_comp)
        self.assertEqual(sub_comp_ref[1](), None)

        # Rerender so that ref1 should also point to label
        render_engine._request_rerender([root])
        new_sub_comp = render_engine._component_tree[root][0]
        new_label = render_engine._component_tree[new_sub_comp][0]
        self.assertEqual(new_sub_comp, sub_comp)
        self.assertEqual(new_label, label_comp)
        self.assertEqual(sub_comp_ref[0](), label_comp)
        self.assertEqual(sub_comp_ref[1](), label_comp)

        # Rerender to test dismount behavior
        render_engine._request_rerender([root])
        new_sub_comp = render_engine._component_tree[root][0]
        assert sub_comp not in render_engine._component_tree
        self.assertEqual(sub_comp_ref[0](), None)
        self.assertEqual(sub_comp_ref[1](), None)


class _TestElementInner(Element):
    def __init__(self, prop_a):
        super().__init__()
        self._register_props(
            {
                "prop_a": prop_a,
            }
        )
        self.state_a = "A"

    def _render_element(self):
        return base_components.VBoxView()(
            base_components.Label(str(self.props["prop_a"])),
            base_components.Label(str(self.state_a)),
        )


class _TestElementOuter(Element):
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

    def __init__(self):
        super().__init__()
        self.state_a = "A"
        self.state_b = "B"
        self.state_c = "C"

    def _render_element(self):
        return base_components.VBoxView()(
            _TestElementInner(self.state_a),
            _TestElementInner(self.state_b),
            base_components.Label(self.state_c),
        )


class _TestElementOuterList(Element):
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

    def _render_element(self):
        if self.use_keys:
            if self.use_state_as_key:
                return base_components.VBoxView()(*[_TestElementInner(text).set_key(text) for text in self.state])
            else:
                return base_components.VBoxView()(
                    *[_TestElementInner(text).set_key(str(i)) for i, text in enumerate(self.state)]
                )
        return base_components.VBoxView()(*[_TestElementInner(text) for text in self.state])


def _commands_for_address(widget_trees: dict[Element, _WidgetTree], qt_tree, address):
    qt_tree = _dereference_tree(widget_trees, qt_tree, address)
    if isinstance(qt_tree.component, base_components.HBoxView) or isinstance(
        qt_tree.component, base_components.VBoxView
    ):
        return qt_tree.component._qt_stateless_commands(widget_trees, engine.props_diff({}, qt_tree.component.props))
    return qt_tree.component._qt_update_commands(widget_trees, engine.props_diff({}, qt_tree.component.props))


class RenderTestCase(unittest.TestCase):
    def test_basic_render(self):
        component = _TestElementOuter()
        app = engine.RenderEngine(component)
        render_result = app._request_rerender([component])
        # qt_tree = render_result.trees[0]
        qt_tree = app._widget_tree[component]
        qt_commands = render_result.commands

        # def C(*args):
        #     return _commands_for_address(app._widget_tree, qt_tree, args)

        # def V(*args):
        #     view = _dereference_tree(app._widget_tree, qt_tree, list(args))
        #     return [
        #         CommandType(view.component._add_child, i, child.underlying) for (i, child) in enumerate(view.children)
        #     ]

        # expected_commands = C(0, 0) + C(0, 1) + V(0) + C(0) + C(1, 0) + C(1, 1) + V(1) + C(1) + C(2) + V() + C()

        self.assertEqual(
            [c.fn.__name__ for c in qt_commands],
            [
                "setText",
                "setText",
                "_add_child",
                "_add_child",
                "setText",
                "setText",
                "_add_child",
                "_add_child",
                "setText",
                "_add_child",
                "_add_child",
                "_add_child",
            ]
        )

        # After everything rendered, a rerender shouldn't involve any commands
        # TODO: make sure this is actually true!
        render_result = app._request_rerender([component])
        qt_tree = app._widget_tree[component]
        qt_commands = render_result.commands
        self.assertEqual(qt_commands, [])

    def test_state_changes(self):
        component = _TestElementOuter()
        app = engine.RenderEngine(component)
        render_result = app._request_rerender([component])
        qt_tree = app._widget_tree[component]
        qt_commands = render_result.commands

        component.state_a = "AChanged"
        render_result = app._request_rerender([component])
        qt_tree = app._widget_tree[component]
        qt_commands = render_result.commands
        # TODO: Make it so that only the label (0, 0) needs to update!
        expected_commands = [
            CommandType(_dereference_tree(app._widget_tree, qt_tree, [0, 0]).component.underlying.setText, "AChanged")
        ]
        self.assertEqual(qt_commands, expected_commands)

        component.state_b = "BChanged"
        render_result = app._request_rerender([component])
        qt_tree = app._widget_tree[component]
        qt_commands = render_result.commands
        expected_commands = [
            CommandType(_dereference_tree(app._widget_tree, qt_tree, [1, 0]).component.underlying.setText, "BChanged")
        ]
        self.assertEqual(qt_commands, expected_commands)

        component.state_c = "CChanged"
        render_result = app._request_rerender([component])
        qt_tree = app._widget_tree[component]
        qt_commands = render_result.commands
        expected_commands = [
            CommandType(_dereference_tree(app._widget_tree, qt_tree, [2]).component.underlying.setText, "CChanged")
        ]

        self.assertEqual(qt_commands, expected_commands)

    def test_keyed_list_add(self):
        component = _TestElementOuterList(True, True)
        app = engine.RenderEngine(component)
        render_result = app._request_rerender([component])
        qt_tree = app._widget_tree[component]
        qt_commands = render_result.commands

        component.state = ["A", "B", "D", "C"]
        render_result = app._request_rerender([component])
        _new_qt_tree = app._widget_tree[component]
        qt_commands = render_result.commands

        self.assertEqual(
            [c.fn.__name__ for c in qt_commands],
            [
                "setText",
                "setText",
                "_add_child",
                "_add_child",
                "_soft_delete_child",
                "_add_child",
                "_add_child",
            ],
        )

    def test_keyed_list_reshuffle(self):
        component = _TestElementOuterList(True, True)
        app = engine.RenderEngine(component)
        render_result = app._request_rerender([component])
        qt_tree = app._widget_tree[component]
        qt_commands = render_result.commands
        qt_tree.children[0]
        qt_tree.children[2]

        component.state = ["C", "B", "A"]
        render_result = app._request_rerender([component])
        qt_commands = render_result.commands

        expected_commands = [
            CommandType(qt_tree.component._soft_delete_child, 2, qt_tree.children[2]),
            CommandType(qt_tree.component._soft_delete_child, 0, qt_tree.children[0]),
            CommandType(qt_tree.component._add_child, 0, qt_tree.children[2].underlying),
            CommandType(qt_tree.component._add_child, 2, qt_tree.children[0].underlying),
        ]

        self.assertEqual(qt_commands, expected_commands)

    def test_keyed_list_nochange(self):
        component = _TestElementOuterList(True, False)
        app = engine.RenderEngine(component)
        render_result = app._request_rerender([component])
        qt_tree = app._widget_tree[component]
        qt_commands = render_result.commands

        component.state = ["C", "B", "A"]
        render_result = app._request_rerender([component])
        qt_commands = render_result.commands

        expected_commands = [
            CommandType(_dereference_tree(app._widget_tree, qt_tree, [0, 0]).component.underlying.setText, "C"),
            CommandType(_dereference_tree(app._widget_tree, qt_tree, [2, 0]).component.underlying.setText, "A"),
        ]
        self.assertEqual(qt_commands, expected_commands)

    def test_keyed_list_delete_child(self):
        component = _TestElementOuterList(True, True)
        app = engine.RenderEngine(component)
        render_result = app._request_rerender([component])
        old_child = app._widget_tree[component].children[2]
        qt_commands = render_result.commands

        component.state = ["A", "B"]
        render_result = app._request_rerender([component])
        _new_qt_tree = app._widget_tree[component]
        qt_commands = render_result.commands

        expected_commands = [CommandType(app._widget_tree[component].component._delete_child, 2, old_child)]

        self.assertEqual(qt_commands, expected_commands)

    def test_one_child_rerender(self):
        class TestCompInner(Element):
            def __init__(self, val):
                super().__init__()
                self._register_props(
                    {
                        "val": val,
                    }
                )
                self.count = 0

            def _render_element(self):
                self.count += 1
                return base_components.Label(str(self.props["val"]))

        class TestCompOuter(Element):
            def _render_element(self):
                return base_components.VBoxView()(TestCompInner(self.value))

        test_comp = TestCompOuter()
        test_comp.value = 2
        app = engine.RenderEngine(test_comp)
        app._request_rerender([test_comp])
        inner_comp = app._component_tree[app._component_tree[test_comp][0]][0]
        self.assertEqual(inner_comp.count, 1)
        self.assertEqual(inner_comp.props["val"], 2)

        test_comp.value = 4
        app._request_rerender([test_comp])
        inner_comp = app._component_tree[app._component_tree[test_comp][0]][0]
        self.assertEqual(inner_comp.count, 2)
        self.assertEqual(inner_comp.props["val"], 4)

    def test_render_exception(self):
        class TestCompInner1(Element):
            def __init__(self, val):
                super().__init__()
                self._register_props(
                    {
                        "val": val,
                    }
                )
                self.count = 0
                self.success_count = 0

            def _render_element(self):
                self.count += 1
                self.success_count += 1
                return base_components.Label(str(self.props["val"]))

        class TestCompInner2(Element):
            def __init__(self, val):
                super().__init__()
                self._register_props(
                    {
                        "val": val,
                    }
                )
                self.count = 0
                self.success_count = 0

            def _render_element(self):
                self.count += 1
                assert self.props["val"] == 8
                self.success_count += 1
                return base_components.Label(str(self.props["val"]))

        class TestCompOuter(Element):
            def _render_element(self):
                return base_components.VBoxView()(
                    TestCompInner1(self.value * 2),
                    TestCompInner2(self.value * 4),
                )

        test_comp = TestCompOuter()
        test_comp.value = 2
        app = engine.RenderEngine(test_comp)
        app._request_rerender([test_comp])
        inner_comp1, inner_comp2 = app._component_tree[app._component_tree[test_comp][0]]
        self.assertEqual(inner_comp1.count, 1)
        self.assertEqual(inner_comp1.props["val"], 4)
        self.assertEqual(inner_comp2.count, 1)
        self.assertEqual(inner_comp2.props["val"], 8)


class RefreshClassTestCase(unittest.TestCase):
    def test_refresh_child(self):
        class OldInnerClass(Element):
            def __init__(self, val):
                super().__init__()
                self._register_props(
                    {
                        "val": val,
                    }
                )
                self.count = 0

            def _render_element(self):
                self.count += 1
                return base_components.Label(str(self.props["val"]))

        class NewInnerClass(Element):
            def __init__(self, val):
                super().__init__()
                self._register_props(
                    {
                        "val": val,
                    }
                )
                self.count = 0

            def _render_element(self):
                self.count += 1
                return base_components.Label(str(self.props["val"] * 2))

        class OuterClass(Element):
            def __init__(self):
                super().__init__()
                self.count = 0

            def _render_element(self):
                self.count += 1
                return base_components.VBoxView()(OldInnerClass(5))

        outer_comp = OuterClass()
        app = engine.RenderEngine(outer_comp)
        app._request_rerender([outer_comp])
        old_inner_comp = app._component_tree[app._component_tree[outer_comp][0]][0]
        assert isinstance(old_inner_comp, OldInnerClass)

        app._refresh_by_class([(OldInnerClass, NewInnerClass)])
        inner_comp = app._component_tree[app._component_tree[outer_comp][0]][0]
        assert isinstance(inner_comp, NewInnerClass)
        self.assertEqual(inner_comp.props["val"], 5)

    def test_refresh_child_component(self):
        """
        @component version of test_refresh_child
        """

        old_inner_render_count = [0]
        new_inner_render_count = [0]
        outer_render_count = [0]

        @component
        def OldInnerClass(self, val):
            old_inner_render_count[0] += 1
            base_components.Label(str(val))

        @component
        def NewInnerClass(self, val):
            new_inner_render_count[0] += 1
            base_components.Label(str(val * 2))

        @component
        def OuterClass(self):
            outer_render_count[0] += 1
            with base_components.VBoxView():
                OldInnerClass(5)

        outer_comp = OuterClass()
        app = engine.RenderEngine(outer_comp)
        app._request_rerender([outer_comp])
        old_inner_comp = app._component_tree[app._component_tree[outer_comp][0]][0]
        assert type(old_inner_comp).__name__ == "OldInnerClass"

        app._refresh_by_class([(OldInnerClass, NewInnerClass)])
        inner_comp = app._component_tree[app._component_tree[outer_comp][0]][0]
        assert old_inner_render_count[0] == 1
        assert type(inner_comp).__name__ == "NewInnerClass"
        self.assertEqual(inner_comp.props["val"], 5)

    def test_refresh_child_error(self):
        class OldInnerClass(Element):
            def __init__(self, val):
                super().__init__()
                self._register_props(
                    {
                        "val": val,
                    }
                )
                self.count = 0

            def _render_element(self):
                self.count += 1
                return base_components.Label(str(self.props["val"]))

        class NewInnerClass(Element):
            def __init__(self, val):
                super().__init__()
                self._register_props(
                    {
                        "val": val,
                    }
                )
                self.count = 0

            def _render_element(self):
                self.count += 1
                assert False
                return base_components.Label(str(self.props["val"] * 2))

        class OuterClass(Element):
            def __init__(self):
                super().__init__()
                self.count = 0

            def _render_element(self):
                self.count += 1
                return base_components.VBoxView()(OldInnerClass(5))

        outer_comp = OuterClass()
        app = engine.RenderEngine(outer_comp)
        app._request_rerender([outer_comp])
        old_inner_comp = app._component_tree[app._component_tree[outer_comp][0]][0]
        assert isinstance(old_inner_comp, OldInnerClass)

        try:
            app._refresh_by_class([(OldInnerClass, NewInnerClass)])
        except AssertionError:
            pass
        inner_comp = app._component_tree[app._component_tree[outer_comp][0]][0]
        assert isinstance(inner_comp, OldInnerClass)
        self.assertEqual(inner_comp.props["val"], 5)

    def test_view_recalculate_children_1(self):
        v = base_components.VBoxView()
        v._initialize()
        children1: list[QtWidgetElement] = [
            base_components.Label("A"),
            base_components.Button("B"),
            base_components.RadioButton(False, "C"),
        ]
        for c in children1:
            c._qt_update_commands({}, PropsDict({}))

        v._widget_children = children1[:]
        new_children = [
            children1[0],
            children1[1],
        ]
        commands = v._recompute_children(new_children)
        self.assertEqual(
            commands,
            [
                CommandType(v._delete_child, 2, children1[2]),
            ],
        )

        v._widget_children = children1[:]
        new_children = [
            children1[2],
            children1[1],
            children1[0],
        ]
        commands = v._recompute_children(new_children)
        self.assertEqual(
            commands,
            [
                CommandType(v._soft_delete_child, 2, children1[2]),
                CommandType(v._soft_delete_child, 0, children1[0]),
                CommandType(v._add_child, 0, children1[2].underlying),
                CommandType(v._add_child, 2, children1[0].underlying),
            ],
        )


if __name__ == "__main__":
    unittest.main()
