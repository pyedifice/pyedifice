from __future__ import annotations

import importlib.resources
import inspect
import typing as tp

import edifice as ed
from edifice.qt import QT_VERSION

if tp.TYPE_CHECKING:
    from edifice.engine import _HookState

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

SELECTION_COLOR = "#ACCEF7"


@ed.component
def ElementLabel(self, root: ed.Element, current_selection: ed.Element | None, on_click: tp.Callable[[], None]):
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
    root_style: dict[str, tp.Any] = {"margin-left": 5}
    if root == current_selection:
        root_style["background-color"] = SELECTION_COLOR
    with ed.HBoxView(style={"align": "left", "padding-left": 2}):
        if collapsed:
            with ed.VBoxView(
                style={"padding-right": 3, "padding-top": 4, "padding-bottom": 4},
                on_click=lambda _ev: toggle(),
            ):
                ed.ImageSvg(
                    src=str(importlib.resources.files("edifice") / "icons/font-awesome/solid/caret-right.svg"),
                    style={"width": 10, "height": 17},
                )
        else:
            with ed.VBoxView(
                style={"padding-right": 2},
                on_click=lambda _ev: toggle(),
            ):
                ed.ImageSvg(
                    src=str(importlib.resources.files("edifice") / "icons/font-awesome/solid/caret-down.svg"),
                    style={"width": 11, "height": 25},
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
    collapsed, collapsed_set = ed.use_state(True)

    child_style = {"align": "top", "padding-left": 20}
    if collapsed:
        child_style["height"] = 0
    with ed.VBoxView(style={"align": "top"}):
        Collapsible(
            root=root,
            current_selection=current_selection,
            collapsed=collapsed,
            on_click=on_click,
            toggle=lambda: collapsed_set(lambda p: not p),
        )
        with ed.VBoxView(
            style=child_style,
        ):
            if not collapsed:
                for comp_fn in load_fun:
                    comp_fn()


@ed.component
def StateView(
    self: ed.Element,
    component_hook_state: list[_HookState],
    refresh_trigger: bool,  # force a refresh when this changes
):
    with ed.VScrollView(
        style={"align": "top", "padding-left": 15},
    ):
        for s in component_hook_state:
            with ed.HBoxView(
                style={"align": "left"},
            ):
                ed.Label(
                    text=str(s.state),
                    selectable=True,
                    size_policy=QtWidgets.QSizePolicy(
                        QtWidgets.QSizePolicy.Policy.Expanding,
                        QtWidgets.QSizePolicy.Policy.Fixed,
                    ),
                )


@ed.component
def PropsView(self, props: dict[str, tp.Any], refresh_trigger: bool):
    with ed.VScrollView(style={"align": "top", "padding-left": 15}):
        for k, v in props.items():
            if k != "children":
                # It's weird and buggy that if we show the children prop, then
                # it is wrong and shows children from the last selected
                # component. But anyway we just don't show the children prop.
                with ed.HBoxView(
                    style={"align": "left"},
                ):
                    ed.Label(
                        k + ":",
                        selectable=True,
                        style={"font-weight": 600, "width": 140},
                    )
                    ed.Label(
                        text=str(v),
                        selectable=True,
                        size_policy=QtWidgets.QSizePolicy(
                            QtWidgets.QSizePolicy.Policy.Expanding,
                            QtWidgets.QSizePolicy.Policy.Fixed,
                        ),
                    )


@ed.component
def ElementView(
    self,
    component: ed.Element,
    # We pass component_props in as separate props because the component
    # props doesn't have an __eq__ relation.
    component_props: ed.PropsDict,
    component_hook_state: list[_HookState],
    refresh_trigger: bool,  # force a refresh when this changes
):
    cls = component.__class__
    if value := getattr(cls, "_edifice_original", None):
        cls = value
    module = inspect.getmodule(cls)
    lineno = None
    try:
        lineno = inspect.getsourcelines(cls)[1]
    except Exception:  # noqa: S110, BLE001
        pass
    heading_style = {"font-size": "16px", "margin": 10, "margin-bottom": 0}

    with ed.VBoxView(style={"align": "top", "min-width": 450, "min-height": 450}):
        ed.Label(cls.__name__, selectable=True, style={"font-size": "20px", "margin": 10})
        if module is not None:
            ed.Label(
                "Class defined in " + str(module.__file__) + ":" + str(lineno),
                selectable=True,
                style={"margin-left": 10},
            )
        ed.Label("Props", style=heading_style)
        PropsView(component_props, refresh_trigger)
        ed.Label("State", style=heading_style)
        StateView(component_hook_state, refresh_trigger)


@ed.component
def Inspector(
    self,
    refresh: tp.Callable[
        [],
        tuple[dict[ed.Element, list[ed.Element]], ed.Element, dict[ed.Element, list[_HookState]]],
    ],
):
    (selected,), selected_set = ed.use_state(tp.cast(tuple[ed.Element | None], (None,)))
    self._refresh_trigger = not getattr(self, "_refresh_trigger", False)

    component_tree, root_component, hook_state = ed.use_memo(refresh)

    def _build_tree(root: ed.Element, recurse_level=0) -> None:
        children = component_tree[root]
        if len(children) > 0:
            TreeView(
                root=root,
                current_selection=selected,
                on_click=lambda: selected_set((root,)),
                load_fun=[(lambda child=child: _build_tree(child, recurse_level + 1)) for child in children],
            )
        else:
            ElementLabel(root, current_selection=selected, on_click=lambda: selected_set((root,)))

    with ed.HBoxView():
        if component_tree is not None and root_component is not None and hook_state is not None:
            with ed.VBoxView(style={"align": "top", "width": 251, "border-right": "1px solid gray"}):
                with ed.HBoxView(style={"align": "left", "height": 30}):
                    ed.Label("Edifice Inspector", style={"font-size": 18, "margin-left": 10, "width": 160})
                with ed.VScrollView(style={"width": 250, "min-height": 450, "padding-top": 10}):
                    if root_component is not None:
                        _build_tree(root_component)
            with ed.VBoxView(style={"min-width": 450, "min-height": 450}):
                if selected is not None:
                    ElementView(
                        selected,
                        selected.props,
                        hook_state[selected],
                        self._refresh_trigger,
                    )
