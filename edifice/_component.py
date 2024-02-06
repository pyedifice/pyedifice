from collections.abc import Callable, Coroutine, Iterator, Iterable
import contextlib
import inspect
import typing as tp
from typing_extensions import Self
import threading
from functools import wraps

P = tp.ParamSpec("P")

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
        self._value = None

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
    _ignored_variables: set[tp.Text] | None = None
    _edifice_internal_parent: tp.Optional["Element"] = None
    # TODO Delete _edifice_internal_parent
    _controller: ControllerProtocol | None = None
    _edifice_internal_references: set[Reference] | None = None

    def __init__(self):
        super().__setattr__("_ignored_variables", set())
        super().__setattr__("_edifice_internal_references", set())
        if not hasattr(self, "_props"):
            self._props = {"children": []}
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
        if not hasattr(self, "_props"):
            self._props = {"children": []}
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

    @contextlib.contextmanager
    def _render_changes(self, ignored_variables: tp.Optional[tp.Sequence[tp.Text]] = None) -> Iterator[None]:
        """Context manager for managing changes to state.

        This context manager does two things:

        - Make a group of assignments to state atomically: if an exception occurs,
          all changes will be rolled back.
        - Renders changes to the state upon successful completion.

        Note that this context manager will not keep track of changes to mutable objects.

        Args:
            ignored_variables: an optional sequence of variables for the manager to ignore.
                               These changes will not be reverted upon exception.
        """
        entered = False
        ignored: set[tp.Text] = set(ignored_variables) if ignored_variables else set()
        exception_raised = False
        if self._render_changes_context is None:
            super().__setattr__("_render_changes_context", {})
            super().__setattr__("_render_unwind_context", {})
            super().__setattr__("_ignored_variables", ignored)
            entered = True
        try:
            yield
        except Exception as e:
            exception_raised = True
            raise e
        finally:
            if entered:
                changes_context = self._render_changes_context
                unwind_context = self._render_unwind_context
                assert changes_context is not None
                assert unwind_context is not None
                super().__setattr__("_render_changes_context", None)
                super().__setattr__("_render_unwind_context", None)
                super().__setattr__("_ignored_variables", set())
                for k, v in unwind_context.items():
                    super().__setattr__(k, v)
                if not exception_raised:
                    self._set_state(**changes_context)

    def __setattr__(self, k, v) -> None:
        changes_context = self._render_changes_context
        ignored_variables = self._ignored_variables
        if changes_context is not None and k not in ignored_variables:
            unwind_context = self._render_unwind_context
            assert unwind_context is not None
            if k not in unwind_context:
                unwind_context[k] = super().__getattribute__(k)
            changes_context[k] = v
        super().__setattr__(k, v)

    def _set_state(self, **kwargs):
        """Set state and render changes.

        The keywords are the names of the state attributes of the class, e.g.
        for the state :code:`self.mystate`, you call :code:`set_state(mystate=2)`.

        At the end of this call, all changes will be rendered.
        All changes are guaranteed to appear atomically: upon exception,
        no changes to state will occur.
        """
        should_update = self._should_update(PropsDict({}), kwargs)
        old_vals = {}
        try:
            for s in kwargs:
                if not hasattr(self, s):
                    raise KeyError
                old_val = super().__getattribute__(s)
                old_vals[s] = old_val
                super().__setattr__(s, kwargs[s])
            if should_update:
                assert self._controller is not None
                self._controller._request_rerender([self], kwargs)
        except Exception as e:
            for s in old_vals:
                super().__setattr__(s, old_vals[s])
            raise e

    def _should_update(self, newprops: PropsDict, newstate: tp.Mapping[tp.Text, tp.Any]) -> bool:
        """Determines if the Element should rerender upon receiving new props and state.

        The arguments, :code:`newprops` and :code:`newstate`, reflect the
        props and state that change: they
        may be a subset of the props and the state. When this function is called,
        all props and state of this Element are the old values, so you can compare
        :code:`self.props` to :code:`newprops` and :code`self` to :code:`newstate`
        to determine changes.

        Args:
            newprops: the new set of props
            newstate: the new set of state
        Returns:
            Whether or not the Element should be rerendered.
        """

        for k,v in newprops._items:
            if k in self.props:
            # If the prop is in the old props, then we check if it's changed.
                v2 = self.props._get(k)
                if v2 != v:
                    return True
            else:
            # If the prop is not in the old props, then we rerender.
                return True


        # for backward compatibility, we have to check for changes to state.
        for k,v in newstate.items():
            v2 = getattr(self, k, None)
            if v2 is None or v2 != v:
                return True

        return False

    def _did_mount(self):
        pass
        """Callback function that is called when the Element mounts for the first time.

        Override if you need to do something after the Element mounts
        (e.g. start a timer).
        """

    def _did_update(self):
        pass
        """Callback function that is called whenever the Element updates.

        *This is not called after the first render.*
        Override if you need to do something after every render except the first.
        """

    def _did_render(self):
        pass
        """Callback function that is called whenever the Element renders.

        It will be called on both renders and updates.
        Override if you need to do something after every render.
        """

    def _will_unmount(self):
        pass
        """Callback function that is called when the Element will unmount.

        Override if you need to clean up some state, e.g. stop a timer,
        close a file.
        """

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

    The compoment will be re-rendered when its **props** are not :code:`__eq__`
    to the **props** from the last time the component rendered.

    In the component function, declare a tree of other :class:`Element`::

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
    be able to use hooks such as :func:`use_state`, since those are bound to an :class:`Element`.

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
            name_to_val = defaults.copy()
            name_to_val.update(filter(not_ignored, zip(varnames, args, strict=False)))
            name_to_val.update(((k, v) for (k, v) in kwargs.items() if k[0] != "_"))
            name_to_val["children"] = name_to_val.get("children") or []
            self._register_props(name_to_val)
            super().__init__()

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
