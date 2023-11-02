from collections.abc import Callable, Coroutine, Iterator, Iterable
import contextlib
import inspect
import typing as tp
from typing_extensions import Self
import threading

_CommandType = tp.Tuple[Callable[..., None], ...]
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
    In these cases, you might need to issue imperative commands to the underlying widgets and components,
    and :class:`Reference` gives you a handle to the currently rendered :class:`Element`.

    Consider the following code::

        class MyComp(Element):
            def __init__(self):
                self.ref = None

            def issue_command(self, e):
                self.ref.issue_command()

            def render(self):
                self.ref = AnotherElement(on_click=self.issue_command)
                return self.ref

    This code is **incorrect** since the component returned by render is not necessarily the Element rendered on Screen,
    since the old component (with all its state) will be reused when possible.
    The right way of solving the problem is via references::

        class MyComp(Element):
            def __init__(self):
                self.ref = Reference()

            def issue_command(self, e):
                self.ref().issue_command()

            def render(self):
                return AnotherElement(on_click=self.issue_command).register_ref(self.ref)

    Under the hood, :code:`register_ref` registers the :class:`Reference` object
    to the component returned by the :code:`render` function.
    While rendering, Edifice will examine all requested references and attaches
    them to the correct :class:`Element`.

    Initially, a :class:`Reference` object will point to :code:`None`.
    After the first render, they will point to the rendered :class:`Element`.
    When the rendered component dismounts, the reference will once again
    point to :code:`None`.
    You may assume that :class:`Reference` is valid whenever it is
    not :code:`None`.
    :class:`Reference` will evaluate false if the underlying value is :code:`None`.

    :class:`Reference` can be dereferenced by calling it. An idiomatic way of using references is::

        if ref:
            ref().do_something()

    If you want to access the Qt widget underlying a base component,
    you can use the :code:`underlying` attribute of the component::

        class MyComp(Element):
            def __init__(self):
                self.ref = Reference()

            def did_render(self):
                if self.ref:
                    self.ref().underlying.setText("Hi")

            def render(self):
                return Label("Hi").register_ref(self.ref)
    """

    def __init__(self):
        self._value = None

    def __bool__(self):
        return self._value is not None

    def __hash__(self):
        return id(self)

    def __call__(self):
        return self._value

T = tp.TypeVar("T")

class ControllerProtocol(tp.Protocol):
    def _request_rerender(self, components: Iterable["Element"], kwargs: dict[str, tp.Any]):
        pass


class Tracker:
    children: list["Element"]
    def __init__(self, component: "Element"):
        self.component = component
        self.children = []

    def append_child(self, component: "Element"):
        self.children.append(component)

    def collect(self) -> list["Element"]:
        children = set()
        for child in self.children:
            children |= find_components(child) - {child}
        return [child for child in self.children if child not in children]

class RenderContextProtocol(tp.Protocol):
    trackers: list[Tracker]
    def use_state(self, initial_state:_T_use_state) -> tuple[_T_use_state, Callable[[_T_use_state], None]]:
        ...
    def use_effect(
        self,
        setup: Callable[[], Callable[[], None]],
        dependencies: tp.Any,
    ) -> None:
        ...
    def use_async(
        self,
        fn_coroutine: Callable[[], Coroutine[None, None, None]],
        dependencies: tp.Any,
    ) -> None:
        ...

local_state = threading.local()

def get_render_context() -> RenderContextProtocol:
    return getattr(local_state, "render_context")

def get_render_context_maybe() -> RenderContextProtocol | None:
    return getattr(local_state, "render_context", None)

class Element:
    """The base class for Edifice Elements.

    A :class:`Element` is a stateful container wrapping a stateless :code:`render` function.
    Elements have both internal and external properties.

    The external properties, **props**, are passed into the :class:`Element` by another
    :class:`Element`’s render function through the constructor. These values are owned
    by the external caller and should not be modified by this :class:`Element`.
    They may be accessed via the field props :code:`self.props`, which is a :class:`PropsDict`.
    A :class:`PropsDict` allows iteration, get item ( :code:`self.props["value"]` ), and get attribute
    ( :code:`self.props.value` ), but not set item or set attribute. This limitation
    is set to protect the user from accidentally modifying props, which may cause
    bugs. (Note though that a mutable prop, e.g. a list, can still be modified;
    be careful not to do so)

    The internal properties, the **state**, belong to this Element, and may be
    used to keep track of internal state. You may set the state as
    attributes of the :class:`Element` object, for instance :code:`self.my_state`.
    You can initialize the state as usual in the constructor
    (e.g. :code:`self.my_state = {"a": 1}` ),
    and the state persists so long as the :class:`Element` is still mounted.

    In most cases, changes in state would ideally trigger a rerender.
    There are two ways to ensure this.
    First, you may use the set_state function to set the state::

        self.set_state(mystate=1, myotherstate=2)

    You may also use the self.render_changes() context manager::

        with self.render_changes():
            self.mystate = 1
            self.myotherstate = 2

    When the context manager exits, a state change will be triggered.
    The :code:`render_changes()` context manager also ensures that all state changes
    happen atomically: if an exception occurs inside the context manager,
    all changes will be unwound. This helps ensure consistency in the
    :class:`Element`’s state.

    Note if you set :class:`self.mystate = 1` outside
    the :code:`render_changes()` context manager,
    this change will not trigger a re-render. This might be occasionally useful
    but usually is unintended.

    The main function of :class:`Element` is :code:`render`, which should return the subcomponents
    of this component. These may be your own higher-level components as well as
    the core :class:`Element` s, such as
    :class:`Label`, :class:`Button`, and :class:`View`.
    :class:`Element` s may be composed in a tree like fashion:
    one special prop is children, which will always be defined (defaults to an
    empty list).
    To better enable the visualization of the tree-structure of a :class:`Element`
    in the code,
    the :code:`call` method of a :class:`Element` has been overriden to set the arguments
    of the call as children of the component.
    This allows you to write tree-like code remniscent of HTML::

        View(layout="column")(
            View(layout="row")(
                Label("Username: "),
                TextInput()
            ),
            View(layout="row")(
                Label("Email: "),
                TextInput()
            ),
        )

    The :code:`render` function is called when
    :code:`self.should_update(newprops, newstate)`
    returns :code:`True`. This function is called when the props change (as set by the
    render function of this component) or when the state changes (when
    using :code:`set_state` or :code:`render_changes()`). By default, all changes
    in :code:`newprops`
    and :code:`newstate` will trigger a re-render.

    When the component is rendered,
    the :code:`render` function is called. This output is then compared against the output
    of the previous render (if that exists). The two renders are diffed,
    and on certain conditions, the :class:`Element` objects from the previous render
    are maintained and updated with new props.

    Two :class:`Element` s belonging to different classes will always be re-rendered,
    and :class:`Element` s belonging to the same class are assumed to be the same
    and thus maintained (preserving the old state).

    When comparing a list of :class:`Element` s, the :class:`Element`’s
    :code:`_key` attribute will
    be compared. :class:`Element` s with the same :code:`_key` and same class are assumed to be
    the same. You can set the key using the :code:`set_key` method, which returns the component
    to allow for chaining::

        View(layout="row")(
            MyElement("Hello").set_key("hello"),
            MyElement("World").set_key("world"),
        )

    If the :code:`_key` is not provided, the diff algorithm will assign automatic keys
    based on index, which could result in subpar performance due to unnecessary rerenders.
    To ensure control over the rerender process, it is recommended to :code:`set_key`
    whenever you have a list of children.
    """

    _render_changes_context: dict | None = None
    _render_unwind_context: dict | None = None
    _ignored_variables: set[tp.Text] | None = None
    _edifice_internal_parent: tp.Optional["Element"] = None
    _controller: ControllerProtocol | None = None
    _edifice_internal_references: set[Reference] | None = None
    _hook_state_index: int = 0
    """use_state hook index for current render."""
    _hook_effect_index: int = 0
    """use_effect hook index for current render."""
    _hook_async_index: int = 0
    """use_async hook index for current render."""

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

    def __enter__(self: Self) -> Self:
        ctx = get_render_context()
        tracker = Tracker(self)
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

    def register_props(self, props: tp.Mapping[tp.Text, tp.Any]) -> None:
        """Register props.

        Call this function if you do not use the
        :func:`register_props <edifice.register_props>` decorator and you have
        props to register.

        Args:
            props: a dictionary representing the props to register.
        """
        if not hasattr(self, "_props"):
            self._props = {"children": []}
        self._props.update(props)

    def set_key(self: Self, key: tp.Text) -> Self:
        """Sets the key of the component.

        The key is used by the re-rendering logic to match a new list of components
        with an existing list of components.
        The algorithm will assume that components with the same key are logically the same.
        If the key is not provided, the list index will be used as the key;
        however, providing the key may provide more accurate results, leading to efficiency gains.

        Example::

            # inside a render call
            with edifice.View():
                edifice.Label("Hello").set_key("en")
                edifice.Label("Bonjour").set_key("fr")
                edifice.Label("Hola").set_key("es")

        Args:
            key: the key to label the component with
        Returns:
            The component itself.
        """
        self._key = key
        return self

    def register_ref(self: Self, reference: Reference) -> Self:
        """Registers provided reference to this component.

        During render, the provided reference will be set to point to the currently rendered instance of this component
        (i.e. if another instance of the Element is rendered and the RenderEngine decides to reconcile the existing
        and current instances, the reference will eventually point to that previously existing Element.

        Args:
            reference: the Reference to register
        Returns:
            The component itself.
        """
        assert self._edifice_internal_references is not None
        self._edifice_internal_references.add(reference)
        return self

    @property
    def children(self) -> list["Element"]:
        """The children of this component."""
        return self._props["children"]

    @property
    def props(self) -> PropsDict:
        """The props of this component."""
        return PropsDict(self._props)

    @contextlib.contextmanager
    def render_changes(self, ignored_variables: tp.Optional[tp.Sequence[tp.Text]] = None) -> Iterator[None]:
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
                    self.set_state(**changes_context)

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

    def set_state(self, **kwargs):
        """Set state and render changes.

        The keywords are the names of the state attributes of the class, e.g.
        for the state :code:`self.mystate`, you call :code:`set_state(mystate=2)`.

        At the end of this call, all changes will be rendered.
        All changes are guaranteed to appear atomically: upon exception,
        no changes to state will occur.
        """
        should_update = self.should_update(PropsDict({}), kwargs)
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

    def should_update(self, newprops: PropsDict, newstate: tp.Mapping[tp.Text, tp.Any]) -> bool:
        """Determines if the component should rerender upon receiving new props and state.

        The arguments, :code:`newprops` and :code:`newstate`, reflect the
        props and state that change: they
        may be a subset of the props and the state. When this function is called,
        all props and state of this Element are the old values, so you can compare
        :code:`self.props` to :code:`newprops` and :code`self` to :code:`newstate`
        to determine changes.

        By default, this function returns :code:`True`, even if props and state are unchanged.

        Args:
            newprops: the new set of props
            newstate: the new set of state
        Returns:
            Whether or not the Element should be rerendered.
        """
        del newprops, newstate
        return True

    def did_mount(self):
        """Callback function that is called when the component mounts for the first time.

        Override if you need to do something after the component mounts
        (e.g. start a timer).
        """

    def did_update(self):
        """Callback function that is called whenever the component updates.

        *This is not called after the first render.*
        Override if you need to do something after every render except the first.
        """

    def did_render(self):
        """Callback function that is called whenever the component renders.

        It will be called on both renders and updates.
        Override if you need to do something after every render.
        """

    def will_unmount(self):
        """Callback function that is called when the component will unmount.

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

    def render(self) -> tp.Optional["Element"]:
        """Logic for rendering, must be overridden.

        The render logic for this component, not implemented for this abstract class.
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

# TODO: Should we really allow the function to return `Any`?
def component(f: Callable[tp.Concatenate[C,P], None]) -> Callable[P,Element]:
    """Decorator turning a render function into a :class:`Element`.

    Some components do not have internal state, and these components are often little more than
    a :code:`render` function. Creating a :class:`Element` class results in a lot of boiler plate code::

        class MySimpleComp(Element):
            def __init__(self, prop1, prop2, prop3):
                self.register_props({
                    "prop1": prop1,
                    "prop2": prop2,
                    "prop3": prop3,
                })
                super().__init__()

            def render(self):
                # Only here is there actual logic.

    To cut down on the amount of boilerplate, you can use the
    :doc:`component <edifice.component>` decorator::

        @component
        def MySimpleComp(self, prop1, prop2, prop3, children):
            # Here you put what you'd normally put in the render logic
            # Note that you can access prop1 via the variable, or via self.props
            return View()(Label(prop1), Label(self.prop2), Label(prop3))

    Of course, you could have written::

        # No decorator
        def MySimpleComp(prop1, prop2, prop3):
            return View()(Label(prop1), Label(self.prop2), Label(prop3))

    instead. The difference is, with the decorator, an actual :class:`Element` object is created,
    which can be viewed, for example, in the inspector. Moreover, you need a :class:`Element` to
    be able to use hooks such as use_state, since those are bound to containing :class:`Element`.

    If this component uses :doc:`State Values or State Managers</state>`,
    only this component and (possibly) its children will be re-rendered.
    If you don't use the decorator, the returned components are directly attached to the
    Element that called the function, and so any re-renders will have to start from that level.

    Args:
        f: the function to wrap. Its first argument must be self.
    Returns:
        Element class.
    """
    varnames = f.__code__.co_varnames[1:]
    signature = inspect.signature(f).parameters
    defaults = {
        k: v.default
        for k, v in signature.items()
        if v.default is not inspect.Parameter.empty and k[0] != "_"
    }

    class MyElement(Element):

        def __init__(self, *args: P.args, **kwargs: P.kwargs):
            name_to_val = defaults.copy()
            name_to_val.update(filter(not_ignored, zip(varnames, args, strict=False)))
            name_to_val.update(((k, v) for (k, v) in kwargs.items() if k[0] != "_"))
            name_to_val["children"] = name_to_val.get("children") or []
            self.register_props(name_to_val)
            super().__init__()

        def render(self):
            props: dict[str, tp.Any] = self.props._d
            params = props.copy()
            if "children" not in varnames:
                del params["children"]
            # We cannot type this because PropsDict forgets the types
            # call the render function
            f(self, **params) # type: ignore[reportGeneralTypeIssues]

        def __repr__(self):
            return f.__name__
    MyElement.__name__ = f.__name__
    return MyElement

def find_components(el: Element | list[Element]) -> set[Element]:
    match el:
        case Element():
            return {el}
        case list():
            elements = set()
            for child in el:
                elements |= find_components(child)
            return elements

@component
def Container(self):
    pass

class BaseElement(Element):
    """Base Element, whose rendering is defined by the backend."""

class WidgetElement(BaseElement):
    pass

class LayoutElement(BaseElement):
    pass


class RootElement(BaseElement):
    """
    The root component of a component tree must be an instance of RootComponent.
    """
    def _qt_update_commands(self, children, newprops, newstate) -> list[_CommandType]:
        del children, newprops, newstate
        return []
