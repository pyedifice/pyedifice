from __future__ import annotations

import asyncio
import functools
import inspect
import logging
import threading
import typing as tp
from collections import defaultdict
from collections.abc import Callable, Coroutine, Iterable, Iterator
from copy import copy
from dataclasses import dataclass
from textwrap import dedent

from typing_extensions import Self

from .qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtCore, QtGui, QtWidgets
else:
    from PySide6 import QtCore, QtGui, QtWidgets

_T_use_state = tp.TypeVar("_T_use_state")
_T_Element = tp.TypeVar("_T_Element", bound="Element")
_T_widget = tp.TypeVar("_T_widget", bound=QtWidgets.QWidget)
logger = logging.getLogger("Edifice")

P = tp.ParamSpec("P")



def stylevalue_to_str(v: QtGui.QColor | tp.Any) -> str:
    match v:
        case QtGui.QColor():
            # should be equivalent to f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"
            return v.name(format=QtGui.QColor.NameFormat.HexArgb)
        case _:
            return v

def _dict_to_style(d: dict[str, tp.Any]) -> str:
    return "{" + (";".join(f"{k}: {stylevalue_to_str(v)}" for (k, v) in d.items())) + "}"


# TODO
# https://stackoverflow.com/questions/37278647/fire-and-forget-python-async-await/37345564#37345564
# “Replace asyncio.ensure_future with asyncio.create_task everywhere if you're
# using Python >= 3.7 It's a newer, nicer way to spawn tasks.”


def _ensure_future(fn):
    # Ensures future if fn is a coroutine, otherwise don't modify fn
    if inspect.iscoroutinefunction(fn):

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return asyncio.ensure_future(fn(*args, **kwargs))

        return wrapper
    return fn


class CommandType:
    def __init__(self, fn: Callable[P, tp.Any], *args: P.args, **kwargs: P.kwargs):
        # The return value of fn is ignored and should thus return None. However, in
        # order to test with equality on the CommandTypes we need to allow fn to return
        # Any value to not allocate wrapper functions ignoring the return value.
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return f"{self.fn}(*{self.args},**{self.kwargs})"

    def __repr__(self):
        return f"{self.fn.__repr__()}(*{self.args.__repr__()},**{self.kwargs.__repr__()})"

    def __eq__(self, other):
        if not isinstance(other, CommandType):
            return False
        if self.fn != other.fn:
            return False
        if len(self.args) != len(other.args):
            return False
        if len(self.kwargs) != len(other.kwargs):
            return False
        for i, arg in enumerate(self.args):
            if arg != other.args[i]:
                return False
        for i, arg in self.kwargs.items():
            if arg != other.kwargs[i]:
                return False
        return True

    def __hash__(self):
        return (self.fn, *self.args, *self.kwargs.items()).__hash__()


_T_use_state = tp.TypeVar("_T_use_state")

"""
Deferred function call. A tuple with a Callable, and all of the values of its arguments.
"""


class PropsDict:
    """An immutable dictionary for storing props.

    Props may be accessed either by indexing

        props["myprop"]

    or by attribute

        props.myprop

    By convention, all PropsDict methods will start with :code:`_` to
    not conflict with keys.

    .. document private functions
    .. autoproperty:: _keys
    .. autoproperty:: _items
    """

    __slots__ = ("_d",)

    def __init__(self, dictionary: tp.Mapping[str, tp.Any]):
        super().__setattr__("_d", dictionary)

    def __getitem__(self, key) -> tp.Any:
        return self._d[key]

    def __setitem__(self, key, value) -> tp.NoReturn:
        raise ValueError("Props are immutable")

    @property
    def _keys(self) -> Iterator:
        """Returns the keys of the props dict as a list."""
        return self._d.keys()

    @property
    def _items(self) -> Iterator:
        """Returns the (key, value) of the props dict as a list."""
        return self._d.items()

    def _get(self, key: str, default: tp.Any | None = None) -> tp.Any:
        """Gets item by key.

        Equivalent to dictionary.get(key, default)

        Args:
            key: key to the PropsDict
            default: returned value if key is not found in props
        Returns:
            The corresponding value if key is in PropsDict, the default
            value otherwise.
        """
        return self._d.get(key, default)

    def __len__(self) -> int:
        return len(self._d)

    def __iter__(self):
        return iter(self._d)

    def __contains__(self, k) -> bool:
        return k in self._d

    def __getattr__(self, key) -> tp.Any:
        if key in self._d:
            return self._d[key]
        raise KeyError(str(key) + " not in props")

    def __repr__(self):
        return "PropsDict(" + str(repr(self._d)) + ")"

    def __str__(self) -> str:
        return "PropsDict(" + str(self._d) + ")"

    def __setattr__(self, key, value) -> tp.NoReturn:
        raise ValueError("Props are immutable")


class Reference(tp.Generic[_T_Element]):
    """Reference to an :class:`Element` for imperative commands.

    Edifice tries to abstract away the need to issue
    imperative commands to widgets but this is not always possible and not
    every feature of Qt Widgets is supported by Edifice.
    In some cases, we might need to issue imperative commands to the
    Elements and their underlying Qt Widgets.
    :class:`Reference` gives us access to a rendered :class:`Element`.

    Create a :class:`Reference` with the :func:`use_ref` Hook.

    :func:`Element.register_ref` registers the :class:`Reference` object
    to the :class:`Element`.

    :class:`Reference` can be dereferenced by calling it. An instance of
    type :code:`Reference[Label]` will dereference to an instance of
    :code:`Label` when called.

    Initially, a :class:`Reference` object will dereference to :code:`None`.
    After the first render, it will dereference to the rendered :class:`Element`.
    When the rendered :class:`Element` dismounts, the reference will once again
    dereference to :code:`None`.
    :class:`Reference` is valid whenever it is not :code:`None`.
    :class:`Reference` will evaluate false if the :class:`Element` is :code:`None`.

    Access the QWidget underlying a :class:`QtWidgetElement`,
    through the :code:`underlying` attribute of the :class:`QtWidgetElement`.
    :func:`use_effect` Hooks always run after the Elements are fully rendered.

    .. code-block:: python

        @component
        def MyComp(self):
            label_ref:Reference[Label] = use_ref()

            def did_render():
                label = label_ref()
                if label and label.underlying:
                    # Set the text of the Label’s underlying QLabel widget.
                    label.underlying.setText("After")

            use_effect(did_render, ())

            with VBoxView():
                Label("Before").register_ref(label_ref)
    """

    def __init__(self):
        self._value: _T_Element | None = None

    def __bool__(self) -> bool:
        return self._value is not None

    def __hash__(self) -> int:
        return id(self)

    def __call__(self) -> _T_Element | None:
        return self._value


T = tp.TypeVar("T")


class AppProtocol(tp.Protocol):
    """Protocol for App"""

    def _request_rerender(self, components: Iterable[Element], kwargs: dict[str, tp.Any]):
        pass

    def _defer_rerender(self, element: Element):
        pass

    def stop(self):
        pass


class _Tracker:
    """
    During a render, track the current element and the children being
    added to the current element.
    """

    def __init__(self, component: Element):
        self.component = component
        self.children: list[Element] = []

    def append_child(self, component: Element):
        self.children.append(component)


class _RenderContext:
    """
    Encapsulates various state that's needed for rendering.

    One _RenderContext is created when a render begins, and it is destroyed
    at the end of the render.
    """

    __slots__ = (
        "need_qt_command_reissue",
        "component_to_old_props",
        "component_tree",
        "widget_tree",
        "enqueued_deletions",
        "trackers",
        "_callback_queue",
        "engine",
        "current_element",
    )
    trackers: list[_Tracker]
    """Stack of _Tracker"""
    current_element: Element | None
    """The Element currently being rendered."""

    # I guess static scope typing of instance members is normal in Python?
    # https://peps.python.org/pep-0526/#class-and-instance-variable-annotations
    def __init__(
        self,
        engine: RenderEngine,
    ):
        self.engine = engine
        self.need_qt_command_reissue = {}
        self.component_to_old_props = {}

        self.component_tree: dict[Element, list[Element]] = {}
        """
        Map of a component to its children.
        """
        self.widget_tree: dict[Element, _WidgetTree] = {}
        """
        Map of a component to its rendered widget tree.
        """
        self.enqueued_deletions: list[Element] = []

        self._callback_queue = []

        self.trackers = []

        self.current_element = None

    def mark_props_change(self, component: Element, newprops: PropsDict):
        if component not in self.component_to_old_props:
            self.component_to_old_props[component] = component.props
        component._props = newprops._d

    def get_old_props(self, component):
        if component in self.component_to_old_props:
            return self.component_to_old_props[component]
        return PropsDict({})

    def mark_qt_rerender(self, component: QtWidgetElement, need_rerender: bool):
        self.need_qt_command_reissue[component] = need_rerender

    def need_rerender(self, component: QtWidgetElement):
        return self.need_qt_command_reissue.get(component, False)


local_state = threading.local()


def get_render_context() -> _RenderContext:
    return getattr(local_state, "render_context")  # noqa: B009


def get_render_context_maybe() -> _RenderContext | None:
    return getattr(local_state, "render_context", None)


def child_place(element: Element) -> None:
    """
    Place a child passed through the special :code:`children` **props** into
    the layout of a parent :func:`@component<component>`.
    """
    get_render_context().trackers[-1].append_child(element)


class Element:
    """The base class for Edifice Elements.

    In user code you should almost never use :class:`Element` directly. Instead
    use :doc:`Base Elements <../base_components>` and :func:`@component<component>` Elements.

    A :class:`Element` is a stateful container wrapping a render function.
    Elements have both internal and external properties.

    The external properties, **props**, are passed into the :class:`Element` by another
    :class:`Element`’s render function through the constructor. These values are owned
    by the external caller and should not be modified by this :class:`Element`.
    """

    _render_changes_context: dict | None = None
    _render_unwind_context: dict | None = None
    _controller: AppProtocol | None = None
    _edifice_internal_references: set[Reference[Self]] | None = None

    def __init__(self):
        super().__setattr__("_edifice_internal_references", set())
        self._props: dict[str, tp.Any] = {"children": []}
        # Ensure we only construct this element once
        assert getattr(self, "_initialized", False) is False
        self._initialized = True
        self._key: str | None = None
        ctx = get_render_context_maybe()
        if ctx is not None:
            trackers = ctx.trackers
            if len(trackers) > 0:
                parent = trackers[-1]
                parent.append_child(self)

        # We don't really need these hook indices to be per-instance state.
        # They are only used during a render.
        self._hook_state_index: int = 0
        """use_state hook index for current render."""
        self._hook_effect_index: int = 0
        """use_effect hook index for current render."""
        self._hook_async_index: int = 0
        """use_async hook index for current render."""

    def __enter__(self: Self) -> Self:
        ctx = get_render_context()
        tracker = _Tracker(self)
        ctx.trackers.append(tracker)
        return self

    def __exit__(self, *args):
        ctx = get_render_context()
        tracker = ctx.trackers.pop()
        prop: list[Element] = list(self._props.get("children", ()))
        prop.extend(tracker.children)
        self._props["children"] = tuple(prop)

    def _register_props(self, props: tp.Mapping[str, tp.Any]) -> None:
        """Register props.

        Args:
            props: a dictionary representing the props to register.
        """
        self._props.update(props)

    def set_key(self: Self, key: str | None) -> Self:
        """Set the key of an :class:`Element`.

        The key is used when re-rendering to match new child Elements
        with old child Elements.
        The diffing algorithm will assume that child Elements with the same key
        are identical.

        Each key must be unique and persistent. The **Edifice Rules
        of Keys** are the same as the
        `React Rules of Keys <https://react.dev/learn/rendering-lists#rules-of-keys>`_.

        - **Keys must be unique among siblings.** However, it’s okay to use the same keys for Elements of different parents.
        - **Keys must not change** or that defeats their purpose! Don’t generate them while rendering.

        Returns the Element to allow for chaining.

        Example::

            with VBoxView():
                if english:
                    Label("Hello").set_key("en")
                if french:
                    Label("Bonjour").set_key("fr")
                if spanish:
                    Label("Hola").set_key("es")

        Args:
            key: The Element unique key string.
        Returns:
            The Element.
        """
        self._key = key
        return self

    def register_ref(self: Self, reference: Reference[Self]) -> Self:
        """Registers provided :class:`Reference` to this Element.

        During render, the provided reference will be set to point to the
        currently rendered instance of this Element.

        Args:
            reference: the Reference to register
        Returns:
            The Element self.
        """
        assert self._edifice_internal_references is not None
        self._edifice_internal_references.add(reference)
        return self

    @property
    def children(self) -> tuple[Element, ...]:
        """The children of this Element."""
        return self._props["children"]

    @property
    def props(self) -> PropsDict:
        """The props of this Element."""
        return PropsDict(self._props)

    def _should_update(self, newprops: PropsDict) -> bool:
        """Determines if the Element should rerender upon receiving new props and state.

        The :code:`newprops` reflect the
        props that change: they
        may be a subset of the props. When this function is called,
        all props of this Element are the old values, so you can compare
        :code:`self.props` to :code:`newprops`
        to determine changes.

        Args:
            newprops: the new set of props
        Returns:
            Whether or not the Element should be rerendered.
        """

        # TODO if an Element has children, then _should_update will always
        # return True, because the children will always be different, because
        # _recycle_children hasn't been called yet. Is that correct behavior?

        for k, v in newprops._items:
            if k in self.props:
                # If the prop is in the old props, then we check if it's changed.
                v2 = self.props._get(k)
                if v2 != v:
                    return True
            else:
                # If the prop is not in the old props, then we rerender.
                return True

        return False

    def __call__(self, *args):
        children = []
        for a in args:
            if isinstance(a, list):
                children.extend(a)
            elif a:
                children.append(a)
        self._props["children"] = tuple(children)
        return self

    def __hash__(self):
        return id(self)

    def _tags(self):
        classname = self.__class__.__name__
        return [
            f"<{classname} id=0x%x %s>"
            % (id(self), " ".join(f"{p}={val}" for (p, val) in self.props._items if p != "children")),
            f"</{classname}>",
            f"<{classname} id=0x%x %s />"
            % (id(self), " ".join(f"{p}={val}" for (p, val) in self.props._items if p != "children")),
        ]

    def __str__(self):
        tags = self._tags()
        return tags[2]

    def _render_element(self) -> Element | None:
        """Logic for rendering, must be overridden.

        The render logic for this Element, not implemented for this abstract class.
        The render function itself should be purely stateless, because the application
        state should not depend on whether or not the render function is called.

        To introduce state or effects in the render function, use
        :func:`use_state` or :func:`use_effect`.

        Args:
            None
        Returns:
            An Element object.
        """
        raise NotImplementedError


P = tp.ParamSpec("P")
selfT = tp.TypeVar("selfT", bound=Element)


def not_ignored(arg: tuple[str, tp.Any]) -> bool:
    return arg[0][0] != "_"


def component(f: Callable[tp.Concatenate[selfT, P], None]) -> Callable[P, Element]:
    """
    Decorator which turns a render function of **props** into an :class:`Element`.

    The first argument of the render function must be :code:`self`, for
    internal technical reasons.

    Props
    -----

    The **props** are the arguments passed to the :func:`@component<component>` function.

    The :func:`@component<component>` will be re-rendered when some of its **props** are not
    :code:`__eq__` to the **props** from the last time the
    :func:`@component<component>` rendered.
    If the **props** are all :code:`__eq__`, the :func:`@component<component>`
    will not re-render.

    Arguments with a leading underscore :code:`_` will not count as **props**.
    They are normal function arguments, and changing their value will not
    cause the :func:`@component<component>` to re-render.


    Render
    ------

    The @component function must render exactly one :class:`Element`.
    In the @component function, declare a tree of :class:`Element` with a
    single root.

    .. code-block:: python
        :caption: a tree with a single root

        @component
        def MySimpleComp(self, prop1, prop2, prop3):
            with VBoxView():
                Label(text=prop1)
                Label(text=prop2)
                Label(text=prop3)

    State
    -----

    The :func:`@component<component>` function is a stateless function from **props**
    to an :class:`Element`.
    To introduce **state** into a :func:`@component<component>`, use :doc:`Hooks <../hooks>`.

    Composition
    -----------

    An :func:`@component<component>`’s children can be passed to it as **props**. This allows a
    :func:`@component<component>` to act as a parent container for other :class:`Element` s,
    and to render them in a specific layout.

    There are two features to accomplish this.

    1. The special :code:`children` **prop** is a tuple of :class:`Element` s.
       The special :code:`children` **prop** must
       be declared as a **keyword argument** with a default empty tuple,
       like this :code:`children:tuple[Element, ...]=()`.

       Do not explicitly pass the :code:`children` **prop** when calling
       the :func:`@component<component>`. The children will be passed implicitly.
    2. The :func:`child_place` function is used to place the :code:`children`
       in the parent :func:`@component<component>`’s render function.

    With these two features, you can declare how the parent
    container :func:`@component<component>` will render its children.

    .. code-block:: python
        :caption: Example ContainerComponent with children props

        @component
        def ContainerComponent(self:Element, children:tuple[Element, ...]=()):
            with VBoxView():
                for child in children:
                    with VBoxView():
                        child_place(child)

    .. code-block:: python
        :caption: Example ContainerComponent usage

        with ContainerComponent():
            Label(text="First Child")
            Label(text="Second Child")
            Label(text="Third Child")

    Args:
        f:
            The render function to wrap.
            Its first argument must be :code:`self`.
            Subsequent arguments are **props**.

    """
    varnames = f.__code__.co_varnames[1:]
    signature = inspect.signature(f).parameters
    defaults = {k: v.default for k, v in signature.items() if v.default is not inspect.Parameter.empty and k[0] != "_"}

    class ComponentElement(Element):
        _edifice_original = f

        @functools.wraps(f)
        def __init__(self, *args: P.args, **kwargs: P.kwargs):
            super().__init__()
            name_to_val = defaults.copy()
            name_to_val.update(filter(not_ignored, zip(varnames, args, strict=False)))
            name_to_val.update((k, v) for (k, v) in kwargs.items() if k[0] != "_")
            name_to_val["children"] = name_to_val.get("children") or ()
            self._register_props(name_to_val)

        def _render_element(self):
            props: dict[str, tp.Any] = self.props._d
            params = props.copy()

            if "children" not in varnames:
                del params["children"]

            # We cannot type this because PropsDict forgets the types
            # call the render function
            f(self, **params)  # type: ignore[reportGeneralTypeIssues]

        def __repr__(self):
            return f.__name__

    ComponentElement.__name__ = f.__name__
    return tp.cast(Callable[P, Element], ComponentElement)


@component
def Container(self):
    pass


ContextMenuType = tp.Mapping[str, tp.Union[None, tp.Callable[[], tp.Any], "ContextMenuType"]]


def _create_qmenu(menu: ContextMenuType, parent, title: str | None = None):
    widget = QtWidgets.QMenu(parent)
    if title is not None:
        widget.setTitle(title)

    for key, value in menu.items():
        if isinstance(value, dict):
            sub_menu = _create_qmenu(value, widget, key)
            widget.addMenu(sub_menu)
        elif value is None:
            widget.addSeparator()
        else:
            widget.addAction(key, value)
    return widget


_CURSORS = {
    "default": QtCore.Qt.CursorShape.ArrowCursor,
    "arrow": QtCore.Qt.CursorShape.ArrowCursor,
    "pointer": QtCore.Qt.CursorShape.PointingHandCursor,
    "grab": QtCore.Qt.CursorShape.OpenHandCursor,
    "grabbing": QtCore.Qt.CursorShape.ClosedHandCursor,
    "text": QtCore.Qt.CursorShape.IBeamCursor,
    "crosshair": QtCore.Qt.CursorShape.CrossCursor,
    "move": QtCore.Qt.CursorShape.SizeAllCursor,
    "wait": QtCore.Qt.CursorShape.WaitCursor,
    "ew-resize": QtCore.Qt.CursorShape.SizeHorCursor,
    "ns-resize": QtCore.Qt.CursorShape.SizeVerCursor,
    "nesw-resize": QtCore.Qt.CursorShape.SizeBDiagCursor,
    "nwse-resize": QtCore.Qt.CursorShape.SizeFDiagCursor,
    "not-allowed": QtCore.Qt.CursorShape.ForbiddenCursor,
    "forbidden": QtCore.Qt.CursorShape.ForbiddenCursor,
}


def _css_to_number(a):
    if not isinstance(a, str):
        return a
    if a.endswith("px"):
        return float(a[:-2])
    return float(a)


class QtWidgetElement(Element, tp.Generic[_T_widget]):
    """Base Qt Widget.

    All elements with an underlying
    `QWidget <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html>`_
    inherit from this element.

    The props add basic functionality such as styling and event handlers.


    Args:
        style: Style dictionary. See :doc:`../../styling` for details.
        tool_tip:
            The tool tip displayed when hovering over the widget.
        cursor:
            The shape of the cursor when mousing over this widget. Must be one of:
            :code:`"default"`, :code:`"arrow"`, :code:`"pointer"`, :code:`"grab"`, :code:`"grabbing"`,
            :code:`"text"`, :code:`"crosshair"`, :code:`"move"`, :code:`"wait"`, :code:`"ew-resize"`,
            :code:`"ns-resize"`, :code:`"nesw-resize"`, :code:`"nwse-resize"`,
            :code:`"not-allowed"`, :code:`"forbidden"`
        context_menu:
            The context menu to display when the user right clicks on the widget.
            Expressed as a dict mapping the name of the context menu entry to either a function
            (which will be called when this entry is clicked) or to another sub context menu.
            For example, :code:`{"Copy": copy_fun, "Share": {"Twitter": twitter_share_fun, "Facebook": facebook_share_fun}}`
        css_class:
            A string or a list of strings, which will be stored in the :code:`css_class` property of the Qt Widget.
            This can be used in an application stylesheet, like:

                QLabel[css_class="heading"] { font-size: 18px; }

        size_policy:
            Horizontal and vertical resizing policy, of type `QSizePolicy <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSizePolicy.html>`_
        focus_policy:
            The various policies a widget can have with respect to acquiring keyboard focus, of type
            `FocusPolicy <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.Qt.FocusPolicy>`_.

            See also `QWidget.focusPolicy <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.QWidget.focusPolicy>`_.
        _focus_open:
            Whether the Element should be focused when this Element is first rendered.

            This argument is not a **prop** and will only focus the Element
            one time on the first render.
        enabled:
            Whether the widget is
            `enabled <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.QWidget.enabled>`_.
            If not, the widget will be grayed out and not respond to user input.
        on_click:
            Callback for click events (mouse pressed and released). Takes a
            `QMouseEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QMouseEvent.html>`_
            as argument.
        on_key_down:
            Callback for key down events (key pressed). Takes a
            `QKeyEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QKeyEvent.html>`_
            as argument.
            The :code:`key()` method of :code:`QKeyEvent` returns the
            `Qt.Key <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.Qt.Key>`_
            pressed.
            The :code:`text()` method returns the unicode of the key press, taking modifier keys (e.g. Shift)
            into account.
        on_key_up:
            Callback for key up events (key released). Takes a
            `QKeyEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QKeyEvent.html>`_
            as argument.
        on_mouse_down:
            Callback for mouse down events (mouse pressed). Takes a
            `QMouseEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QMouseEvent.html>`_
            as argument.
        on_mouse_up:
            Callback for mouse up events (mouse released). Takes a
            `QMouseEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QMouseEvent.html>`_
            as argument.
        on_mouse_enter:
            Callback for mouse enter events (triggered once every time mouse enters widget).
            Takes a
            `QMouseEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QMouseEvent.html>`_
            as argument.
        on_mouse_leave:
            Callback for mouse leave events (triggered once every time mouse leaves widget).
            Takes a
            `QMouseEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QMouseEvent.html>`_
            as argument.
        on_mouse_move:
            Callback for mouse move events (triggered every time mouse moves within widget).
            Takes a
            `QMouseEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QMouseEvent.html>`_
            as argument.
        on_mouse_wheel:
            Callback for mouse wheel events. Takes a
            `QWheelEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QWheelEvent.html>`_
            as argument.
        on_drop:
            Handle drop events.

            See `Dropping <https://doc.qt.io/qtforpython-6/overviews/dnd.html#dropping>`_.

            The handler function will be passed one of

            * `QDragEnterEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QDragEnterEvent.html>`_
              when the proposed drop enters the widget.
            * `QDragMoveEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QDragMoveEvent.html>`_
              when the proposed drop moves over the widget.
            * `QDragLeaveEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QDragLeaveEvent.html>`_
              when the proposed drop leaves the widget.
            * `QDropEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QDropEvent.html>`_
              when the drop happens.

            The handler function should handle all cases. Example::

                dropped_files, dropped_files_set = use_state(cast(list[str], []))
                proposed_files, proposed_files_set = use_state(cast(list[str], []))

                def handle_on_drop(event: QDragEnterEvent | QDragMoveEvent | QDragLeaveEvent | QDropEvent):
                    event.accept()
                    match event:
                        case QDragEnterEvent():
                            # Handle proposed drop enter
                            if event.mimeData().hasUrls():
                                event.acceptProposedAction()
                                proposed_files_set([url.toLocalFile()) for url in event.mimeData().urls()])
                        case QDragMoveEvent():
                            # Handle proposed drop move
                            if event.mimeData().hasUrls():
                                event.acceptProposedAction()
                        case QDragLeaveEvent():
                            # Handle proposed drop leave
                            proposed_files_set([])
                        case QDropEvent():
                            # Handle finalized drop
                            if event.mimeData().hasUrls():
                                dropped_files_set(proposed_files)
                                proposed_files_set([])

            Note that the handler function cannot not be a coroutine.
        on_resize:
            Callback for `resize events <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.QWidget.resizeEvent>`_.
            Takes a `QResizeEvent <https://doc.qt.io/qtforpython-6/PySide6/QtGui/QResizeEvent.html>`_
            as argument.

    """

    def __init__(
        self,
        style: tp.Mapping[str, tp.Any] | None = None,
        tool_tip: str | None = None,
        cursor: str | None = None,
        context_menu: ContextMenuType | None = None,
        css_class: tp.Any | None = None,
        size_policy: QtWidgets.QSizePolicy | None = None,
        focus_policy: QtCore.Qt.FocusPolicy | None = None,
        _focus_open: bool = False,
        enabled: bool | None = None,
        on_click: tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]] | None = None,
        on_key_down: tp.Callable[[QtGui.QKeyEvent], None | tp.Awaitable[None]] | None = None,
        on_key_up: tp.Callable[[QtGui.QKeyEvent], None | tp.Awaitable[None]] | None = None,
        on_mouse_down: tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]] | None = None,
        on_mouse_up: tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]] | None = None,
        on_mouse_enter: tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]] | None = None,
        on_mouse_leave: tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]] | None = None,
        on_mouse_move: tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]] | None = None,
        on_mouse_wheel: tp.Callable[[QtGui.QWheelEvent], None | tp.Awaitable[None]] | None = None,
        on_drop: tp.Callable[
            [QtGui.QDragEnterEvent | QtGui.QDragMoveEvent | QtGui.QDragLeaveEvent | QtGui.QDropEvent],
            None,
        ]
        | None = None,
        on_resize: tp.Callable[[QtGui.QResizeEvent], None | tp.Awaitable[None]] | None = None,
    ):
        super().__init__()
        self._register_props(
            {
                "style": style,
                "tool_tip": tool_tip,
                "cursor": cursor,
                "context_menu": context_menu,
                "css_class": css_class,
                "size_policy": size_policy,
                "focus_policy": focus_policy,
                "enabled": enabled,
                "on_click": on_click,
                "on_key_down": on_key_down,
                "on_key_up": on_key_up,
                "on_mouse_down": on_mouse_down,
                "on_mouse_up": on_mouse_up,
                "on_mouse_enter": on_mouse_enter,
                "on_mouse_leave": on_mouse_leave,
                "on_mouse_move": on_mouse_move,
                "on_mouse_wheel": on_mouse_wheel,
                "on_drop": on_drop,
                "on_resize": on_resize,
            },
        )
        self._height = 0
        self._width = 0
        self._top = 0
        self._left = 0
        self._size_from_font = None  # TODO _size_from_font is unused
        self._on_click = None
        self._on_key_down = None
        self._default_on_key_down = None
        self._on_key_up = None
        self._default_on_key_up = None
        self._on_mouse_enter = None
        self._on_mouse_leave = None
        self._on_mouse_down = None
        self._on_mouse_up = None
        self._on_mouse_move = None
        self._on_mouse_wheel = None
        self._on_drop: (
            tp.Callable[[QtGui.QDragEnterEvent | QtGui.QDragMoveEvent | QtGui.QDragLeaveEvent | QtGui.QDropEvent], None]
            | None
        ) = None
        self._on_resize: tp.Callable[[QtGui.QResizeEvent], None] | None = None
        self._default_mouse_press_event = None
        self._default_mouse_release_event = None
        self._default_mouse_move_event = None
        self._default_mouse_enter_event = None
        self._default_mouse_leave_event = None
        self._default_mouse_wheel_event = None
        self._default_drag_enter_event = None
        self._default_drag_move_event = None
        self._default_drag_leave_event = None
        self._default_drop_event = None
        self._default_resize_event = None
        self._default_size_policy : QtWidgets.QSizePolicy | None = None

        self._context_menu = None
        self._context_menu_connected = False
        if cursor is not None:
            if cursor not in _CURSORS:
                raise ValueError(f"Unrecognized cursor {cursor}. Cursor must be one of {list(_CURSORS.keys())}")

        self.underlying: _T_widget | None = None
        """
        The underlying QWidget, which may not exist if this Element has not rendered.
        """
        self._mouse_pressed = False
        self._focus_open_needed = _focus_open

    def _set_size(self, width, height, size_from_font=None):
        self._height = height
        self._width = width
        self._size_from_font = size_from_font

    def _get_width(self, children):
        # TODO this function is unreferenced
        if self._width:
            return self._width
        layout = self.props._get("layout", "none")
        if layout == "row":
            return sum(max(0, child.component._width + child.component._left) for child in children)
        try:
            return max(max(0, child.component._width + child.component._left) for child in children)
        except ValueError:
            return 0

    def _get_height(self, children):
        # TODO this function is unreferenced
        if self._height:
            return self._height
        layout = self.props._get("layout", "none")
        if layout == "column":
            return sum(max(0, child.component._height + child.component._top) for child in children)
        try:
            return max(max(0, child.component._height + child.component._top) for child in children)
        except ValueError:
            return 0

    def _mouse_press(self, event: QtGui.QMouseEvent) -> None:
        if self._on_mouse_down is not None:
            self._on_mouse_down(event)
        if self._default_mouse_press_event is not None:
            self._default_mouse_press_event(event)

    def _mouse_release(self, underlying: QtWidgets.QWidget):
        def handler(event: QtGui.QMouseEvent):
            event_pos = event.pos()
            if self._on_mouse_up is not None:
                self._on_mouse_up(event)
            if self._default_mouse_release_event is not None:
                self._default_mouse_release_event(event)
            geometry = underlying.geometry()

            if 0 <= event_pos.x() <= geometry.width() and 0 <= event_pos.y() <= geometry.height():
                self._mouse_clicked(event)
            self._mouse_pressed = False

        return handler

    def _mouse_clicked(self, ev):
        if self._on_click:
            self._on_click(ev)

    def _set_on_click(self, underlying: QtWidgets.QWidget, on_click):
        # FIXME: Should this not use `underlying`?
        if on_click is not None:
            self._on_click = _ensure_future(on_click)
        else:
            self._on_click = None
        if self._default_mouse_press_event is None:
            self._default_mouse_press_event = underlying.mousePressEvent
        underlying.mousePressEvent = self._mouse_press
        if self._default_mouse_release_event is None:
            self._default_mouse_release_event = underlying.mouseReleaseEvent
        underlying.mouseReleaseEvent = self._mouse_release(underlying)

    def _handle_mouse_wheel(self, event: QtGui.QWheelEvent):
        if self._on_mouse_wheel is not None:
            self._on_mouse_wheel(event)
        else:
            type(self.underlying).wheelEvent(self.underlying, event) # type: ignore  # noqa: PGH003

    def _set_mouse_wheel(self, underlying: QtWidgets.QWidget, on_mouse_wheel):
        # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.QWidget.wheelEvent
        # “If you reimplement this handler, it is very important that
        # you ignore() the event if you do not handle it, so that the widget’s
        # parent can interpret it.”
        if self._default_mouse_wheel_event is None:
            self._default_mouse_wheel_event = underlying.wheelEvent
            underlying.wheelEvent = self._handle_mouse_wheel
        if on_mouse_wheel is not None:
            self._on_mouse_wheel = _ensure_future(on_mouse_wheel)
        else:
            self._on_mouse_wheel = None

    def _handle_key_down(self, event: QtGui.QKeyEvent):
        if self._on_key_down is not None:
            _ensure_future(self._on_key_down)(event)
        if self._default_on_key_down is not None:
            self._default_on_key_down(event)

    def _set_on_key_down(self, underlying: QtWidgets.QWidget, on_key_down):
        # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.QWidget.keyPressEvent
        # “If you reimplement this handler, it is very important that you call
        # the base class implementation if you do not act upon the key.”
        if self._default_on_key_down is None:
            # one-time setup
            self._default_on_key_down = underlying.keyPressEvent
            underlying.keyPressEvent = self._handle_key_down
        self._on_key_down = on_key_down

    def _handle_key_up(self, event: QtGui.QKeyEvent):
        if self._on_key_up is not None:
            _ensure_future(self._on_key_up)(event)
        if self._default_on_key_up is not None:
            self._default_on_key_up(event)

    def _set_on_key_up(self, underlying: QtWidgets.QWidget, on_key_up):
        if self._default_on_key_up is None:
            # one-time setup
            self._default_on_key_up = underlying.keyReleaseEvent
            underlying.keyReleaseEvent = self._handle_key_up
        self._on_key_up = on_key_up

    def _set_on_mouse_down(self, underlying: QtWidgets.QWidget, on_mouse_down):
        if on_mouse_down is not None:
            self._on_mouse_down = _ensure_future(on_mouse_down)
        else:
            self._on_mouse_down = None
        if self._default_mouse_press_event is None:
            self._default_mouse_press_event = underlying.mousePressEvent
        underlying.mousePressEvent = self._mouse_press

    def _set_on_mouse_up(self, underlying: QtWidgets.QWidget, on_mouse_up):
        if on_mouse_up is not None:
            self._on_mouse_up = _ensure_future(on_mouse_up)
        else:
            self._on_mouse_up = None
        if self._default_mouse_release_event is None:
            self._default_mouse_release_event = underlying.mouseReleaseEvent
        underlying.mouseReleaseEvent = self._mouse_release(underlying)

    def _set_on_mouse_enter(self, underlying: QtWidgets.QWidget, on_mouse_enter):
        if self._default_mouse_enter_event is None:
            self._default_mouse_enter_event = underlying.enterEvent
        if on_mouse_enter is not None:
            self._on_mouse_enter = _ensure_future(on_mouse_enter)
            underlying.enterEvent = self._on_mouse_enter
        else:
            self._on_mouse_enter = None
            underlying.enterEvent = self._default_mouse_enter_event

    def _set_on_mouse_leave(self, underlying: QtWidgets.QWidget, on_mouse_leave):
        if self._default_mouse_leave_event is None:
            self._default_mouse_leave_event = underlying.leaveEvent
        if on_mouse_leave is not None:
            self._on_mouse_leave = _ensure_future(on_mouse_leave)
            underlying.leaveEvent = self._on_mouse_leave
        else:
            underlying.leaveEvent = self._default_mouse_leave_event
            self._on_mouse_leave = None

    def _set_on_mouse_move(self, underlying: QtWidgets.QWidget, on_mouse_move):
        if self._default_mouse_move_event is None:
            self._default_mouse_move_event = underlying.mouseMoveEvent
        if on_mouse_move is not None:
            self._on_mouse_move = _ensure_future(on_mouse_move)
            underlying.mouseMoveEvent = self._on_mouse_move
            underlying.setMouseTracking(True)
        else:
            self._on_mouse_move = None
            underlying.mouseMoveEvent = self._default_mouse_move_event

    def _set_on_drop(
        self,
        underlying: QtWidgets.QWidget,
        on_drop: tp.Callable[
            [QtGui.QDragEnterEvent | QtGui.QDragMoveEvent | QtGui.QDragLeaveEvent | QtGui.QDropEvent],
            None,
        ]
        | None,
    ):
        # Store the QWidget's default virtual event handler methods
        if self._default_drag_enter_event is None:
            self._default_drag_enter_event = underlying.dragEnterEvent
        if self._default_drag_move_event is None:
            self._default_drag_move_event = underlying.dragMoveEvent
        if self._default_drag_leave_event is None:
            self._default_drag_leave_event = underlying.dragLeaveEvent
        if self._default_drop_event is None:
            self._default_drop_event = underlying.dropEvent

        if on_drop is not None:
            self._on_drop = on_drop
            underlying.setAcceptDrops(True)
            underlying.dragEnterEvent = self._on_drop  # type: ignore  # noqa: PGH003
            underlying.dragMoveEvent = self._on_drop  # type: ignore  # noqa: PGH003
            underlying.dragLeaveEvent = self._on_drop  # type: ignore  # noqa: PGH003
            underlying.dropEvent = self._on_drop  # type: ignore  # noqa: PGH003
        else:
            self._on_drop = None
            underlying.setAcceptDrops(False)

    def _resizeEvent(self, event: QtGui.QResizeEvent):
        if self._on_resize is not None:
            self._on_resize(event)
            # In the case of QScrollArea (and possibly other widgets), the resizeEvent is used by
            # the QScrollArea widget to resize its children. If we don't call the default
            # method then that functionality is lost.
            # I've got no reference that says we can call a method like this, but it works.
            type(self.underlying).resizeEvent(self.underlying, event)  # type: ignore  # noqa: PGH003

    def _set_on_resize(self, underlying: QtWidgets.QWidget, on_resize: tp.Callable[[QtGui.QResizeEvent], None] | None):
        # Store the QWidget's default virtual event handler method one time
        if self._default_resize_event is None:
            self._default_resize_event = underlying.resizeEvent

        if on_resize is not None:
            self._on_resize = _ensure_future(on_resize)
            underlying.resizeEvent = self._resizeEvent
        else:
            self._on_resize = None
            underlying.resizeEvent = self._default_resize_event

    def _gen_styling_commands(
        self,
        style: dict[str, tp.Any],
        underlying: QtWidgets.QWidget,
        underlying_layout: QtWidgets.QLayout | None = None,
    ):
        # shallow copy the style because we will be modifying it
        cpstyle = copy(style)

        commands: list[CommandType] = []

        if underlying_layout is not None:
            # QLayouts don't observe the Box Model.
            # https://doc.qt.io/qtforpython-6/overviews/stylesheet-customizing.html#the-box-model
            #
            # The "border" style will work.
            #
            # The "margin" style will not work.
            #
            # The "padding" style will not work, but we can fake it by
            # using QLayout.setContentsMargins().
            # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLayout.html#PySide6.QtWidgets.QLayout.setContentsMargins
            set_padding = False
            new_padding = [0, 0, 0, 0]
            if "padding" in cpstyle:
                new_padding = [int(_css_to_number(cpstyle["padding"]))] * 4
                cpstyle.pop("padding")
                set_padding = True
            if "padding-left" in cpstyle:
                new_padding[0] = int(_css_to_number(cpstyle["padding-left"]))
                cpstyle.pop("padding-left")
                set_padding = True
            if "padding-right" in cpstyle:
                new_padding[2] = int(_css_to_number(cpstyle["padding-right"]))
                cpstyle.pop("padding-right")
                set_padding = True
            if "padding-top" in cpstyle:
                new_padding[1] = int(_css_to_number(cpstyle["padding-top"]))
                cpstyle.pop("padding-top")
                set_padding = True
            if "padding-bottom" in cpstyle:
                new_padding[3] = int(_css_to_number(cpstyle["padding-bottom"]))
                cpstyle.pop("padding-bottom")
                set_padding = True

            if "align" in cpstyle:
                # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLayout.html#PySide6.QtWidgets.QLayout.setAlignment
                cpstyle_align = cpstyle["align"]
                if type(cpstyle_align) is str:
                    if cpstyle_align == "left":
                        set_align = QtCore.Qt.AlignmentFlag.AlignLeft
                    elif cpstyle_align == "center":
                        set_align = QtCore.Qt.AlignmentFlag.AlignCenter
                    elif cpstyle_align == "right":
                        set_align = QtCore.Qt.AlignmentFlag.AlignRight
                    elif cpstyle_align == "justify":
                        set_align = QtCore.Qt.AlignmentFlag.AlignJustify
                    elif cpstyle_align == "top":
                        set_align = QtCore.Qt.AlignmentFlag.AlignTop
                    elif cpstyle_align == "bottom":
                        set_align = QtCore.Qt.AlignmentFlag.AlignBottom
                    else:
                        raise ValueError(f"Unknown style align: {cpstyle_align}")
                elif type(cpstyle_align) is QtCore.Qt.AlignmentFlag:
                    set_align = cpstyle_align
                else:
                    raise ValueError(f"Style align wrong type: {cpstyle_align}")
                cpstyle.pop("align")
                commands.append(CommandType(underlying_layout.setAlignment, set_align))

            if set_padding:
                commands.append(
                    CommandType(
                        underlying_layout.setContentsMargins,
                        new_padding[0],
                        new_padding[1],
                        new_padding[2],
                        new_padding[3],
                    ),
                )

        if "align" in cpstyle:
            if hasattr(type(underlying), "setAlignment"):
            # QLabels and other things that have a setAlignment method
            # https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLabel.html#PySide6.QtWidgets.QLabel.setAlignment
                cpstyle_align = cpstyle["align"]
                if type(cpstyle_align) is str:
                    if cpstyle_align == "left":
                        set_align = QtCore.Qt.AlignmentFlag.AlignLeft
                    elif cpstyle_align == "center":
                        set_align = QtCore.Qt.AlignmentFlag.AlignCenter
                    elif cpstyle_align == "right":
                        set_align = QtCore.Qt.AlignmentFlag.AlignRight
                    elif cpstyle_align == "justify":
                        set_align = QtCore.Qt.AlignmentFlag.AlignJustify
                    elif cpstyle_align == "top":
                        set_align = QtCore.Qt.AlignmentFlag.AlignTop
                    elif cpstyle_align == "bottom":
                        set_align = QtCore.Qt.AlignmentFlag.AlignBottom
                    else:
                        raise ValueError(f"Unknown style align: {cpstyle_align}")
                elif type(cpstyle_align) is QtCore.Qt.AlignmentFlag:
                    set_align = cpstyle_align
                else:
                    raise ValueError(f"Style align wrong type: {cpstyle_align}")
                cpstyle.pop("align")
                commands.append(CommandType(underlying.setAlignment, set_align)) # type: ignore  # noqa: PGH003
            else:
                # Set the align property for the style sheet
                # TODO This case is probably unreachable?
                if cpstyle["align"] == "left":
                    set_align = "AlignLeft"
                elif cpstyle["align"] == "center":
                    set_align = "AlignCenter"
                elif cpstyle["align"] == "right":
                    set_align = "AlignRight"
                elif cpstyle["align"] == "justify":
                    set_align = "AlignJustify"
                elif cpstyle["align"] == "top":
                    set_align = "AlignTop"
                elif cpstyle["align"] == "bottom":
                    set_align = "AlignBottom"
                else:
                    raise ValueError(f"Unknown style align: {cpstyle['align']}")
                cpstyle.pop("align")
                cpstyle["qproperty-alignment"] = set_align

        if "font-size" in cpstyle:
            font_size = _css_to_number(cpstyle["font-size"])
            if self._size_from_font is not None:
                size = self._size_from_font(font_size)
                self._width = size[0]
                self._height = size[1]
            if not isinstance(cpstyle["font-size"], str):
                cpstyle["font-size"] = "%dpx" % font_size
        if "width" in cpstyle:
            if "min-width" not in cpstyle:
                cpstyle["min-width"] = cpstyle["width"]
            if "max-width" not in cpstyle:
                cpstyle["max-width"] = cpstyle["width"]
        # else:
        #     if "min-width" not in cpstyle:
        #         cpstyle["min-width"] = self._get_width(children)

        if "height" in cpstyle:
            if "min-height" not in cpstyle:
                cpstyle["min-height"] = cpstyle["height"]
            if "max-height" not in cpstyle:
                cpstyle["max-height"] = cpstyle["height"]
        # else:
        #     if "min-height" not in cpstyle:
        #         cpstyle["min-height"] = self._get_height(children)

        set_move = False
        move_coords = [0, 0]
        if "top" in cpstyle:
            set_move = True
            move_coords[1] = int(_css_to_number(cpstyle["top"]))
            self._top = move_coords[1]
        if "left" in cpstyle:
            set_move = True
            move_coords[0] = int(_css_to_number(cpstyle["left"]))
            self._left = move_coords[0]

        if set_move:
            commands.append(CommandType(underlying.move, move_coords[0], move_coords[1]))

        # CSS style selection is matched by setting underlying.setObjectName(str(id(self)))
        # In Element initialization.
        # https://doc.qt.io/qtforpython-6/PySide6/QtCore/QObject.html#PySide6.QtCore.QObject.setObjectName
        css_string = "QWidget#" + str(id(self)) + _dict_to_style(cpstyle)
        commands.append(CommandType(underlying.setStyleSheet, css_string))
        return commands

    def _set_context_menu(self, underlying: QtWidgets.QWidget):
        if self._context_menu_connected:
            underlying.customContextMenuRequested.disconnect()
        self._context_menu_connected = True

        def _show_context_menu(pos):
            if self.props.context_menu is not None:
                menu = _create_qmenu(self.props.context_menu, underlying)
                pos = underlying.mapToGlobal(pos)
                menu.move(pos)
                menu.show()

        underlying.customContextMenuRequested.connect(_show_context_menu)

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops: PropsDict,
    ) -> list[CommandType]:
        raise NotImplementedError

    def _qt_update_commands_super(
        self,
        widget_trees: dict[Element, _WidgetTree],
        # We must pass all of the widget_trees because some elements
        # like TableGridView need to know the children of the children.
        newprops: PropsDict,
        underlying: QtWidgets.QWidget,
        underlying_layout: QtWidgets.QLayout | None = None,
    ) -> list[CommandType]:
        commands: list[CommandType] = []
        for prop in newprops:
            if prop == "style":
                style = newprops.style or {}
                commands.extend(self._gen_styling_commands(style, underlying, underlying_layout))
            elif prop == "size_policy":
                if newprops.size_policy is not None:
                    if self._default_size_policy is None:
                        self._default_size_policy = underlying.sizePolicy()
                    commands.append(CommandType(underlying.setSizePolicy, newprops.size_policy))
                elif self._default_size_policy is not None:
                    commands.append(CommandType(underlying.setSizePolicy, self._default_size_policy))
            elif prop == "focus_policy":
                if newprops.focus_policy is not None:
                    commands.append(CommandType(underlying.setFocusPolicy, newprops.focus_policy))
            elif prop == "enabled":
                if newprops.enabled is not None:
                    commands.append(CommandType(underlying.setEnabled, newprops.enabled))
            elif prop == "on_click":
                commands.append(CommandType(self._set_on_click, underlying, newprops.on_click))
                if newprops.on_click is not None and self.props.cursor is not None:
                    commands.append(CommandType(underlying.setCursor, QtCore.Qt.CursorShape.PointingHandCursor))
            elif prop == "on_key_down":
                commands.append(CommandType(self._set_on_key_down, underlying, newprops.on_key_down))
            elif prop == "on_key_up":
                commands.append(CommandType(self._set_on_key_up, underlying, newprops.on_key_up))
            elif prop == "on_mouse_down":
                commands.append(CommandType(self._set_on_mouse_down, underlying, newprops.on_mouse_down))
            elif prop == "on_mouse_up":
                commands.append(CommandType(self._set_on_mouse_up, underlying, newprops.on_mouse_up))
            elif prop == "on_mouse_enter":
                commands.append(CommandType(self._set_on_mouse_enter, underlying, newprops.on_mouse_enter))
            elif prop == "on_mouse_leave":
                commands.append(CommandType(self._set_on_mouse_leave, underlying, newprops.on_mouse_leave))
            elif prop == "on_mouse_move":
                commands.append(CommandType(self._set_on_mouse_move, underlying, newprops.on_mouse_move))
            elif prop == "on_mouse_wheel":
                commands.append(CommandType(self._set_mouse_wheel, underlying, newprops.on_mouse_wheel))
            elif prop == "on_drop":
                commands.append(CommandType(self._set_on_drop, underlying, newprops.on_drop))
            elif prop == "on_resize":
                commands.append(CommandType(self._set_on_resize, underlying, newprops.on_resize))
            elif prop == "tool_tip":
                if newprops.tool_tip is not None:
                    commands.append(CommandType(underlying.setToolTip, newprops.tool_tip))
            elif prop == "css_class":
                css_class = newprops.css_class
                if css_class is None:
                    css_class = []
                commands.append(CommandType(underlying.setProperty, "css_class", css_class))
                commands.extend(
                    [
                        CommandType(underlying.style().unpolish, underlying),
                        CommandType(underlying.style().polish, underlying),
                    ],
                )
            elif prop == "cursor":
                cursor = self.props.cursor or ("default" if self.props.on_click is None else "pointer")
                commands.append(CommandType(underlying.setCursor, _CURSORS[cursor]))
            elif prop == "context_menu":
                if self._context_menu_connected:
                    underlying.customContextMenuRequested.disconnect()
                if self.props.context_menu is not None:
                    commands.append(
                        CommandType(underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.CustomContextMenu),
                    )
                    commands.append(CommandType(self._set_context_menu, underlying))
                else:
                    commands.append(
                        CommandType(underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu),
                    )
        if self._focus_open_needed:
            # Only do this on first render
            self._focus_open_needed = False
            # call_soon() is the only way to get this to work.
            # It doesn't work if you setFocus in the commands.
            # Hopefully this does not cause a race condition where we setFocus on a destroyed QWidget.
            asyncio.get_event_loop().call_soon(underlying.setFocus, QtCore.Qt.FocusReason.OtherFocusReason)

        return commands


qtT = tp.TypeVar("qtT", bound=QtWidgetElement)


def qt_component(
    f: Callable[
        tp.Concatenate[qtT, list[str], Callable[[_T_widget, QtWidgets.QLayout | None], list[CommandType]], P],
        list[CommandType],
    ],
) -> Callable[P, QtWidgetElement[_T_widget]]:
    varnames = f.__code__.co_varnames[3:]
    signature = inspect.signature(f).parameters
    defaults = {k: v.default for k, v in signature.items() if v.default is not inspect.Parameter.empty and k[0] != "_"}

    class ComponentElement(QtWidgetElement):
        _edifice_original = f

        @functools.wraps(f)
        def __init__(self, *args: P.args, **kwargs: P.kwargs):
            super().__init__()
            name_to_val = defaults.copy()
            name_to_val.update(filter(not_ignored, zip(varnames, args, strict=False)))
            # kwards prefixed with _ are excluded from props
            name_to_val.update((k, v) for (k, v) in kwargs.items() if k[0] != "_")
            self._register_props(name_to_val)

        def _qt_update_commands(
            self,
            widget_trees: dict[Element, _WidgetTree],
            newprops: PropsDict,
        ) -> list[CommandType]:
            props: dict[str, tp.Any] = self.props._d
            params = props.copy()
            newkeys = list(newprops._d.keys())

            def super_commands(underlying: QtWidgets.QWidget, layout: QtWidgets.QLayout | None):
                return super(ComponentElement, self)._qt_update_commands_super(
                    widget_trees,
                    newprops,
                    underlying,
                    layout,
                )

            me = tp.cast(qtT, self)
            return f(me, newkeys, super_commands, **params)

        def __repr__(self):
            return f.__name__

    ComponentElement.__name__ = f.__name__
    return tp.cast(Callable[P, QtWidgetElement], ComponentElement)


class _WidgetTree:
    """
    A QtWidgetElement and its QtWidgetElement children.
    """

    __slots__ = ("component", "children")

    def __init__(self, component: QtWidgetElement, children: list[QtWidgetElement]):
        self.component: QtWidgetElement = component
        self.children: list[QtWidgetElement] = children


def _get_widget_children(widget_trees: dict[Element, _WidgetTree], element: QtWidgetElement) -> list[QtWidgetElement]:
    if (w := widget_trees.get(element, None)) is not None:
        return w.children
    return []


def _dereference_tree(widget_trees: dict[Element, _WidgetTree], widget_tree: _WidgetTree, address: list[int]):
    """
    This method used only for testing
    """
    for index in address:
        widget_tree = widget_trees[widget_tree.children[index]]
    return widget_tree


def print_tree(widget_trees: dict[Element, _WidgetTree], element: Element, indent=0):
    t = widget_trees[element]
    tags = t.component._tags()
    if t.children:
        print("  " * indent + tags[0])  # noqa: T201
        for child in t.children:
            print_tree(widget_trees, child, indent=indent + 1)
        print("  " * indent + tags[1])  # noqa: T201
    else:
        print("  " * indent + tags[2])  # noqa: T201


class RenderResult:
    """Encapsulates the results of a render.

    Concretely, it stores information such as commands,
    which must be executed by the caller.
    """

    def __init__(
        self,
        commands: list[CommandType],
    ):
        self.commands: list[CommandType] = commands


@dataclass
class _HookState:
    state: tp.Any
    updaters: list[tp.Callable[[tp.Any], tp.Any]]
    element: Element
    engine: RenderEngine

    # Stable setter function will always be the same function
    # returned by repeated calls to use_state. So it can be used
    # as a stable prop.
    def setter(self, updater):
        if self.element not in self.engine._hook_state:
            # Then the component has been deleted and unmounted.
            # This might happen if the setter is called during a
            # a use_async CancelledError handler.
            # In that case, we don't want to update the state.
            return
        self.updaters.append(updater)
        self.engine._hook_state_setted.add(self.element)
        assert self.engine._app is not None
        self.engine._app._defer_rerender(self.element)


@dataclass
class _HookEffect:
    setup: tp.Callable[[], tp.Callable[[], None] | None] | None
    cleanup: tp.Callable[[], None] | None
    """
    Cleanup function called on unmount and overwrite
    """
    dependencies: tp.Any


@dataclass
class _HookAsync:
    task: asyncio.Task[tp.Any] | None
    """
    The currently executing async effect task.
    """
    queue: list[tp.Callable[[], Coroutine[None, None, None]]]
    """
    The queue of waiting async effect tasks. Max length 1.
    """
    dependencies: tp.Any
    """
    The dependencies of use_async().
    """


def elements_match(a: Element, b: Element) -> bool:
    """
    Should return True if element b can be used to update element a
    by _update_old_component().
    """
    # Elements must be of the same __class__.
    # Elements must have the same __class__.__name__. This is to distinguish
    # between different @component Components. (Why does class __eq__ return
    # True if the class __name__ is different?)
    return (a.__class__ == b.__class__) and (a.__class__.__name__ == b.__class__.__name__) and (a._key == b._key)


class RenderEngine:
    """
    One RenderEngine instance persists across the life of the App.
    """

    __slots__ = (
        "_component_tree",
        "_widget_tree",
        "_root",
        "_app",
        "_hook_state",
        "_hook_state_setted",
        "_hook_effect",
        "_hook_async",
        "is_stopped",
    )

    def __init__(self, root: Element, app: AppProtocol | None = None):
        self._component_tree: dict[Element, list[Element]] = {}
        """
        The _component_tree maps an Element to its children.
        """
        self._widget_tree: dict[Element, _WidgetTree] = {}
        """
        Map of an Element to its rendered widget tree.

        TODO This should actually be a map of each QtWidgetElement to its rendered
        children, of type dict[QtWidgetElement, list[QtWidgetElement]].
        """
        self._root = root
        self._app: AppProtocol | None = app

        self._hook_state: defaultdict[Element, list[_HookState]] = defaultdict(list)
        """
        The per-element hooks for use_state().
        """
        self._hook_state_setted: set[Element] = set()
        """
        The set of elements which have had their use_state() setters called
        since the last render.
        """
        self._hook_effect: defaultdict[Element, list[_HookEffect]] = defaultdict(list)
        """
        The per-element hooks for use_effect().
        """
        self._hook_async: defaultdict[Element, list[_HookAsync]] = defaultdict(list)
        """
        The per-element hooks for use_async().
        """
        self.is_stopped: bool = False
        """
        Flag determining if the render engine has been stopped.
        """

    def is_hook_async_done(self, element: Element) -> bool:
        """
        True if all of the async hooks for an Element are done.
        """
        if element not in self._hook_async:
            return True
        hooks = self._hook_async[element]
        for hook in hooks:
            if hook.task is not None:
                if not hook.task.done():
                    return False
        return True

    def _delete_component(self, component: Element, recursive: bool):
        # Delete component from render trees
        sub_components = self._component_tree[component]
        if recursive:
            for sub_comp in sub_components:
                self._delete_component(sub_comp, recursive)
            # Node deletion

        # Clean up use_effect for the component
        if component in self._hook_effect:
            for hook in self._hook_effect[component]:
                if hook.cleanup is not None:
                    # None indicates that the setup effect failed,
                    # or that there is no cleanup function.
                    try:
                        hook.cleanup()
                    except Exception:  # noqa: S110, BLE001
                        pass
            del self._hook_effect[component]
        # Clean up use_async for the component
        if component in self._hook_async:
            for hook in self._hook_async[component]:
                hook.queue.clear()
                if hook.task is not None:
                    # If there are some running tasks, wait until they are
                    # done and then delete this HookAsync object.
                    def done_callback(_future_object):
                        if component in self._hook_async:
                            if self.is_hook_async_done(component):
                                del self._hook_async[component]

                    hook.task.add_done_callback(done_callback)
                    hook.task.cancel()
            if self.is_hook_async_done(component):
                # If there are no running tasks, then we can delete this
                # HookAsync object immediately.
                del self._hook_async[component]
        # Clean up use_state for the component
        if component in self._hook_state:
            del self._hook_state[component]
        self._hook_state_setted.discard(component)

        # Clean up component references
        # Do this after use_effect cleanup, so that the cleanup function
        # can still access the component References.
        assert component._edifice_internal_references is not None
        for ref in component._edifice_internal_references:
            ref._value = None
        del self._component_tree[component]
        del self._widget_tree[component]

    def _refresh_by_class(self, classes) -> None:
        # This refresh is done only for a hot reload. It refreshes all
        # elements which were defined in a module which was changed
        # on the filesystem.

        if self.is_stopped:
            return

        # Algorithm:
        # 1) Find all old components that's not a child of another component

        # components_to_replace is (old_component, new_component_class, parent component, new_component)
        components_to_replace = []
        # classes should be only ComponentElement, because only ComponentElement can change in user code.
        old_components = [cls for cls, _ in classes]

        def traverse(comp, parent):
            if comp.__class__ in old_components and parent is not None:  # We can't replace the unparented root
                new_component_class = next(new_cls for old_cls, new_cls in classes if old_cls == comp.__class__)
                if new_component_class is None:
                    raise ValueError(f"Error after updating code: cannot find class {comp.__class__}")
                components_to_replace.append([comp, new_component_class, parent, None])
                return
            sub_components = self._component_tree[comp]
            if isinstance(sub_components, list):
                for sub_comp in sub_components:
                    traverse(sub_comp, comp)
            else:
                traverse(sub_components, comp)

        traverse(self._root, None)
        # 2) For all such old components, construct a new component and merge in old component props
        for parts in components_to_replace:
            old_comp, new_comp_class, _, _ = parts
            parameters = list(inspect.signature(new_comp_class.__init__).parameters.items())

            try:
                kwargs = {
                    k: old_comp.props[k]
                    for k, v in parameters[1:]
                    if v.default is inspect.Parameter.empty and k[0] != "_" and k != "kwargs"
                }
            # We don't actually need all the kwargs, just enough
            # to construct new_comp_class.
            # The other kwargs will be set with _props.update.
            except KeyError as err:
                k = None
                for k, _ in parameters[1:]:
                    if k not in old_comp.props:
                        break
                raise ValueError(
                    f"Error while reloading {old_comp}: New class expects prop ({k}) not present in old class",
                ) from err
            parts[3] = new_comp_class(**kwargs)
            parts[3]._props.update(old_comp._props)
            parts[3]._key = old_comp._key

        # 3) Replace old component in the place in the tree where they first appear, with a reference to new component

        backup = {}
        for old_comp, _, parent_comp, new_comp in components_to_replace:
            parent_comp_children = list(parent_comp.children)
            backup[parent_comp] = copy(parent_comp.children)
            for i, comp in enumerate(parent_comp.children):
                if comp is old_comp:
                    parent_comp_children[i] = new_comp
                    # Move the hook states to the new component.
                    # We want to be careful that the hooks don't have
                    # any references to the old component, especially
                    # function closures. I think this code is okay.
                    #
                    # During the effect functions and the async coroutine, usually
                    # what happens is that some use_state setters are called,
                    # and those use_state setters would be closures on the
                    # state which was moved, not references to the old_comp.
                    #
                    # Because this is only during hot-reload, so only during
                    # development, it's not catastrophic if some references
                    # to old_comp are retained and cause bugs.
                    if old_comp in self._hook_state:
                        self._hook_state[new_comp] = self._hook_state[old_comp]
                        del self._hook_state[old_comp]
                    if old_comp in self._hook_effect:
                        self._hook_effect[new_comp] = self._hook_effect[old_comp]
                        del self._hook_effect[old_comp]
                    if old_comp in self._hook_async:
                        self._hook_async[new_comp] = self._hook_async[old_comp]
                        del self._hook_async[old_comp]
            parent_comp._props["children"] = tuple(parent_comp_children)

        # 5) call _render for all new component parents
        try:
            logger.info(
                "Rerendering parents of: %s",
                [new_comp_class.__name__ for _, new_comp_class, _, _ in components_to_replace],
            )
            logger.info("Rerendering: %s", [parent for _, _, parent, _ in components_to_replace])
            self._request_rerender([parent_comp for _, _, parent_comp, _ in components_to_replace])
        except Exception:
            # Restore components
            for parent_comp, backup_val in backup.items():
                parent_comp._props["children"] = backup_val
            raise

    def _update_old_component(
        self,
        component: Element,
        new_component: Element,
        render_context: _RenderContext,
    ) -> _WidgetTree:
        # new_component is a new rendering of old component, so update
        # old component to have props of new_component.
        # The new_component will be discarded.
        assert component._edifice_internal_references is not None
        assert new_component._edifice_internal_references is not None
        newprops = new_component.props
        # TODO are we leaking memory by holding onto the old references?
        component._edifice_internal_references.update(new_component._edifice_internal_references)
        # component needs re-rendering if
        #  1) props changed
        #  2) state changed
        #  3) it has any pending _hook_state updates
        #  4) it has any references
        if (
            component._should_update(newprops)
            or len(component._edifice_internal_references) > 0
            or component in self._hook_state_setted
        ):
            render_context.mark_props_change(component, newprops)
            rerendered_obj = self._render(component, render_context)
            render_context.mark_qt_rerender(rerendered_obj.component, True)
            return rerendered_obj

        render_context.mark_props_change(component, newprops)
        return self._widget_tree[component]

    def _recycle_children(self, component: QtWidgetElement, render_context: _RenderContext) -> list[Element]:
        # Children diffing and reconciliation
        #
        # Returns element children, which contains all the future children of the component:
        # a mixture of old components (if they can be updated) and new ones
        #
        # Returns children widget trees, cached or newly rendered.

        children_old_bykey: dict[str, Element] = {}
        children_new_bykey: dict[str, Element] = {}

        children_old_ = self._component_tree[component]

        widgettree = _WidgetTree(component, [])

        # We will mutate children_old to reuse and remove old elements if we can match them.
        # Ordering of children_old must be preserved for reverse deletion.
        children_old: list[Element] = children_old_[:]
        for child_old in children_old:
            if child_old._key is not None:
                children_old_bykey[child_old._key] = child_old

        # We will mutate children_new to replace them with old elements if we can match them.
        children_new: list[Element] = list(component.children)
        for child_new in children_new:
            if child_new._key is not None:
                if children_new_bykey.get(child_new._key, None) is not None:
                    raise ValueError("Duplicate keys found in " + str(component))
                children_new_bykey[child_new._key] = child_new

        # We will not try to intelligently handle the situation where
        # an unkeyed element is added or removed.
        # If the elements are unkeyed then try to match them pairwise.
        i_old = 0
        i_new = 0
        while i_new < len(children_new):
            child_new = children_new[i_new]
            if (key := child_new._key) is not None:
                if (child_old_bykey := children_old_bykey.get(key, None)) is not None and elements_match(
                    child_old_bykey,
                    child_new,
                ):
                    # then we have a match for reusing the old child
                    child_wtree = self._update_old_component(child_old_bykey, child_new, render_context)
                    children_new[i_new] = child_old_bykey
                    widgettree.children.append(child_wtree.component)
                    render_context.widget_tree[child_wtree.component] = child_wtree
                    children_old.remove(child_old_bykey)
                else:
                    # new child so render
                    widgettree.children.append(self._render(child_new, render_context).component)
                    # this component will need qt rerender
                    render_context.mark_qt_rerender(component, True)

            elif i_old < len(children_old):
                child_old = children_old[i_old]
                if elements_match(child_old, child_new):
                    # then we have a match for reusing the old child
                    child_wtree = self._update_old_component(child_old, child_new, render_context)
                    children_new[i_new] = child_old
                    widgettree.children.append(child_wtree.component)
                    render_context.widget_tree[child_wtree.component] = child_wtree
                    del children_old[i_old]
                else:
                    # new child so render
                    widgettree.children.append(self._render(child_new, render_context).component)
                    # this component will need qt rerender
                    render_context.mark_qt_rerender(component, True)
                    # leave this old element to be deleted
                    i_old += 1
            else:
                # new child so render
                widgettree.children.append(self._render(child_new, render_context).component)
                # this component will need qt rerender
                render_context.mark_qt_rerender(component, True)
            i_new += 1

        render_context.enqueued_deletions.extend(children_old)
        render_context.component_tree[component] = children_new
        render_context.widget_tree[component] = widgettree
        return children_new

    def _render_base_component(self, component: QtWidgetElement, render_context: _RenderContext) -> _WidgetTree:
        if component not in self._component_tree:
            # New component, simply render everything
            render_context.component_tree[component] = list(component.children)
            rendered_children = [self._render(child, render_context) for child in component.children]
            widgettree = _WidgetTree(component, [c.component for c in rendered_children])
            render_context.widget_tree[component] = widgettree
            render_context.mark_qt_rerender(component, True)
            return widgettree

        # Figure out which children can be re-used
        children = self._recycle_children(component, render_context)

        props_dict = dict(component.props._items)
        props_dict["children"] = tuple(children)
        render_context.mark_props_change(component, PropsDict(props_dict))
        return render_context.widget_tree[component]

    def _render(self, component: Element, render_context: _RenderContext) -> _WidgetTree:
        if component in render_context.widget_tree:
            return render_context.widget_tree[component]
        try:
            assert component._edifice_internal_references is not None
            for ref in component._edifice_internal_references:
                ref._value = component
        except TypeError as err:
            raise ValueError(
                f"{component.__class__} is not correctly initialized. "
                "Did you remember to call super().__init__() in the constructor? "
                "(alternatively, the register_props decorator will also correctly initialize the component)",
            ) from err
        component._controller = self._app

        if isinstance(component, QtWidgetElement):
            return self._render_base_component(component, render_context)

        # Before the render, set the hooks indices to 0.
        component._hook_state_index = 0
        component._hook_effect_index = 0
        component._hook_async_index = 0

        # Record that we are rendering this component with current use_state
        self._hook_state_setted.discard(component)

        # Call user provided render function and retrieve old results
        with Container() as container:
            prev_element = render_context.current_element
            render_context.current_element = component
            sub_component = component._render_element()
            render_context.current_element = prev_element
        # If the component.render() call evaluates to an Element
        # we use that as the sub_component the component renders as.
        if sub_component is None:
            # If the render() method doesn't render as
            # an Element (always the case for @component Components)
            # we obtain the rendered sub_component as either:
            #
            # 1. The only child of the Container wrapping the render, or
            # 2. A View element containing the children of the Container
            if len(container.children) == 1:
                sub_component = container.children[0]
            else:
                newline = "\n"
                message = dedent(
                    f"""\
                    A @component must render as exactly one Element.
                    Element {component} renders as {len(container.children)} elements.""",
                ) + newline.join([child.__str__() for child in container.children])
                raise ValueError(message)
        old_rendering: list[Element] | None = self._component_tree.get(component, None)

        if old_rendering is not None and elements_match(old_rendering[0], sub_component):
            # TODO Why do we set the key of the widget_tree to be a #component
            # Element here? This is not used anywhere. This widget_tree[component]
            # insertion should not happen. widget_tree key should be a QtWidgetElement.
            # See _widget_tree.
            render_context.widget_tree[component] = self._update_old_component(
                old_rendering[0],
                sub_component,
                render_context,
            )
        else:
            if old_rendering is not None:
                render_context.enqueued_deletions.extend(old_rendering)
            render_context.component_tree[component] = [sub_component]
            # TODO Why do we set the key of the widget_tree to be a #component
            # Element here? This is not used anywhere. This widget_tree[component]
            # insertion should not happen. widget_tree key should be a QtWidgetElement.
            # See _widget_tree.
            render_context.widget_tree[component] = self._render(sub_component, render_context)

        return render_context.widget_tree[component]

    def gen_qt_commands(self, element: QtWidgetElement, render_context: _RenderContext) -> list[CommandType]:
        """
        Recursively generate the update commands for the widget tree.
        """
        commands: list[CommandType] = []
        if self.is_stopped:
            return commands

        children = _get_widget_children(render_context.widget_tree, element)
        for child in children:
            rendered = self.gen_qt_commands(child, render_context)
            commands.extend(rendered)

        if not render_context.need_rerender(element):
            return commands

        old_props = render_context.get_old_props(element)
        new_props = PropsDict({k: v for k, v in element.props._items if k not in old_props or old_props[k] != v})

        # Call user provided render function and retrieve old results
        prev_element = render_context.current_element
        render_context.current_element = element
        commands.extend(element._qt_update_commands(render_context.widget_tree, new_props))
        render_context.current_element = prev_element
        return commands

    def _request_rerender(self, components: list[Element]) -> RenderResult:
        if self.is_stopped:
            return RenderResult([])

        components_ = components[:]
        # Before the render, reduce the _hook_state updaters.
        # We can't do this after the render, because there may have been state
        # updates from event handlers.
        for element in self._hook_state_setted:
            hooks = self._hook_state[element]
            for hook in hooks:
                state0 = hook.state
                for updater in hook.updaters:
                    if callable(updater):
                        hook.state = updater(hook.state)
                        # We don't catch the state updater exceptions.
                        # We want the program to crash if state updaters throw.
                    else:
                        hook.state = updater
                if state0 != hook.state:
                    # State changed so we need to re-render this component.
                    if element not in components_:
                        components_.append(element)
                hook.updaters.clear()

        all_commands: list[CommandType] = []

        # Here is the problem.
        # We need to render the child before parent if the child state changed.
        # We need to render the parent before child if the child props changed.
        # So we do a complete render of each component individually, and then
        # we don't have to solve the problem of the order of rendering.
        for component in components_:
            commands: list[CommandType] = []

            render_context = _RenderContext(self)
            local_state.render_context = render_context

            widget_tree = self._render(component, render_context)

            # Generate the update commands from the widget trees
            commands.extend(self.gen_qt_commands(widget_tree.component, render_context))

            # Update the stored component trees and widget trees
            self._component_tree.update(render_context.component_tree)
            self._widget_tree.update(render_context.widget_tree)

            # This is the phase of the render when the commands run.
            for command in commands:
                try:
                    command.fn(*command.args, **command.kwargs)
                except Exception:  # noqa: PERF203
                    logger.exception(f"Exception while running command:\n{command}")  # noqa: G004
            all_commands.extend(commands)

            # Delete components that should be deleted (and call the respective unmounts)
            for component_delete in render_context.enqueued_deletions:
                self._delete_component(component_delete, True)

        # after render, call the use_effect setup functions.
        # we want to guarantee that elements are fully rendered before
        # effects are performed.
        for hooks in self._hook_effect.values():
            for hook in hooks:
                if hook.setup is not None:
                    if hook.cleanup is not None:
                        try:
                            hook.cleanup()
                        except Exception:  # noqa: S110, BLE001
                            pass
                        finally:
                            hook.cleanup = None
                    try:
                        hook.cleanup = hook.setup()
                    except Exception:  # noqa: BLE001
                        hook.cleanup = None
                    finally:
                        hook.setup = None

        # We return all the commands but that's only needed for testing.
        return RenderResult(all_commands)

    def use_state(
        self,
        element: Element,
        initial_state: _T_use_state | tp.Callable[[], _T_use_state],
    ) -> tuple[
        _T_use_state,  # current value
        tp.Callable[[_T_use_state | tp.Callable[[_T_use_state], _T_use_state]], None],  # updater
    ]:
        hooks = self._hook_state[element]

        h_index = element._hook_state_index
        element._hook_state_index += 1

        if len(hooks) <= h_index:
            # Then this is the first render.
            hook = _HookState(
                # Call the initializer function if it is a function.
                initial_state() if callable(initial_state) else initial_state,
                [],
                element,
                self,
            )
            if callable(hook.state):
                raise ValueError("The state value of use_state cannot be Callable.")
            hooks.append(hook)
        else:
            hook = hooks[h_index]

        return (hook.state, hook.setter)

    def use_effect(
        self,
        element: Element,
        setup: tp.Callable[[], tp.Callable[[], None] | None],
        dependencies: tp.Any = None,
    ) -> None:
        # https://legacy.reactjs.org/docs/hooks-effect.html#example-using-hooks
        # effects happen “after render”.
        # React guarantees the DOM has been updated by the time it runs the effects.

        hooks = self._hook_effect[element]

        h_index = element._hook_effect_index
        element._hook_effect_index += 1

        if len(hooks) <= h_index:
            # then this is the first render
            hook = _HookEffect(setup, None, dependencies)
            hooks.append(hook)

        else:
            # then this is not the first render
            hook = hooks[h_index]
            if hook.dependencies is None or hook.dependencies != dependencies:
                # deps changed
                hook.setup = setup
            hook.dependencies = dependencies

    def use_async(
        self,
        element: Element,
        fn_coroutine: tp.Callable[[], Coroutine[None, None, None]],
        dependencies: tp.Any,
    ) -> Callable[[], None]:
        hooks = self._hook_async[element]
        h_index = element._hook_async_index
        element._hook_async_index += 1

        # When the done_callback is called,
        # this component might have already unmounted. In that case
        # this done_callback will still be holding a reference to the
        # _HookAsync, and the _HookAsync.queue will be cleared.
        # After the done_callback is called, the _HookAsync object
        # should be garbage collected.

        if len(hooks) <= h_index:
            # then this is the first render.
            task = asyncio.create_task(fn_coroutine())
            hook = _HookAsync(
                task=task,
                dependencies=dependencies,
                queue=[],
            )
            hooks.append(hook)

            def done_callback(_future_object):
                hook.task = None
                if len(hook.queue) > 0:
                    # There is another async task waiting in the queue
                    task = asyncio.create_task(hook.queue.pop(0)())
                    hook.task = task
                    task.add_done_callback(done_callback)

            task.add_done_callback(done_callback)

            def cancel():
                task.cancel()

            return cancel

        if dependencies != (hook := hooks[h_index]).dependencies:
            # then this is not the first render and deps changed
            hook.dependencies = dependencies
            if hook.task is not None:
                # There's already an old async effect in flight, so enqueue
                # the new async effect and cancel the old async effect.
                # We also want to cancel all of the other async effects
                # in the queue, so the queue should have max len 1.
                # Maybe queue should be type Optional instead of list? That
                # would be weird though.
                hook.queue.clear()
                hook.queue.append(fn_coroutine)
                hook.task.cancel()

            else:
                hook.task = asyncio.create_task(fn_coroutine())

                def done_callback(_future_object):
                    hook.task = None
                    if len(hook.queue) > 0:
                        # There is another async task waiting in the queue
                        task = asyncio.create_task(hook.queue.pop(0)())
                        hook.task = task
                        task.add_done_callback(done_callback)

                hook.task.add_done_callback(done_callback)

            def cancel():
                if hook.task is not None:
                    hook.task.cancel()
                else:
                    hook.queue.clear()

            return cancel

        # not first render, dependencies did not change
        hook = hooks[h_index]

        def cancel():
            if hook.task is not None:
                hook.task.cancel()
            else:
                hook.queue.clear()

        return cancel
