import inspect
import typing as tp
import edifice as ed
from edifice.engine import _HookState, PropsDict
from collections import defaultdict

SELECTION_COLOR = "#ACCEF7"


@ed.component
def ElementLabel(self, root: ed.Element, current_selection: ed.Element | None, on_click: tp.Callable[[], None]):
    setattr(self, "__edifice_inspector_element", True)
    ed.Label(
        root.__class__.__name__,
        style={"background-color": SELECTION_COLOR} if root == current_selection else {},
        on_click=lambda _ev: on_click(),
    )


@ed.component
def Collapsible(
    self,
    root: ed.Element,
    current_selection: ed.Element | None,
    collapsed: bool,
    on_click: tp.Callable[[], None],
    toggle: tp.Callable[[], None],
):
    setattr(self, "__edifice_inspector_element", True)
    root_style: dict[str, tp.Any] = {"margin-left": 5}
    if root == current_selection:
        root_style["background-color"] = SELECTION_COLOR
    with ed.View(layout="row", style={"align": "left"}):
        ed.Icon(
            "caret-right",
            rotation=0 if collapsed else 90,
            on_click=lambda _ev: toggle(),
        )
        ed.Label(root.__class__.__name__, style=root_style, on_click=lambda _ev: on_click())


@ed.component
def TreeView(
    self,
    root: ed.Element,
    current_selection: ed.Element | None,
    on_click: tp.Callable[[], None],
    load_fun: list[tp.Callable[[], None]],
):
    setattr(self, "__edifice_inspector_element", True)

    collapsed, collapsed_set = ed.use_state(True)

    child_style = {"align": "top", "margin-left": 20}
    if collapsed:
        child_style["height"] = 0
    with ed.View(layout="column", style={"align": "top"}):
        Collapsible(
            root=root,
            current_selection=current_selection,
            collapsed=collapsed,
            on_click=on_click,
            toggle=lambda: collapsed_set(lambda p: not p),
        )
        with ed.View(
            layout="column",
            style=child_style,
        ):
            if not collapsed:
                for comp_fn in load_fun:
                    comp_fn()


@ed.component
def StateView(
    self,
    component: ed.Element,
    hook_state: defaultdict[ed.Element, list[_HookState]],
    refresh_trigger: bool,  # force a refresh when this changes
):
    setattr(self, "__edifice_inspector_element", True)

    with ed.ScrollView(
        layout="column",
        style={"align": "top", "margin-left": 15},
    ):
        if component in hook_state:
            for s in hook_state[component]:
                with ed.View(
                    layout="row",
                    style={"align": "left"},
                ):
                    ed.Label(
                        text=str(s.state),
                        selectable=True,
                    )


@ed.component
def PropsView(self, props: PropsDict):
    setattr(self, "__edifice_inspector_element", True)
    with ed.ScrollView(layout="column", style={"align": "top", "margin-left": 15}):
        for key in props._keys:
            with ed.View(
                layout="row",
                style={"align": "left"},
            ):
                ed.Label(
                    key + ":",
                    selectable=True,
                    style={"font-weight": 600, "width": 140},
                )
                ed.Label(
                    props[key],
                    selectable=True,
                    style={},
                )


@ed.component
def ElementView(
    self,
    component: ed.Element,
    hook_state: defaultdict[ed.Element, list[_HookState]],
    refresh_trigger: bool,  # force a refresh when this changes
):
    setattr(self, "__edifice_inspector_element", True)
    cls = component.__class__
    if value := getattr(cls, "_edifice_original", None):
        cls = value
    module = inspect.getmodule(cls)
    lineno = None
    try:
        lineno = inspect.getsourcelines(cls)[1]
    except Exception:
        pass
    heading_style = {"font-size": "16px", "margin": 10, "margin-bottom": 0}

    assert module is not None
    with ed.View(layout="column", style={"align": "top", "min-width": 450, "min-height": 450}):
        ed.Label(component.__class__.__name__, selectable=True, style={"font-size": "20px", "margin": 10})
        ed.Label(
            "Class defined in " + str(module.__file__) + ":" + str(lineno), selectable=True, style={"margin-left": 10}
        )
        ed.Label("Props", style=heading_style)
        PropsView(component.props)
        ed.Label("State", style=heading_style)
        StateView(component, hook_state, refresh_trigger)


@ed.component
def Inspector(
    self,
    refresh: tp.Callable[
        [], tuple[dict[ed.Element, list[ed.Element]], ed.Element, defaultdict[ed.Element, list[_HookState]]]
    ],
):
    setattr(self, "__edifice_inspector_element", True)
    component_tree, component_tree_set = ed.use_state(tp.cast(dict[ed.Element, list[ed.Element]], {}))
    root_component, root_component_set = ed.use_state(tp.cast(ed.Element | None, None))
    hook_state, hook_state_set = ed.use_state(tp.cast(defaultdict[ed.Element, list[_HookState]] | None, None))
    selected, selected_set = ed.use_state(tp.cast(ed.Element | None, None))
    refresh_trigger, refresh_trigger_set = ed.use_state(False)

    def _force_refresh():
        component_tree_, root_component_, hook_state_ = refresh()
        component_tree_set(component_tree_)
        root_component_set(root_component_)
        hook_state_set(hook_state_)
        refresh_trigger_set(lambda t: not t)

    def setup():
        self.force_refresh = _force_refresh

    ed.use_effect(setup, [])

    def _build_tree(root: ed.Element, recurse_level=0) -> None:
        children = component_tree[root]
        if len(children) > 0:
            TreeView(
                root=root,
                current_selection=selected,
                on_click=lambda: selected_set(root),
                load_fun=[(lambda child=child: _build_tree(child, recurse_level + 1)) for child in children],
            )
        else:
            ElementLabel(root, current_selection=selected, on_click=lambda: selected_set(root))

    with ed.View(layout="row"):
        if component_tree is not None and root_component is not None and hook_state is not None:
            with ed.View(layout="column", style={"align": "top", "width": 251, "border-right": "1px solid gray"}):
                with ed.View(layout="row", style={"align": "left", "height": 30}):
                    ed.Label("Edifice Inspector", style={"font-size": 18, "margin-left": 10, "width": 160})
                    ed.Icon("sync-alt", size=20, on_click=lambda e: _force_refresh(), tool_tip="Reload component tree")
                with ed.ScrollView(layout="column", style={"width": 250, "min-height": 450, "margin-top": 10}):
                    if root_component is not None:
                        _build_tree(root_component)
            with ed.View(layout="column", style={"min-width": 450, "min-height": 450}):
                if selected is not None:
                    ElementView(
                        selected,
                        hook_state,
                        refresh_trigger,
                    )
