import asyncio
from collections import defaultdict
from collections.abc import Callable, Coroutine, Iterator, Iterable
from dataclasses import dataclass
import functools
import inspect
import logging
from textwrap import dedent
import threading
import typing as tp
from typing_extensions import Self

from .qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtCore, QtWidgets, QtGui
else:
    from PySide6 import QtCore, QtWidgets, QtGui

_T_use_state = tp.TypeVar("_T_use_state")
logger = logging.getLogger("Edifice")

P = tp.ParamSpec("P")

StyleType = tp.Optional[tp.Union[tp.Mapping[tp.Text, tp.Any], tp.Sequence[tp.Mapping[tp.Text, tp.Any]]]]


def _dict_to_style(d, prefix="QWidget"):
    d = d or {}
    stylesheet = prefix + "{%s}" % (";".join("%s: %s" % (k, v) for (k, v) in d.items()))
    return stylesheet


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


class PropsDict(object):
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

    def __init__(self, dictionary: tp.Mapping[tp.Text, tp.Any]):
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

    def _get(self, key: tp.Text, default: tp.Optional[tp.Any] = None) -> tp.Any:
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
        raise KeyError("%s not in props" % key)

    def __repr__(self):
        return "PropsDict(%s)" % repr(self._d)

    def __str__(self) -> str:
        return "PropsDict(%s)" % str(self._d)

    def __setattr__(self, key, value) -> tp.NoReturn:
        raise ValueError("Props are immutable")


class Reference(object):
    """Reference to a :class:`Element` to allow imperative modifications.

    While Edifice is a declarative library and tries to abstract away the need to issue
    imperative commands to widgets,
    this is not always possible, either due to limitations with the underlying backened,
    or because some feature implemented by the backend is not yet supported by the declarative layer.
    In these cases, you might need to issue imperative commands to the underlying Widgets and Elements,
    and :class:`Reference` gives you a handle to the currently rendered :class:`Element`.

    Create a :class:`Reference` with the :func:`use_ref` Hook::

        @component
        def MyComp(self):
            ref = use_ref()

            def issue_command(e):
                ref().command()

            AnotherElement(on_click=issue_command).register_ref(ref)

    Under the hood, :func:`Element.register_ref` registers the :class:`Reference` object
    to the :class:`Element` returned by the :code:`render` function.
    While rendering, Edifice will examine all requested references and attaches
    them to the correct :class:`Element`.

    Initially, a :class:`Reference` object will point to :code:`None`.
    After the first render, it will point to the rendered :class:`Element`.
    When the rendered :class:`Element` dismounts, the reference will once again
    point to :code:`None`.
    You may assume that :class:`Reference` is valid whenever it is
    not :code:`None`.
    :class:`Reference` will evaluate false if the underlying value is :code:`None`.

    :class:`Reference` can be dereferenced by calling it. An idiomatic way of using references is::

        if ref:
            ref().do_something()

    If you want to access the QWidget underlying a Base Element,
    you can use the :code:`underlying` attribute of the Element.
    :func:`use_effect` Hooks always run after the Elements are fully rendered::

        @component
        def MyComp(self):
            ref = use_ref()

            def did_render():
                element = ref()
                assert isinstance(element, Label)
                element.underlying.setText("After")
                return lambda:None

            use_effect(did_render, ref)

            with View():
                Label("Before").register_ref(ref)
    """

    def __init__(self):
        self._value: Element | None = None

    def __bool__(self) -> bool:
        return self._value is not None

    def __hash__(self) -> int:
        return id(self)

    def __call__(self) -> tp.Optional["Element"]:
        return self._value


T = tp.TypeVar("T")


class ControllerProtocol(tp.Protocol):
    """Protocol for App"""

    def _request_rerender(self, components: Iterable["Element"], kwargs: dict[str, tp.Any]):
        pass

    def _defer_rerender(self, components: list["Element"]):
        pass

    def stop(self):
        pass


class _Tracker:
    """
    During a render, track the current element and the children being
    added to the current element.
    """

    children: list["Element"]

    def __init__(self, component: "Element"):
        self.component = component
        self.children = []

    def append_child(self, component: "Element"):
        self.children.append(component)

    def collect(self) -> list["Element"]:
        """Collect all the children for the component, except for... something?"""
        children = set()
        for child in self.children:
            # find_components will flatten lists of elements, but according
            # to append_child, it's impossible for child to be a list.
            # So why do we need find_components?
            children |= find_components(child) - {child}
        return [child for child in self.children if child not in children]


class _RenderContext(object):
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
    current_element: "Element | None"
    """The Element currently being rendered."""

    # I guess static scope typing of instance members is normal in Python?
    # https://peps.python.org/pep-0526/#class-and-instance-variable-annotations
    def __init__(
        self,
        engine: "RenderEngine",
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

    def mark_props_change(self, component: "Element", newprops: PropsDict):
        if component not in self.component_to_old_props:
            self.component_to_old_props[component] = component.props
        component._props = newprops._d

    def get_old_props(self, component):
        if component in self.component_to_old_props:
            return self.component_to_old_props[component]
        return PropsDict({})

    def mark_qt_rerender(self, component: "QtWidgetElement", need_rerender: bool):
        self.need_qt_command_reissue[component] = need_rerender

    def need_rerender(self, component: "QtWidgetElement"):
        return self.need_qt_command_reissue.get(component, False)


local_state = threading.local()


def get_render_context() -> _RenderContext:
    return getattr(local_state, "render_context")


def get_render_context_maybe() -> _RenderContext | None:
    return getattr(local_state, "render_context", None)


class Element:
    """The base class for Edifice Elements.

    In user code you should almost never use :class:`Element` directly. Instead
    use :doc:`Base Elements <../base_components>` and :func:`component` Elements.

    A :class:`Element` is a stateful container wrapping a render function.
    Elements have both internal and external properties.

    The external properties, **props**, are passed into the :class:`Element` by another
    :class:`Element`’s render function through the constructor. These values are owned
    by the external caller and should not be modified by this :class:`Element`.
    """

    _render_changes_context: dict | None = None
    _render_unwind_context: dict | None = None
    _controller: ControllerProtocol | None = None
    _edifice_internal_references: set[Reference] | None = None

    def __init__(self):
        super().__setattr__("_edifice_internal_references", set())
        self._props: dict[str, tp.Any] = {"children": []}
        # Ensure we only construct this element once
        assert getattr(self, "_initialized", False) is False
        self._initialized = True
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
        children = tracker.collect()
        prop = self._props.get("children", [])
        for child in children:
            prop.append(child)
        self._props["children"] = prop

    def _register_props(self, props: tp.Mapping[tp.Text, tp.Any]) -> None:
        """Register props.

        Args:
            props: a dictionary representing the props to register.
        """
        self._props.update(props)

    def set_key(self: Self, key: tp.Text) -> Self:
        """Sets the key of the Element.

        The key is used by the re-rendering logic to match a new list of Elements
        with an existing list of Elements.
        The algorithm will assume that Elements with the same key are logically the same.
        If the key is not provided, the list index will be used as the key;
        however, providing the key may provide more accurate results, leading to efficiency gains.

        Returns the Element to allow for chaining.

        Example::

            # inside a render call
            with edifice.View():
                edifice.Label("Hello").set_key("en")
                edifice.Label("Bonjour").set_key("fr")
                edifice.Label("Hola").set_key("es")

        Args:
            key: The key to label the Element with.
        Returns:
            The Element itself.
        """
        self._key = key
        return self

    def register_ref(self: Self, reference: Reference) -> Self:
        """Registers provided :class:`Reference` to this Element.

        During render, the provided reference will be set to point to the currently rendered instance of this Element
        (i.e. if another instance of the Element is rendered and the RenderEngine decides to reconcile the existing
        and current instances, the reference will eventually point to that previously existing Element.

        Args:
            reference: the Reference to register
        Returns:
            The Element self.
        """
        assert self._edifice_internal_references is not None
        self._edifice_internal_references.add(reference)
        return self

    @property
    def children(self) -> list["Element"]:
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
        self._props["children"] = children
        return self

    def __hash__(self):
        return id(self)

    def _tags(self):
        classname = self.__class__.__name__
        return [
            f"<{classname} id=0x%x %s>"
            % (id(self), " ".join("%s=%s" % (p, val) for (p, val) in self.props._items if p != "children")),
            "</%s>" % (classname),
            f"<{classname} id=0x%x %s />"
            % (id(self), " ".join("%s=%s" % (p, val) for (p, val) in self.props._items if p != "children")),
        ]

    def __str__(self):
        tags = self._tags()
        return tags[2]

    def _render_element(self) -> tp.Optional["Element"]:
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
C = tp.TypeVar("C", bound=Element)


def not_ignored(arg: tuple[str, tp.Any]) -> bool:
    return arg[0][0] != "_"


def component(f: Callable[tp.Concatenate[C, P], None]) -> Callable[P, Element]:
    """Decorator turning a render function of **props** into an :class:`Element`.

    The component will be re-rendered when its **props** are not :code:`__eq__`
    to the **props** from the last time the component rendered.

    The component function must render exactly one :class:`Element`.
    In the component function, declare a tree of :class:`Element` with a
    single root::

        @component
        def MySimpleComp(self, prop1, prop2, prop3):
            with View():
                Label(prop1)
                Label(prop2)
                Label(prop3)

    To declare an :class:`Element` to be the parent of some other
    :class:`Element` s in the tree, use the parent as a
    `with statement context manager <https://docs.python.org/3/reference/datamodel.html#context-managers>`_.

    To introduce **state** into a component, use :doc:`Hooks <../hooks>`.

    Each :class:`Element` is actually implemented as the constructor function
    for a Python class. The :class:`Element` constructor function also has
    the side-effect of inserting itself to the rendered :class:`Element` tree,
    as a child of the :code:`with` context layout Element.

    For that reason, you have to be careful about binding Elements to variables
    and passing them around. They will insert themselves at the time they are
    created. This code will **NOT** declare the intended Element tree, same as the code above::

        @component
        def MySimpleComp(self, prop1, prop2, prop3):
            label3 = Label(prop3)
            with View():
                Label(prop1)
                Label(prop2)
                label3

    To solve this, defer the construction of the Element with a lambda function.
    This code will declare the same intended Element tree as the code above::

        @component
        def MySimpleComp(self, prop1, prop2, prop3):
            label3 = lambda: Label(prop3)
            with View():
                Label(prop1)
                Label(prop2)
                label3()

    If these component Elements are render functions, then why couldn’t we just write
    a normal render function with no decorator::

        # No decorator
        def MySimpleComp(prop1, prop2, prop3):
            with View():
                Label(prop1)
                Label(prop2)
                Label(prop3)

    instead. The difference is, with the decorator, an actual :class:`Element` object is created,
    which can be viewed, for example, in the inspector. Moreover, you need an :class:`Element` to
    be able to use Hooks such as :func:`use_state`, since those are bound to an :class:`Element`.

    Args:
        f: the function to wrap. Its first argument must be self.
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
            name_to_val.update(((k, v) for (k, v) in kwargs.items() if k[0] != "_"))
            name_to_val["children"] = name_to_val.get("children") or []
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
    comp = tp.cast(Callable[P, Element], ComponentElement)
    return comp


def find_components(el: Element | list[Element]) -> set[Element]:
    match el:
        case Element():
            return {el}
        case list():
            elements = set()
            for child in el:
                elements |= find_components(child)
                # The type of el says that it's impossible for an element
                # in list[Element] to be a list[Element], so why recurse?
            return elements


@component
def Container(self):
    pass


ContextMenuType = tp.Mapping[tp.Text, tp.Union[None, tp.Callable[[], tp.Any], "ContextMenuType"]]


def _create_qmenu(menu: ContextMenuType, parent, title: tp.Optional[tp.Text] = None):
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


class QtWidgetElement(Element):
    """Base Qt Widget.

    All elements with an underlying
    `QWidget <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html>`_
    inherit from this element.

    The props add basic functionality such as styling and event handlers.


    Args:
        style: style for the widget. Could either be a dictionary or a list of dictionaries.

            See :doc:`../../styling` for a primer on styling.
        tool_tip:
            the tool tip displayed when hovering over the widget.
        cursor:
            the shape of the cursor when mousing over this widget. Must be one of:
            :code:`"default"`, :code:`"arrow"`, :code:`"pointer"`, :code:`"grab"`, :code:`"grabbing"`,
            :code:`"text"`, :code:`"crosshair"`, :code:`"move"`, :code:`"wait"`, :code:`"ew-resize"`,
            :code:`"ns-resize"`, :code:`"nesw-resize"`, :code:`"nwse-resize"`,
            :code:`"not-allowed"`, :code:`"forbidden"`
        context_menu:
            the context menu to display when the user right clicks on the widget.
            Expressed as a dict mapping the name of the context menu entry to either a function
            (which will be called when this entry is clicked) or to another sub context menu.
            For example, :code:`{"Copy": copy_fun, "Share": {"Twitter": twitter_share_fun, "Facebook": facebook_share_fun}}`
        css_class:
            a string or a list of strings, which will be stored in the :code:`css_class` property of the Qt Widget.
            This can be used in an application stylesheet, like:

                QLabel[css_class="heading"] { font-size: 18px; }

        size_policy:
            Horizontal and vertical resizing policy, of type `QSizePolicy <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSizePolicy.html>`_
        focus_policy:
            The various policies a widget can have with respect to acquiring keyboard focus, of type
            `FocusPolicy <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.PySide6.QtCore.Qt.FocusPolicy>`_.

            See also `QWidget.focusPolicy <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.PySide6.QtWidgets.QWidget.focusPolicy>`_.
        enabled:
            Whether the widget is
            `enabled <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html#PySide6.QtWidgets.PySide6.QtWidgets.QWidget.enabled>`_.
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
            `Qt.Key <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.PySide6.QtCore.Qt.Key>`_
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
        style: StyleType = None,
        tool_tip: tp.Optional[tp.Text] = None,
        cursor: tp.Optional[tp.Text] = None,
        context_menu: tp.Optional[ContextMenuType] = None,
        css_class: tp.Optional[tp.Any] = None,
        size_policy: tp.Optional[QtWidgets.QSizePolicy] = None,
        focus_policy: tp.Optional[QtCore.Qt.FocusPolicy] = None,
        enabled: tp.Optional[bool] = None,
        on_click: tp.Optional[tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]]] = None,
        on_key_down: tp.Optional[tp.Callable[[QtGui.QKeyEvent], None | tp.Awaitable[None]]] = None,
        on_key_up: tp.Optional[tp.Callable[[QtGui.QKeyEvent], None | tp.Awaitable[None]]] = None,
        on_mouse_down: tp.Optional[tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]]] = None,
        on_mouse_up: tp.Optional[tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]]] = None,
        on_mouse_enter: tp.Optional[tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]]] = None,
        on_mouse_leave: tp.Optional[tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]]] = None,
        on_mouse_move: tp.Optional[tp.Callable[[QtGui.QMouseEvent], None | tp.Awaitable[None]]] = None,
        on_drop: tp.Optional[
            tp.Callable[[QtGui.QDragEnterEvent | QtGui.QDragMoveEvent | QtGui.QDragLeaveEvent | QtGui.QDropEvent], None]
        ] = None,
        on_resize: tp.Optional[tp.Callable[[QtGui.QResizeEvent], None | tp.Awaitable[None]]] = None,
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
                "on_drop": on_drop,
                "on_resize": on_resize,
            }
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
        self._on_drop: tp.Optional[
            tp.Callable[[QtGui.QDragEnterEvent | QtGui.QDragMoveEvent | QtGui.QDragLeaveEvent | QtGui.QDropEvent], None]
        ] = None
        self._on_resize: tp.Optional[tp.Callable[[QtGui.QResizeEvent], None]] = None
        self._default_mouse_press_event = None
        self._default_mouse_release_event = None
        self._default_mouse_move_event = None
        self._default_mouse_enter_event = None
        self._default_mouse_leave_event = None
        self._default_drag_enter_event = None
        self._default_drag_move_event = None
        self._default_drag_leave_event = None
        self._default_drop_event = None
        self._default_resize_event = None

        self._context_menu = None
        self._context_menu_connected = False
        if cursor is not None:
            if cursor not in _CURSORS:
                raise ValueError("Unrecognized cursor %s. Cursor must be one of %s" % (cursor, list(_CURSORS.keys())))

        self.underlying: QtWidgets.QWidget | None = None
        """
        The underlying QWidget, which may not exist if this Element has not rendered.
        """

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

    def _mouse_press(self, event: QtGui.QMouseEvent):
        if self._on_mouse_down is not None:
            self._on_mouse_down(event)
        if self._default_mouse_press_event is not None:
            self._default_mouse_press_event(event)

    def _mouse_release(self, event):
        assert self.underlying is not None
        event_pos = event.pos()
        if self._on_mouse_up is not None:
            self._on_mouse_up(event)
        if self._default_mouse_release_event is not None:
            self._default_mouse_release_event(event)
        geometry = self.underlying.geometry()

        if 0 <= event_pos.x() <= geometry.width() and 0 <= event_pos.y() <= geometry.height():
            self._mouse_clicked(event)
        self._mouse_pressed = False

    def _mouse_clicked(self, ev):
        if self._on_click:
            self._on_click(ev)

    def _set_on_click(self, underlying: QtWidgets.QWidget, on_click):
        assert self.underlying is not None
        # FIXME: Should this not use `underlying`?
        if on_click is not None:
            self._on_click = _ensure_future(on_click)
        else:
            self._on_click = None
        if self._default_mouse_press_event is None:
            self._default_mouse_press_event = self.underlying.mousePressEvent
        self.underlying.mousePressEvent = self._mouse_press
        if self._default_mouse_release_event is None:
            self._default_mouse_release_event = self.underlying.mouseReleaseEvent
        self.underlying.mouseReleaseEvent = self._mouse_release

    def _set_on_key_down(self, underlying: QtWidgets.QWidget, on_key_down):
        assert self.underlying is not None
        if self._default_on_key_down is None:
            self._default_on_key_down = self.underlying.keyPressEvent
        if on_key_down is not None:
            self._on_key_down = _ensure_future(on_key_down)
        else:
            self._on_key_down = self._default_on_key_down
        self.underlying.keyPressEvent = self._on_key_down

    def _set_on_key_up(self, underlying: QtWidgets.QWidget, on_key_up):
        assert self.underlying is not None
        if self._default_on_key_up is None:
            self._default_on_key_up = self.underlying.keyReleaseEvent
        if on_key_up is not None:
            self._on_key_up = _ensure_future(on_key_up)
        else:
            self._on_key_up = self._default_on_key_up
        self.underlying.keyReleaseEvent = self._on_key_up

    def _set_on_mouse_down(self, underlying: QtWidgets.QWidget, on_mouse_down):
        assert self.underlying is not None
        if on_mouse_down is not None:
            self._on_mouse_down = _ensure_future(on_mouse_down)
        else:
            self._on_mouse_down = None
        if self._default_mouse_press_event is None:
            self._default_mouse_press_event = self.underlying.mousePressEvent
        self.underlying.mousePressEvent = self._mouse_press

    def _set_on_mouse_up(self, underlying: QtWidgets.QWidget, on_mouse_up):
        assert self.underlying is not None
        if on_mouse_up is not None:
            self._on_mouse_up = _ensure_future(on_mouse_up)
        else:
            self._on_mouse_up = None
        if self._default_mouse_release_event is None:
            self._default_mouse_release_event = self.underlying.mouseReleaseEvent
        self.underlying.mouseReleaseEvent = self._mouse_release

    def _set_on_mouse_enter(self, underlying: QtWidgets.QWidget, on_mouse_enter):
        assert self.underlying is not None
        if self._default_mouse_enter_event is None:
            self._default_mouse_enter_event = self.underlying.enterEvent
        if on_mouse_enter is not None:
            self._on_mouse_enter = _ensure_future(on_mouse_enter)
            self.underlying.enterEvent = self._on_mouse_enter
        else:
            self._on_mouse_enter = None
            self.underlying.enterEvent = self._default_mouse_enter_event

    def _set_on_mouse_leave(self, underlying: QtWidgets.QWidget, on_mouse_leave):
        assert self.underlying is not None
        if self._default_mouse_leave_event is None:
            self._default_mouse_leave_event = self.underlying.leaveEvent
        if on_mouse_leave is not None:
            self._on_mouse_leave = _ensure_future(on_mouse_leave)
            self.underlying.leaveEvent = self._on_mouse_leave
        else:
            self.underlying.leaveEvent = self._default_mouse_leave_event
            self._on_mouse_leave = None

    def _set_on_mouse_move(self, underlying: QtWidgets.QWidget, on_mouse_move):
        assert self.underlying is not None
        if self._default_mouse_move_event is None:
            self._default_mouse_move_event = self.underlying.mouseMoveEvent
        if on_mouse_move is not None:
            self._on_mouse_move = _ensure_future(on_mouse_move)
            self.underlying.mouseMoveEvent = self._on_mouse_move
            self.underlying.setMouseTracking(True)
        else:
            self._on_mouse_move = None
            self.underlying.mouseMoveEvent = self._default_mouse_move_event

    def _set_on_drop(
        self,
        underlying: QtWidgets.QWidget,
        on_drop: tp.Optional[
            tp.Callable[[QtGui.QDragEnterEvent | QtGui.QDragMoveEvent | QtGui.QDragLeaveEvent | QtGui.QDropEvent], None]
        ],
    ):
        assert self.underlying is not None

        # Store the QWidget's default virtual event handler methods
        if self._default_drag_enter_event is None:
            self._default_drag_enter_event = self.underlying.dragEnterEvent
        if self._default_drag_move_event is None:
            self._default_drag_move_event = self.underlying.dragMoveEvent
        if self._default_drag_leave_event is None:
            self._default_drag_leave_event = self.underlying.dragLeaveEvent
        if self._default_drop_event is None:
            self._default_drop_event = self.underlying.dropEvent

        if on_drop is not None:
            self._on_drop = on_drop
            self.underlying.setAcceptDrops(True)
            self.underlying.dragEnterEvent = self._on_drop  # type: ignore
            self.underlying.dragMoveEvent = self._on_drop  # type: ignore
            self.underlying.dragLeaveEvent = self._on_drop  # type: ignore
            self.underlying.dropEvent = self._on_drop  # type: ignore
        else:
            self._on_drop = None
            self.underlying.setAcceptDrops(False)

    def _resizeEvent(self, event: QtGui.QResizeEvent):
        if self._on_resize is not None:
            self._on_resize(event)

    def _set_on_resize(self, on_resize: tp.Optional[tp.Callable[[QtGui.QResizeEvent], None]]):
        assert self.underlying is not None

        # Store the QWidget's default virtual event handler method one time
        if self._default_resize_event is None:
            self._default_resize_event = self.underlying.resizeEvent

        if on_resize is not None:
            self._on_resize = _ensure_future(on_resize)
            self.underlying.resizeEvent = self._resizeEvent
        else:
            self._on_resize = None
            self.underlying.resizeEvent = self._default_resize_event

    def _gen_styling_commands(
        self,
        style,
        underlying: QtWidgets.QWidget | None,
        underlying_layout: QtWidgets.QLayout | None = None,
    ):
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
            #
            # Also we keep the "margin" style for the QLayout because
            # that's how PyEdifice has always worked and we don't want to
            # break backwards compatibility for that yet.
            set_padding = False
            new_padding = [0, 0, 0, 0]
            if "margin" in style:
                new_padding = [int(_css_to_number(style["margin"]))] * 4
                style.pop("margin")
                set_padding = True
            if "margin-left" in style:
                new_padding[0] = int(_css_to_number(style["margin-left"]))
                style.pop("margin-left")
                set_padding = True
            if "margin-right" in style:
                new_padding[2] = int(_css_to_number(style["margin-right"]))
                style.pop("margin-right")
                set_padding = True
            if "margin-top" in style:
                new_padding[1] = int(_css_to_number(style["margin-top"]))
                style.pop("margin-top")
                set_padding = True
            if "margin-bottom" in style:
                new_padding[3] = int(_css_to_number(style["margin-bottom"]))
                style.pop("margin-bottom")
                set_padding = True
            if "padding" in style:
                new_padding = [int(_css_to_number(style["padding"]))] * 4
                style.pop("padding")
                set_padding = True
            if "padding-left" in style:
                new_padding[0] = int(_css_to_number(style["padding-left"]))
                style.pop("padding-left")
                set_padding = True
            if "padding-right" in style:
                new_padding[2] = int(_css_to_number(style["padding-right"]))
                style.pop("padding-right")
                set_padding = True
            if "padding-top" in style:
                new_padding[1] = int(_css_to_number(style["padding-top"]))
                style.pop("padding-top")
                set_padding = True
            if "padding-bottom" in style:
                new_padding[3] = int(_css_to_number(style["padding-bottom"]))
                style.pop("padding-bottom")
                set_padding = True

            set_align = None
            if "align" in style:
                if style["align"] == "left":
                    set_align = QtCore.Qt.AlignmentFlag.AlignLeft
                elif style["align"] == "center":
                    set_align = QtCore.Qt.AlignmentFlag.AlignCenter
                elif style["align"] == "right":
                    set_align = QtCore.Qt.AlignmentFlag.AlignRight
                elif style["align"] == "justify":
                    set_align = QtCore.Qt.AlignmentFlag.AlignJustify
                elif style["align"] == "top":
                    set_align = QtCore.Qt.AlignmentFlag.AlignTop
                elif style["align"] == "bottom":
                    set_align = QtCore.Qt.AlignmentFlag.AlignBottom
                else:
                    logger.warning("Unknown alignment: %s", style["align"])
                style.pop("align")

            if set_padding:
                commands.append(
                    CommandType(
                        underlying_layout.setContentsMargins,
                        new_padding[0],
                        new_padding[1],
                        new_padding[2],
                        new_padding[3],
                    )
                )
            if set_align:
                commands.append(CommandType(underlying_layout.setAlignment, set_align))
        else:
            if "align" in style:
                if style["align"] == "left":
                    set_align = "AlignLeft"
                elif style["align"] == "center":
                    set_align = "AlignCenter"
                elif style["align"] == "right":
                    set_align = "AlignRight"
                elif style["align"] == "justify":
                    set_align = "AlignJustify"
                elif style["align"] == "top":
                    set_align = "AlignTop"
                elif style["align"] == "bottom":
                    set_align = "AlignBottom"
                else:
                    logger.warning("Unknown alignment: %s", style["align"])
                    set_align = None
                style.pop("align")
                if set_align is not None:
                    style["qproperty-alignment"] = set_align

        if "font-size" in style:
            font_size = _css_to_number(style["font-size"])
            if self._size_from_font is not None:
                size = self._size_from_font(font_size)
                self._width = size[0]
                self._height = size[1]
            if not isinstance(style["font-size"], str):
                style["font-size"] = "%dpx" % font_size
        if "width" in style:
            if "min-width" not in style:
                style["min-width"] = style["width"]
            if "max-width" not in style:
                style["max-width"] = style["width"]
        # else:
        #     if "min-width" not in style:
        #         style["min-width"] = self._get_width(children)

        if "height" in style:
            if "min-height" not in style:
                style["min-height"] = style["height"]
            if "max-height" not in style:
                style["max-height"] = style["height"]
        # else:
        #     if "min-height" not in style:
        #         style["min-height"] = self._get_height(children)

        set_move = False
        move_coords = [0, 0]
        if "top" in style:
            set_move = True
            move_coords[1] = int(_css_to_number(style["top"]))
            self._top = move_coords[1]
        if "left" in style:
            set_move = True
            move_coords[0] = int(_css_to_number(style["left"]))
            self._left = move_coords[0]

        if set_move:
            assert self.underlying is not None
            commands.append(CommandType(self.underlying.move, move_coords[0], move_coords[1]))

        assert self.underlying is not None
        css_string = _dict_to_style(style, "QWidget#" + str(id(self)))
        commands.append(CommandType(self.underlying.setStyleSheet, css_string))
        return commands

    def _set_context_menu(self, underlying: QtWidgets.QWidget):
        if self._context_menu_connected:
            underlying.customContextMenuRequested.disconnect()
        self._context_menu_connected = True
        underlying.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        assert self.underlying is not None
        if self.props.context_menu is not None:
            menu = _create_qmenu(self.props.context_menu, self.underlying)
            pos = self.underlying.mapToGlobal(pos)
            menu.move(pos)
            menu.show()

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, "_WidgetTree"],
        newprops: PropsDict,
    ) -> list[CommandType]:
        raise NotImplementedError

    def _qt_update_commands_super(
        self,
        widget_trees: dict[Element, "_WidgetTree"],
        # We must pass all of the widget_trees because some elements
        # like TableGridView need to know the children of the children.
        newprops: PropsDict,
        underlying: QtWidgets.QWidget,
        underlying_layout: QtWidgets.QLayout | None = None,
    ) -> list[CommandType]:
        commands: list[CommandType] = []
        for prop in newprops:
            if prop == "style":
                style = newprops[prop] or {}
                if isinstance(style, list):
                    # style is nonempty since otherwise the or statement would make it a dict
                    first_style = style[0].copy()
                    for next_style in style[1:]:
                        first_style.update(next_style)
                    style = first_style
                else:
                    style = dict(style)
                commands.extend(self._gen_styling_commands(style, underlying, underlying_layout))
            elif prop == "size_policy":
                if newprops.size_policy is not None:
                    commands.append(CommandType(underlying.setSizePolicy, newprops.size_policy))
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
            elif prop == "on_drop":
                commands.append(CommandType(self._set_on_drop, underlying, newprops.on_drop))
            elif prop == "on_resize":
                commands.append(CommandType(self._set_on_resize, newprops.on_resize))
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
                    ]
                )
            elif prop == "cursor":
                cursor = self.props.cursor or ("default" if self.props.on_click is None else "pointer")
                commands.append(CommandType(underlying.setCursor, _CURSORS[cursor]))
            elif prop == "context_menu":
                if self._context_menu_connected:
                    underlying.customContextMenuRequested.disconnect()
                if self.props.context_menu is not None:
                    commands.append(
                        CommandType(underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
                    )
                    commands.append(CommandType(self._set_context_menu, underlying))
                else:
                    commands.append(
                        CommandType(underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu)
                    )
        return commands


class _WidgetTree(object):
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
        print("  " * indent + tags[0])
        for child in t.children:
            print_tree(widget_trees, child, indent=indent + 1)
        print("  " * indent + tags[1])
    else:
        print("  " * indent + tags[2])


class RenderResult(object):
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
    return (
        (a.__class__ == b.__class__)
        and (a.__class__.__name__ == b.__class__.__name__)
        and (getattr(a, "_key", None) == getattr(b, "_key", None))
    )


class RenderEngine(object):
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

    def __init__(self, root: Element, app=None):
        self._component_tree: dict[Element, list[Element]] = {}
        """
        The _component_tree maps an Element to its children.
        """
        self._widget_tree: dict[Element, _WidgetTree] = {}
        """
        Map of an Element to its rendered widget tree.
        """
        self._root = root
        self._app = app

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
                    except Exception:
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
                new_component_class = [new_cls for old_cls, new_cls in classes if old_cls == comp.__class__][0]
                if new_component_class is None:
                    raise ValueError("Error after updating code: cannot find class %s" % comp.__class__)
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
            except KeyError:
                k = None
                for k, _ in parameters[1:]:
                    if k not in old_comp.props:
                        break
                raise ValueError(
                    f"Error while reloading {old_comp}: " f"New class expects prop ({k}) not present in old class"
                )
            parts[3] = new_comp_class(**kwargs)
            parts[3]._props.update(old_comp._props)
            if hasattr(old_comp, "_key"):
                parts[3]._key = old_comp._key

        # 3) Replace old component in the place in the tree where they first appear, with a reference to new component

        backup = {}
        for old_comp, _, parent_comp, new_comp in components_to_replace:
            backup[parent_comp] = list(parent_comp.children)
            for i, comp in enumerate(parent_comp.children):
                if comp is old_comp:
                    parent_comp._props["children"][i] = new_comp
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

        # 5) call _render for all new component parents
        try:
            logger.info(
                "Rerendering parents of: %s",
                [new_comp_class.__name__ for _, new_comp_class, _, _ in components_to_replace],
            )
            logger.info("Rerendering: %s", [parent for _, _, parent, _ in components_to_replace])
            self._request_rerender([parent_comp for _, _, parent_comp, _ in components_to_replace])
        except Exception as e:
            # Restore components
            for parent_comp, backup_val in backup.items():
                parent_comp._props["children"] = backup_val
            raise e

    def _update_old_component(
        self, component: Element, new_component: Element, render_context: _RenderContext
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

        # TODO So _should_update returned False but then we call
        # mark_props_change? What does mark_props_change mean then?
        render_context.mark_props_change(component, newprops)
        return self._widget_tree[component]

    def _recycle_children(self, component: QtWidgetElement, render_context: _RenderContext) -> list[Element]:
        # Children diffing and reconciliation
        #
        # Returns element children, which contains all the future children of the component:
        # a mixture of old components (if they can be updated) and new ones
        #
        # Returns children widget trees, cached or newly rendered.

        children_old_bykey: dict[str, Element] = dict()
        children_new_bykey: dict[str, Element] = dict()

        children_old_ = self._component_tree[component]

        widgettree = _WidgetTree(component, [])

        # We will mutate children_old to reuse and remove old elements if we can match them.
        # Ordering of children_old must be preserved for reverse deletion.
        children_old: list[Element] = children_old_[:]
        for child_old in children_old:
            if hasattr(child_old, "_key"):
                children_old_bykey[child_old._key] = child_old

        # We will mutate children_new to replace them with old elements if we can match them.
        children_new: list[Element] = component.children[:]
        for child_new in children_new:
            if hasattr(child_new, "_key"):
                if children_new_bykey.get(child_new._key, None) is not None:
                    raise ValueError("Duplicate keys found in %s" % component)
                children_new_bykey[child_new._key] = child_new

        # We will not try to intelligently handle the situation where
        # an unkeyed element is added or removed.
        # If the elements are unkeyed then try to match them pairwise.
        i_old = 0
        i_new = 0
        while i_new < len(children_new):
            child_new = children_new[i_new]
            if (key := getattr(child_new, "_key", None)) is not None:
                if (child_old_bykey := children_old_bykey.get(key, None)) is not None and elements_match(
                    child_old_bykey, child_new
                ):
                    # then we have a match for reusing the old child
                    self._update_old_component(child_old_bykey, child_new, render_context)
                    children_new[i_new] = child_old_bykey
                    if (w := render_context.widget_tree.get(child_old_bykey, None)) is not None:
                        # Try to get the cached WidgetTree from this render
                        widgettree.children.append(w.component)
                    else:
                        # Get the cached WidgetTree from previous render
                        widgettree.children.append(self._widget_tree[child_old_bykey].component)
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
                    self._update_old_component(child_old, child_new, render_context)
                    children_new[i_new] = child_old
                    if (w := render_context.widget_tree.get(child_old, None)) is not None:
                        # Try to get the cached WidgetTree from this render
                        widgettree.children.append(w.component)
                    else:
                        # Get the cached WidgetTree from previous render
                        widgettree.children.append(self._widget_tree[child_old].component)
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
        props_dict["children"] = list(children)
        render_context.mark_props_change(component, PropsDict(props_dict))
        return render_context.widget_tree[component]

    def _render(self, component: Element, render_context: _RenderContext) -> _WidgetTree:
        if component in render_context.widget_tree:
            return render_context.widget_tree[component]
        try:
            assert component._edifice_internal_references is not None
            for ref in component._edifice_internal_references:
                ref._value = component
        except TypeError:
            raise ValueError(
                f"{component.__class__} is not correctly initialized. "
                "Did you remember to call super().__init__() in the constructor? "
                "(alternatively, the register_props decorator will also correctly initialize the component)"
            )
        component._controller = self._app

        if isinstance(component, QtWidgetElement):
            ret = self._render_base_component(component, render_context)
            return ret

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
                    Element {component} renders as {len(container.children)} elements."""
                ) + newline.join([child.__str__() for child in container.children])
                raise ValueError(message)
        old_rendering: list[Element] | None = self._component_tree.get(component, None)

        if old_rendering is not None and elements_match(old_rendering[0], sub_component):
            render_context.widget_tree[component] = self._update_old_component(
                old_rendering[0], sub_component, render_context
            )
        else:
            if old_rendering is not None:
                render_context.enqueued_deletions.extend(old_rendering)
            render_context.component_tree[component] = [sub_component]
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
        commands.extend(element._qt_update_commands(render_context.widget_tree, new_props))
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
                except Exception as ex:
                    logger.exception("Exception while running command:\n" + str(command) + "\n" + str(ex) + "\n")
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
                        except Exception:
                            pass
                        finally:
                            hook.cleanup = None
                    try:
                        hook.cleanup = hook.setup()
                    except Exception:
                        hook.cleanup = None
                    finally:
                        hook.setup = None

        # We return all the commands but that's only needed for testing.
        return RenderResult(all_commands)

    def use_state(
        self, element: Element, initial_state: _T_use_state
    ) -> tuple[
        _T_use_state,  # current value
        tp.Callable[[_T_use_state | tp.Callable[[_T_use_state], _T_use_state]], None],  # updater
    ]:
        hooks = self._hook_state[element]

        h_index = element._hook_state_index
        element._hook_state_index += 1

        if len(hooks) <= h_index:
            # then this is the first render
            hook = _HookState(initial_state, list())
            hooks.append(hook)
        else:
            hook = hooks[h_index]

        def setter(updater):
            if element not in self._hook_state:
                # Then the component has been deleted and unmounted.
                # This might happen if the setter is called during a
                # a use_async CancelledError handler.
                # In that case, we don't want to update the state.
                return
            hook.updaters.append(updater)
            self._hook_state_setted.add(element)
            assert self._app is not None
            self._app._defer_rerender(element)

        return (hook.state, setter)

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

        elif dependencies != (hook := hooks[h_index]).dependencies:
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

        else:
            # not first render, dependencies did not change
            hook = hooks[h_index]

            def cancel():
                if hook.task is not None:
                    hook.task.cancel()
                else:
                    hook.queue.clear()

            return cancel
