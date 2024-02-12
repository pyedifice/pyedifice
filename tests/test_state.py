from collections import OrderedDict

import unittest
import unittest.mock
import edifice.state as state
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


class MockApp(object):

    def __init__(self, component):
        self._root = component
        self._render_engine = engine.RenderEngine(self._root, self)
        self.render_count = 0

    def __hash__(self):
        return id(self)

    def _request_rerender(self, components, newstate=None):
        self.render_count += 1
        self._render_engine._request_rerender(components)


class TopologicalUpdateTestCase(unittest.TestCase):

    def test_add(self):
        class Node(object):
            def __init__(self, ancestor=None):
                self._edifice_internal_parent = ancestor

            def __hash__(self):
                return id(self)

        node_a = Node()
        node_b = Node(node_a)
        node_d = Node(node_b)
        node_c = Node(node_a)
        node_e = Node(node_b)
        node_f = Node(node_a)
        node_g = Node(node_f)
        node_h = Node(node_c)
        previous = OrderedDict([
            (node_a, set()),
            (node_b, set([node_a])),
            (node_d, set([node_a, node_b])),
            (node_c, set([node_a])),
            (node_e, set([node_a, node_b])),
            (node_g, set([node_a, node_f])),
        ])

        new_comp = state._add_subscription(previous, node_f)
        self.assertEqual(
            list(new_comp.keys()), [node_a, node_b, node_d, node_c, node_e,
                               node_f, node_g])
        previous = new_comp
        new_comp = state._add_subscription(previous, node_h)
        self.assertEqual(
            list(new_comp.keys()), [node_a, node_b, node_d, node_c, node_e,
                               node_f, node_g, node_h])


class StateValueTestCase(unittest.TestCase):

    def test_subscribe(self):
        state_value = state.StateValue(2)
        class TestComp(component.Element):
            def _render_element(self):
                if not hasattr(self, "render_called_count"):
                    self.render_called_count = 0
                self.value = state_value.subscribe(self)
                self.render_called_count += 1
                return base_components.Label(self.value)

        test_comp = TestComp()
        app = MockApp(test_comp)
        app._request_rerender([test_comp])
        self.assertEqual(test_comp.render_called_count, 1)
        self.assertEqual(test_comp.value, 2)

        state_value.set(5)
        self.assertEqual(test_comp.render_called_count, 2)
        self.assertEqual(test_comp.value, 5)
        self.assertEqual(state_value.value, 5)

    def test_subscribe_error(self):
        state_value = state.StateValue(2)

        class InnerComp(component.Element):

            def __init__(self, val):
                self._register_props({
                    "val": val,
                })
                super().__init__()

            def _render_element(self):
                assert self.props.val == 2
                return base_components.Label(self.props.val)

        class TestComp(component.Element):

            def __init___(self):
                super().__init__()

            def _render_element(self):
                if not hasattr(self, "render_called_count"):
                    self.render_called_count = 0
                self.value = state_value.subscribe(self)
                self.render_called_count += 1
                return InnerComp(self.value)

        test_comp = TestComp()
        app = MockApp(test_comp)
        app._request_rerender([test_comp])
        inner_comp = app._render_engine._component_tree[test_comp][0]
        self.assertEqual(test_comp.render_called_count, 1)
        self.assertEqual(test_comp.value, 2)
        self.assertEqual(inner_comp.props.val, 2)

        try:
            state_value.set(5)
        except AssertionError:
            pass
        inner_comp = app._render_engine._component_tree[test_comp][0]
        self.assertEqual(test_comp.render_called_count, 2)
        self.assertEqual(test_comp.value, 5)
        self.assertEqual(state_value.value, 2)
        self.assertEqual(inner_comp.props.val, 2)


class StateManagerTestCase(unittest.TestCase):

    def test_subscribe(self):
        state_manager = state.StateManager({
            "key1": 1,
            "key2": 2,
        })

        class TestComp1(component.Element):
            def trigger_update(self):
                self.state_value = state_manager.subscribe(self, "key2")
                self.state_value.set(5)

            def _render_element(self):
                if not hasattr(self, "render_called_count"):
                    self.render_called_count = 0
                self.value = state_manager.subscribe(self, "key1").value
                self.render_called_count += 1
                return base_components.Label(self.value)

        class TestComp2(component.Element):
            def _render_element(self):
                if not hasattr(self, "render_called_count"):
                    self.render_called_count = 0
                self.value = state_manager.subscribe(self, "key2").value
                self.render_called_count += 1
                return base_components.Label(self.value)

        class TestComp(component.Element):
            def _render_element(self):
                if not hasattr(self, "render_called_count"):
                    self.render_called_count = 0
                self.render_called_count += 1
                return base_components.View()(
                    TestComp1(),
                    TestComp2(),
                )

        def extract_inner_components(comp):
            tree = app._render_engine._component_tree
            return tree[tree[comp][0]]

        test_comp = TestComp()
        app = MockApp(test_comp)
        app._request_rerender([test_comp])

        test_comp1, test_comp2 = extract_inner_components(test_comp)

        self.assertEqual(test_comp.render_called_count, 1)
        self.assertEqual(test_comp1.value, 1)
        self.assertEqual(test_comp1.render_called_count, 1)
        self.assertEqual(test_comp2.value, 2)
        self.assertEqual(test_comp2.render_called_count, 1)

        state_manager.update({
            "key1": 11
        })
        test_comp1, test_comp2 = extract_inner_components(test_comp)

        self.assertEqual(test_comp.render_called_count, 1)
        self.assertEqual(test_comp1.value, 11)
        self.assertEqual(test_comp1.render_called_count, 2)
        self.assertEqual(test_comp2.value, 2)
        self.assertEqual(test_comp2.render_called_count, 1)
        self.assertEqual(app.render_count, 2)

        state_manager.update({
            "key1": 11,
            "key2": 21,
        })
        test_comp1, test_comp2 = extract_inner_components(test_comp)

        self.assertEqual(test_comp.render_called_count, 1)
        self.assertEqual(test_comp1.value, 11)
        self.assertEqual(test_comp1.render_called_count, 3)
        self.assertEqual(test_comp2.value, 21)
        self.assertEqual(state_manager["key2"], 21)
        self.assertEqual(test_comp2.render_called_count, 2)
        self.assertEqual(app.render_count, 3)

        test_comp1.trigger_update()
        test_comp1, test_comp2 = extract_inner_components(test_comp)
        self.assertEqual(state_manager["key2"], 5)
        self.assertEqual(test_comp2.value, 5)
        self.assertEqual(test_comp2.render_called_count, 3)
        self.assertEqual(app.render_count, 4)


    def test_subscribe_error(self):
        state_manager = state.StateManager({
            "key1": 1,
            "key2": 2,
        })

        class TestComp1(component.Element):
            def _render_element(self):
                if not hasattr(self, "render_called_count"):
                    self.render_called_count = 0
                self.value = state_manager.subscribe(self, "key1").value
                self.render_called_count += 1
                return base_components.Label(self.value)

        class TestComp2(component.Element):
            def _render_element(self):
                if not hasattr(self, "render_called_count"):
                    self.render_called_count = 0
                self.value = state_manager.subscribe(self, "key2").value
                self.render_called_count += 1
                assert self.value == 2
                return base_components.Label(self.value)

        class TestComp(component.Element):
            def _render_element(self):
                if not hasattr(self, "render_called_count"):
                    self.render_called_count = 0
                self.render_called_count += 1
                return base_components.View()(
                    TestComp1(),
                    TestComp2(),
                )

        def extract_inner_components(comp):
            tree = app._render_engine._component_tree
            return tree[tree[comp][0]]

        test_comp = TestComp()
        app = MockApp(test_comp)
        app._request_rerender([test_comp])

        test_comp1, test_comp2 = extract_inner_components(test_comp)

        self.assertEqual(test_comp.render_called_count, 1)
        self.assertEqual(test_comp1.value, 1)
        self.assertEqual(test_comp1.render_called_count, 1)
        self.assertEqual(test_comp2.value, 2)
        self.assertEqual(test_comp2.render_called_count, 1)

        try:
            state_manager.update({
                "key1": 11,
                "key2": 21,
            })
        except AssertionError:
            pass
        test_comp1, test_comp2 = extract_inner_components(test_comp)

        self.assertEqual(test_comp.render_called_count, 1)
        self.assertEqual(test_comp2.value, 21)
        self.assertEqual(test_comp2.render_called_count, 2)
        self.assertEqual(app.render_count, 2)
        self.assertEqual(state_manager["key1"], 1)
        self.assertEqual(state_manager["key2"], 2)
