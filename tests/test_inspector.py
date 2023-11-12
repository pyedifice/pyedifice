import unittest
import unittest.mock
import edifice
from edifice.inspector import inspector


class ElementB(edifice.Element):

    def __init__(self, a, b, c):
        self._register_props({
            "a": a,
            "b": b,
            "c": c,
        })
        super().__init__()
        self.state = 0

    def render(self):
        return edifice.Label("Test")

class ElementA(edifice.Element):

    def render(self):
        return ElementB(a=1, b=2, c=3)


class InspectorTestCase(unittest.TestCase):

    def test_inspector_render(self):
        comp_b = ElementB(a=1, b=2, c=3)
        root = ElementA()
        component_tree = {
            root: comp_b,
            comp_b: []
        }

        inspector_component = inspector.Inspector(
            component_tree, root, (lambda: component_tree, root))
        inspector_component.selected = comp_b
        inspector_component.render()
        inspector.ElementView(comp_b).render()
        inspector.StateView(comp_b).render()
        inspector.TreeView(root, root.__class__.__name__,
                           lambda e: None, lambda: [], lambda: True,).render()
        inspector.ElementLabel(
            root,
            on_click = lambda e: None).render()
        inspector.Collapsible(
            collapsed=True, on_click=lambda e: None,
            root=object(),
            toggle=lambda e: None).render()
