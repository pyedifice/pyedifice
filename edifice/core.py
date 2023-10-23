import asyncio
from collections.abc import Callable
import signal
import sys
import threading
from typing import Generic, ParamSpec, TypeVar, cast, overload, Literal, Optional
import functools
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtAsyncio import QAsyncioEventLoopPolicy

from PySide6.QtCore import QObject, Signal, Slot

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

CHILDREN: str = "children"

class Element(Generic[W]):
    def __init__(
        self,
        component: "Component",
        name: str,
        args=None,
        kwargs=None,
    ) -> None:
        self.component = component
        self._current_context = None
        self.args = args or []
        self.kwargs = kwargs or {}
        self.name = name
        ctx = get_render_context(required=False)
        if ctx is not None and len(ctx.trackers) > 0:
            ctx.trackers[-1].add(self)
        else:
            if ctx is not None:
                print(ctx.trackers)
        print("init", self.name)

    def __enter__(self):
        print("enter", self.name)
        ctx = get_render_context()
        tracker = Tracker(self)
        ctx.trackers.append(tracker)
        return self

    def __exit__(self, *args):
        print("exit", self.name)
        ctx = get_render_context()
        tracker = ctx.trackers.pop()
        children = tracker.collect()
        # Mutate kwargs to include children
        print(self.name, children)
        if CHILDREN not in self.kwargs:
            self.kwargs[CHILDREN] = []
        for child in children:
            self.kwargs[CHILDREN].append(child)
        ctx.element = self

    def __repr__(self) -> str:
        name = self.name
        kids = [c.__repr__() for c in self.kwargs.get(CHILDREN, [])]
        children = ", ".join(kids)
        return f"{name}({children})"

class FunctionComponent:
    def __init__(self, name: str, render: Callable[..., Element | None]) -> None:
        self.render = render
        self.name = name
        functools.update_wrapper(self, render)

    def __call__(self, *args, **kwargs):
        element: Element = Element(self, name=self.name, args=args, kwargs=kwargs)
        return element

class QtComponent:
    def __init__(self, name: str) -> None:
        self.name = name

    def __call__(self, *args, **kwargs) -> Element:
        el: Element = Element(self, name=self.name, args=args, kwargs=kwargs)
        return el

class RowComponent(QtComponent):
    def __init__(self, name: str) -> None:
        self.name = name
        self.widget = QWidget()
        self.layout = QHBoxLayout(self.widget)

Component = FunctionComponent | QtComponent


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
        component = FunctionComponent(name, render=fn)
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
        with container() as main:
            match element.component:
                case FunctionComponent():
                    root = element.component.render(*element.args, **element.kwargs)
                case QtComponent():
                    raise NotImplementedError
        if root is None:
            root = main

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
def container():
    pass

# Example components

def Row(children: tuple[Element, ...] = ()):
    name = "Row"
    print(children)
    component = RowComponent(name)
    return Element(component, name)


@component
def Label(text: str):
    pass

@component
def View():
    print("in View")
    with Row():
        with Label(text="Hello"):
            Label(text="Asd")
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

def main():
    QApplication(sys.argv)
    main_window = QMainWindow()
    el = View()
    ctx = _RenderContext(el)
    ctx.render(el)
    main_window.show()

    # row = QWidget()
    # main_window.setCentralWidget(row)
    # box = QVBoxLayout(row)
    # box.addWidget(QLabel(text="asd"))
    # row2 = QWidget()
    # box2 = QHBoxLayout(row2)
    # box.addWidget(row2)
    # col = QWidget()
    # box2.addWidget(col)
    # col2 = QWidget()
    # box2.addWidget(col2)
    # box3 = QVBoxLayout(col)
    # box3.addWidget(QLabel(text="fgh"))
    # box4 = QVBoxLayout(col2)
    # box4.addWidget(QLabel(text="jkl"))
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    asyncio.set_event_loop_policy(QAsyncioEventLoopPolicy())
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()
