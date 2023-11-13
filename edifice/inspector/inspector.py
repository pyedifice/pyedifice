import inspect
from typing import Any
import edifice as ed
from edifice.state import StateManager


SELECTION_COLOR = "#ACCEF7"


current_selection = StateManager({
})


class InspectorElement(ed.Element):
    pass


class ElementLabel(InspectorElement):

    def __init__(self, root, on_click):
        self._register_props({
            "root": root,
            "on_click": on_click,
        })
        super().__init__()

    def _should_update(self, newprops, newstate):
        return self.props.root is not newprops.root

    def _render_element(self):
        root = self.props.root
        on_click = self.props.on_click
        try:
            selected = current_selection.subscribe(self, str(id(root))).value
        except KeyError:
            selected = False
        return ed.Label(root.__class__.__name__,
                        style={"background-color": SELECTION_COLOR} if selected else {},
                        on_click=on_click)

class Collapsible(InspectorElement):

    def __init__(self, collapsed, on_click, root, toggle):
        self._register_props({
            "collapsed": collapsed,
            "on_click": on_click,
            "root": root,
            "toggle": toggle,
        })
        super().__init__()

    def _should_update(self, newprops, newstate):
        return newprops._get("root", self.props.root) != self.props.root or newprops._get("collapsed", self.props.collapsed) != self.props.collapsed

    def _render_element(self):
        try:
            selected = current_selection.subscribe(self, str(id(self.props.root))).value
        except KeyError:
            selected = False
        root_style: dict[str, Any] = {"margin-left": 5}
        if selected:
            root_style["background-color"] = SELECTION_COLOR
        return ed.View(layout="row", style={"align": "left"})(
                ed.Icon("caret-right",
                        rotation=0 if self.props.collapsed else 90,
                        on_click=self.props.toggle,
                ).set_key("caret"),
                ed.Label(self.props.root.__class__.__name__, style=root_style, on_click=self.props.on_click).set_key("title"),
            )

class TreeView(InspectorElement):

    def __init__(self, root, on_click, load_fun, must_refresh, initial_collapsed=False):
        self._register_props({
            "root": root,
            "on_click": on_click,
            "load_fun": load_fun,
            "must_refresh": must_refresh,
            "initial_collapsed": initial_collapsed,
        })
        super().__init__()
        self.collapsed = initial_collapsed
        # We load children of the tree lazily, because the component tree can get pretty large!
        self.cached_children = []
        self.cached_children_loaded = False

    def _did_mount(self):
        if not self.props.initial_collapsed:
            with self._render_changes():
                self.cached_children = self.props.load_fun()
                self.cached_children_loaded = True

    def toggle(self, e):
        if not self.cached_children_loaded:
            with self._render_changes():
                self.collapsed = not self.collapsed
                self.cached_children = self.props.load_fun()
                self.cached_children_loaded = True
        else:
            self._set_state(collapsed=not self.collapsed)

    def _should_update(self, newprops, newstate):
        if newstate:
            return True
        if self.props.must_refresh():
            try:
                if self.props.root is not newprops.root:
                    return True
            except KeyError:
                pass
            if not self.cached_children_loaded:
                return False
            return True
        try:
            return self.props.root is not newprops.root
        except KeyError:
            return False


    def _render_element(self):
        child_style = {"align": "top", "margin-left": 20}
        if self.collapsed:
            child_style["height"] = 0
        return ed.View(layout="column", style={"align": "top"})(
            Collapsible(root=self.props.root, on_click=self.props.on_click, toggle=self.toggle,
                        collapsed=self.collapsed).set_key("root"),
            ed.View(layout="column", style=child_style)(
                *[comp.set_key(str(i)) for i, comp in enumerate(self.cached_children)]
            ).set_key("children")
        )

class StateView(InspectorElement):

    def __init__(self, component):
        self._register_props({
            "component": component,
        })
        super().__init__()

    def _render_element(self):
        state = dict((k, v) for (k, v) in vars(self.props.component).items() if k[0] != "_")
        return ed.ScrollView(layout="column", style={"align": "top", "margin-left": 15})(
            *[ed.View(layout="row", style={"align": "left"})(
                  ed.Label(key + ":", selectable=True, style={"font-weight": 600, "width": 140}).set_key("key"),
                  ed.Label(state[key], selectable=True, style={}).set_key("value"),
              ).set_key(key) for key in state]
        )

class PropsView(InspectorElement):

    def __init__(self, props):
        self._register_props({
            "props": props,
        })
        super().__init__()

    def _render_element(self):
        props = self.props.props
        return ed.ScrollView(layout="column", style={"align": "top", "margin-left": 15})(
            *[ed.View(layout="row", style={"align": "left"})(
                  ed.Label(key + ":", selectable=True, style={"font-weight": 600, "width": 140},
                          ).set_key("key"),
                  ed.Label(props[key], selectable=True, style={}).set_key("value"),
              ).set_key(key) for key in props._keys]
        )


class ElementView(InspectorElement):

    def __init__(self, component):
        self._register_props({
            "component": component,
        })
        super().__init__()

    def _render_element(self):
        component = self.props.component
        module = inspect.getmodule(component.__class__)
        lineno = None
        try:
            lineno = inspect.getsourcelines(component.__class__)[1]
        except Exception:
            pass
        heading_style = {"font-size": "16px", "margin": 10, "margin-bottom": 0}

        assert module is not None
        return ed.View(layout="column", style={"align": "top", "min-width": 450, "min-height": 450})(
            ed.Label(component.__class__.__name__,
                     selectable=True,
                     style={"font-size": "20px", "margin": 10}).set_key("class_name"),
            ed.Label("Class defined in " + str(module.__file__) + ":" + str(lineno),
                     selectable=True,
                     style={"margin-left": 10}).set_key("file"),
            ed.Label("Props", style=heading_style).set_key("props_header"),
            PropsView(component.props).set_key("_props_view"),
            ed.Label("State", style=heading_style).set_key("state_header"),
            StateView(component).set_key("_state_view"),
        )


class Inspector(InspectorElement):

    def __init__(self, component_tree, root_component, refresh):
        self._register_props({
            "component_tree": component_tree,
            "root_component": root_component,
            "refresh": refresh,
        })
        super().__init__()
        self.selected: ed.Element | None = None
        self.component_tree = component_tree
        self.root_component = root_component
        self.must_refresh = False
        self._cached_tree = None

    def _refresh(self):
        with self._render_changes():
            self.must_refresh = True
            self.component_tree, self.root_component = self.props.refresh()

    def _did_render(self):
        self.must_refresh = False

    def select_component(self, comp):
        old_selection = self.selected
        self._set_state(selected=comp)
        current_selection.update({
            str(id(comp)): True,
            str(id(old_selection)): False
        })

    def _build_tree(self, root, recurse_level=0):
        children = self.component_tree[root]
        if isinstance(children, ed.Element):
            children = [children]

        if len(children) > 0:
            return TreeView(on_click=lambda e: self.select_component(root),
                            root=root,
                            must_refresh=lambda: self.must_refresh,
                            initial_collapsed=len(children) > 1 or recurse_level > 2,
                            load_fun=lambda: [self._build_tree(child, recurse_level+1) for child in children])

        return ElementLabel(root, on_click=lambda e: self.select_component(root))

    def _render_element(self):
        if self.must_refresh or self._cached_tree is None:
            self._cached_tree = self._build_tree(self.root_component)
        return ed.View(layout="row")(
            ed.View(layout="column", style={"align": "top", "width": 251, "border-right": "1px solid gray"})(
                ed.View(layout="row", style={"align": "left", "height": 30})(
                    ed.Label("Edifice Inspector", style={"font-size": 18, "margin-left": 10, "width": 160}).set_key("title"),
                    ed.Icon("sync-alt", size=20, on_click=lambda e: self._refresh, tool_tip="Reload component tree").set_key("refresh")
                ).set_key("heading"),
                ed.ScrollView(layout="column", style={"width": 250, "min-height": 450, "margin-top": 10})(
                    self._cached_tree
                ).set_key("tree"),
            ).set_key("left_pane"),
            ed.View(layout="column", style={"min-width": 450, "min-height": 450})(
                self.selected and ElementView(self.selected).set_key("component_view")
            ).set_key("right_pane")
        )
