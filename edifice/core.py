from collections.abc import Callable
import threading
from typing import Any, Generic, ParamSpec, TypeVar, cast, overload, Literal, Optional
from contextlib import ExitStack

local_state = threading.local()

@overload
def get_render_context(*, required: Literal[True] = ...) -> "_RenderContext":
    ...


@overload
def get_render_context(*, required: Literal[False] = ...) -> Optional["_RenderContext"]:
    ...

def get_render_context(*,required: bool = True):
    ctx = getattr(local_state, "render_context", None)
    if ctx is None and required:
        msg = "No render context found"
        raise RuntimeError(msg)
    return ctx

class Tracker:
    def __init__(self, el) -> None:
        self.el = el
        self.created = []

    def add(self, el):
        self.created.append(el)

    def collect(self):
        children = set()
        for el in self.created:
            children |= find_elements(el) - {el}
        return [k for k in self.created if k not in children]

W = TypeVar("W")
P = ParamSpec("P")

class Element(Generic[W]):
    def __init__(
        self, component: "Component",
        name: str,
        args=None,
        kwargs=None,
    ) -> None:
        self.component = component
        self._current_context = None
        self.children = []
        self.args = args or []
        self.kwargs = kwargs or {}
        self.name = name
        ctx = get_render_context(required=False)
        if ctx is not None and len(ctx.trackers) > 0:
            ctx.trackers[-1].add(self)

    def __enter__(self):
        ctx = get_render_context()
        tracker = Tracker(self)
        ctx.trackers.append(tracker)
        return self

    def __exit__(self, *args):
        ctx = get_render_context()
        tracker = ctx.trackers.pop()
        children = tracker.collect()
        for child in children:
            self.children.append(child)
        ctx.element = self

    def __repr__(self) -> str:
        name = self.name
        kids = [c.__repr__() for c in self.children]
        children = ", ".join(kids)
        return f"{name}({children})"

class Component:
    def __init__(self, name: str, render: Callable[..., Element | None]) -> None:
        self.render = render
        self.name = name

    def __call__(self, *args, **kwargs):
        element: Element = Element(self, name=self.name, args=args, kwargs=kwargs)
        return element

F = TypeVar("F", bound=Callable[..., Element])

@overload
def component(fn: None = None) -> Callable[
    [Callable[P, Element | None]],
    Callable[P, Element]
]:
    ...

@overload
def component(fn: Callable[P, None]) -> Callable[P, Element]:
    ...

@overload
def component(fn: F) -> F:
    ...

def component(
    fn: Callable[P, Element | None] | F | None = None,
) -> (
    Callable[[Callable[P, Element | None]], F]
    | F
):
    def wrapper(fn: Callable[P, Element | None] | F) -> F:
        name = fn.__name__
        component = Component(name, render=fn)
        # A component is a Callable[..., Element]
        return cast(F, component)
    if fn is not None:
        value = wrapper(fn)
        return value
    else:
        return wrapper

class _RenderContext:
    def __init__(self, element: Element) -> None:
        self.trackers: list[Tracker] = []
        self.element: Element = element

    def render(self, element: Element):
        local_state.render_context = self
        self.element = element
        self._render(self.element)

    def _render(self, element: Element):
        self.trackers = []
        # TODO: introduce container?
        root = element.component.render(*element.args, **element.kwargs)
        if root is None:
            root = element

def find_elements(el: Element | list[Element]) -> set[Element]:
    match el:
        case Element():
            return {el}
        case list():
            elements = set()
            for child in el:
                elements |= find_elements(child)
            return elements
@component
def Row():
    pass

@component
def Label(text: str):
    pass

@component
def View():
    with Row():
        Label(text="Hello")
        Label(text="Hello")
        Label(text="Hello")

@component
def A():
    pass

@component
def B():
    pass

@component
def example():
    with A():
        with B():
            with A() as inner:
                print(f"inner={inner}")
        with A():
            with B() as inner:
                print(f"inner={inner}")

el = example()
print("CTX")
ctx = _RenderContext(el)
ctx.render(el)
print(ctx.element)
