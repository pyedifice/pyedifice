import unittest
import unittest.mock
import edifice
from edifice.inspector import inspector


class ElementB(edifice.Element):
    def __init__(self, a, b, c):
        super().__init__()
        self._register_props(
            {
                "a": a,
                "b": b,
                "c": c,
            }
        )
        self.state = 0

    def _render_element(self):
        return edifice.Label("Test")


class ElementA(edifice.Element):
    def _render_element(self):
        return ElementB(a=1, b=2, c=3)


class InspectorTestCase(unittest.TestCase):
    def test_inspector_render(self):
        pass
        # comp_b = ElementB(a=1, b=2, c=3)
        # root = ElementA()
        # component_tree = {
        #     root: comp_b,
        #     comp_b: []
        # }

        # inspector_component = inspector.Inspector(
        #     component_tree, root, (lambda: component_tree, root))
        # inspector_component.selected = comp_b
        # inspector_component._render_element()
        # inspector.ElementView(comp_b)._render_element()
        # inspector.StateView(comp_b)._render_element()
        # inspector.TreeView(root, root.__class__.__name__, lambda e: None, lambda: [], True)._render_element()
        # inspector.ElementLabel(
        #     root,
        #     on_click = lambda e: None)._render_element()
        # inspector.Collapsible(
        #     collapsed=True, on_click=lambda e: None,
        #     root=object(),
        #     toggle=lambda e: None)._render_element()


if __name__ == "__main__":
    unittest.main()
