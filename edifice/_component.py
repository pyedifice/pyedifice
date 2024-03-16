from collections.abc import Callable, Coroutine, Iterator, Iterable
import contextlib
import inspect
import functools
import logging
import asyncio
import typing as tp
from typing_extensions import Self
import threading
from functools import wraps

from .qt import QT_VERSION
if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtCore, QtWidgets, QtGui
else:
    from PySide6 import QtCore, QtWidgets, QtGui

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

class _CommandType:
    def __init__(self, fn: Callable[P, tp.Any], *args: P.args, **kwargs: P.kwargs):
        # The return value of fn is ignored and should thus return None. However, in
        # order to test with equality on the _CommandTypes we need to allow fn to return
        # Any value to not allocate wrapper functions ignoring the return value.
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return f"{self.fn}(*{self.args},**{self.kwargs})"

    def __repr__(self):
        return f"{self.fn.__repr__()}(*{self.args.__repr__()},**{self.kwargs.__repr__()})"

    def __eq__(self, other):
        if not isinstance(other, _CommandType):
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

class RenderContextProtocol(tp.Protocol):
    """
    Protocol for _RenderContext. TODO rearrange modules so we don't need this protocol.
    """
    trackers: list[_Tracker]
    def use_state(self, initial_state:_T_use_state) -> tuple[
        _T_use_state, # current value
        tp.Callable[ # updater
            [_T_use_state | tp.Callable[[_T_use_state],_T_use_state]],
            None
        ]]:
        ...
    def use_effect(
        self,
        setup: Callable[[], Callable[[], None] | None],
        dependencies: tp.Any,
    ) -> None:
        ...
    def use_async(
        self,
        fn_coroutine: Callable[[], Coroutine[None, None, None]],
        dependencies: tp.Any,
    ) -> Callable[[],None]:
        ...

local_state = threading.local()

def get_render_context() -> RenderContextProtocol:
    return getattr(local_state, "render_context")

def get_render_context_maybe() -> RenderContextProtocol | None:
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

        for k,v in newprops._items:
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
            f"<{classname} id=0x%x %s>" % (
                id(self),
                " ".join("%s=%s" % (p, val) for (p, val) in self.props._items if p != "children")),
            "</%s>" % (classname),
            f"<{classname} id=0x%x %s />" % (
                id(self),
                " ".join("%s=%s" % (p, val) for (p, val) in self.props._items if p != "children")),
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

def component(f: Callable[tp.Concatenate[C,P], None]) -> Callable[P,Element]:
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
    defaults = {
        k: v.default
        for k, v in signature.items()
        if v.default is not inspect.Parameter.empty and k[0] != "_"
    }

    class ComponentElement(Element):

        @wraps(f)
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
            f(self, **params) # type: ignore[reportGeneralTypeIssues]

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
        on_drop: tp.Optional[tp.Callable[[QtGui.QDragEnterEvent | QtGui.QDragMoveEvent | QtGui.QDragLeaveEvent | QtGui.QDropEvent], None]] = None,
    ):
        super().__init__()
        self._register_props({
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
        })
        self._height = 0
        self._width = 0
        self._top = 0
        self._left = 0
        self._size_from_font = None # TODO _size_from_font is unused
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
        self._on_drop: tp.Optional[tp.Callable[[QtGui.QDragEnterEvent | QtGui.QDragMoveEvent | QtGui.QDragLeaveEvent | QtGui.QDropEvent], None]] = None
        self._default_mouse_press_event = None
        self._default_mouse_release_event = None
        self._default_mouse_move_event = None
        self._default_mouse_enter_event = None
        self._default_mouse_leave_event = None
        self._default_drag_enter_event = None
        self._default_drag_move_event = None
        self._default_drag_leave_event = None
        self._default_drop_event = None

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

    def _set_on_drop(self, underlying: QtWidgets.QWidget,
        on_drop: tp.Optional[tp.Callable[[QtGui.QDragEnterEvent | QtGui.QDragMoveEvent | QtGui.QDragLeaveEvent | QtGui.QDropEvent], None]]
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
            self.underlying.dragEnterEvent = self._on_drop # type: ignore
            self.underlying.dragMoveEvent = self._on_drop # type: ignore
            self.underlying.dragLeaveEvent = self._on_drop # type: ignore
            self.underlying.dropEvent = self._on_drop # type: ignore
        else:
            self._on_drop = None
            self.underlying.setAcceptDrops(False)

    def _gen_styling_commands(
        self,
        style,
        underlying: QtWidgets.QWidget | None,
        underlying_layout: QtWidgets.QLayout | None = None,
    ):
        commands: list[_CommandType] = []

        if underlying_layout is not None:
            set_margin = False
            new_margin=[0, 0, 0, 0]
            if "margin" in style:
                new_margin = [int(_css_to_number(style["margin"]))] * 4
                style.pop("margin")
                set_margin = True
            if "margin-left" in style:
                new_margin[0] = int(_css_to_number(style["margin-left"]))
                style.pop("margin-left")
                set_margin = True
            if "margin-right" in style:
                new_margin[2] = int(_css_to_number(style["margin-right"]))
                style.pop("margin-right")
                set_margin = True
            if "margin-top" in style:
                new_margin[1] = int(_css_to_number(style["margin-top"]))
                style.pop("margin-top")
                set_margin = True
            if "margin-bottom" in style:
                new_margin[3] = int(_css_to_number(style["margin-bottom"]))
                style.pop("margin-bottom")
                set_margin = True

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

            if set_margin:
                commands.append(_CommandType(underlying_layout.setContentsMargins, new_margin[0], new_margin[1], new_margin[2], new_margin[3]))
            if set_align:
                commands.append(_CommandType(underlying_layout.setAlignment, set_align))
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
            commands.append(_CommandType(self.underlying.move, move_coords[0], move_coords[1]))

        assert self.underlying is not None
        css_string = _dict_to_style(style,  "QWidget#" + str(id(self)))
        commands.append(_CommandType(self.underlying.setStyleSheet, css_string))
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
        newprops : PropsDict,
    ) -> list[_CommandType]:
        raise NotImplementedError

    def _qt_update_commands_super(
        self,
        widget_trees: dict[Element, "_WidgetTree"],
        # We must pass all of the widget_trees because some elements
        # like TableGridView need to know the children of the children.
        newprops : PropsDict,
        underlying: QtWidgets.QWidget,
        underlying_layout: QtWidgets.QLayout | None = None
    ) -> list[_CommandType]:
        commands: list[_CommandType] = []
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
                    commands.append(_CommandType(underlying.setSizePolicy, newprops.size_policy))
            elif prop == "focus_policy":
                if newprops.focus_policy is not None:
                    commands.append(_CommandType(underlying.setFocusPolicy, newprops.focus_policy))
            elif prop == "enabled":
                if newprops.enabled is not None:
                    commands.append(_CommandType(underlying.setEnabled, newprops.enabled))
            elif prop == "on_click":
                commands.append(_CommandType(self._set_on_click, underlying, newprops.on_click))
                if newprops.on_click is not None and self.props.cursor is not None:
                    commands.append(_CommandType(underlying.setCursor, QtCore.Qt.CursorShape.PointingHandCursor))
            elif prop == "on_key_down":
                commands.append(_CommandType(self._set_on_key_down, underlying, newprops.on_key_down))
            elif prop == "on_key_up":
                commands.append(_CommandType(self._set_on_key_up, underlying, newprops.on_key_up))
            elif prop == "on_mouse_down":
                commands.append(_CommandType(self._set_on_mouse_down, underlying, newprops.on_mouse_down))
            elif prop == "on_mouse_up":
                commands.append(_CommandType(self._set_on_mouse_up, underlying, newprops.on_mouse_up))
            elif prop == "on_mouse_enter":
                commands.append(_CommandType(self._set_on_mouse_enter, underlying, newprops.on_mouse_enter))
            elif prop == "on_mouse_leave":
                commands.append(_CommandType(self._set_on_mouse_leave, underlying, newprops.on_mouse_leave))
            elif prop == "on_mouse_move":
                commands.append(_CommandType(self._set_on_mouse_move, underlying, newprops.on_mouse_move))
            elif prop == "on_drop":
                commands.append(_CommandType(self._set_on_drop, underlying, newprops.on_drop))
            elif prop == "tool_tip":
                if newprops.tool_tip is not None:
                    commands.append(_CommandType(underlying.setToolTip, newprops.tool_tip))
            elif prop == "css_class":
                css_class = newprops.css_class
                if css_class is None:
                    css_class = []
                commands.append(_CommandType(underlying.setProperty, "css_class", css_class))
                commands.extend([
                    _CommandType(underlying.style().unpolish, underlying),
                    _CommandType(underlying.style().polish, underlying)
                ])
            elif prop == "cursor":
                cursor = self.props.cursor or ("default" if self.props.on_click is None else "pointer")
                commands.append(_CommandType(underlying.setCursor, _CURSORS[cursor]))
            elif prop == "context_menu":
                if self._context_menu_connected:
                    underlying.customContextMenuRequested.disconnect()
                if self.props.context_menu is not None:
                    commands.append(_CommandType(underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.CustomContextMenu))
                    commands.append(_CommandType(self._set_context_menu, underlying))
                else:
                    commands.append(_CommandType(underlying.setContextMenuPolicy, QtCore.Qt.ContextMenuPolicy.DefaultContextMenu))
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
