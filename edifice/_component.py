from collections.abc import Iterator
import contextlib
import functools
import inspect
import typing as tp


class PropsDict(object):
    """An immutable dictionary for storing props.

    Props may be accessed either by indexing (props["myprop"]) or by
    attribute (props.myprop).

    By convention, all PropsDict methods will start with _ to
    not conflict with keys.

    .. document private functions
    .. autoproperty:: _keys
    .. autoproperty:: _items
    """
    __slots__ = ("_d",)

    def __init__(self, dictionary: tp.Mapping[tp.Text, tp.Any]):
        super().__setattr__("_d", dictionary)

    def __getitem__(self, key):
        return self._d[key]

    def __setitem__(self, key, value):
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

    def __len__(self):
        return len(self._d)

    def __iter__(self):
        return iter(self._d)

    def __contains__(self, k):
        return k in self._d

    def __getattr__(self, key):
        if key in self._d:
            return self._d[key]
        raise KeyError("%s not in props" % key)

    def __repr__(self):
        return "PropsDict(%s)" % repr(self._d)

    def __str__(self):
        return "PropsDict(%s)" % str(self._d)

    def __setattr__(self, key, value):
        raise ValueError("Props are immutable")


class Reference(object):
    """Reference to a Component to allow imperative modifications.

    While Edifice is a declarative library and tries to abstract away the need to issue
    imperative commands to widgets,
    this is not always possible, either due to limitations with the underlying backened,
    or because some feature implemented by the backend is not yet supported by the declarative layer.
    In these cases, you might need to issue imperative commands to the underlying widgets and components,
    and References gives you a handle to the currently rendered Component.

    Consider the following code::

        class MyComp(Component):
            def __init__(self):
                self.ref = None

            def issue_command(self, e):
                self.ref.issue_command()

            def render(self):
                self.ref = AnotherComponent(on_click=self.issue_command)
                return self.ref

    This code is **incorrect** since the component returned by render is not necessarily the Component rendered on Screen,
    since the old component (with all its state) will be reused when possible.
    The right way of solving the problem is via references::

        class MyComp(Component):
            def __init__(self):
                self.ref = Reference()

            def issue_command(self, e):
                self.ref().issue_command()

            def render(self):
                return AnotherComponent(on_click=self.issue_command).register_ref(self.ref)

    Under the hood, register_ref registers the Reference object to the component returned by the render function.
    While rendering, Edifice will examine all requested references and attaches them to the correct Component.

    Initially, a Reference object will point to None. After the first render, they will point to the rendered Component.
    When the rendered component dismounts, the reference will once again point to None.
    You may assume that References are valid whenever they are not None.
    References evaluate false if the underlying value is None.

    References can be dereferenced by calling them. An idiomatic way of using references is::

        if ref:
            ref().do_something()

    If you want to access the Qt widget underlying a base component,
    you can use the :code:`underlying` attribute of the component::

        class MyComp(Component):
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


class Component(object):
    """The base class for Edifice Components.

    A Component is a stateful container wrapping a stateless render function.
    Components have both internal and external properties.

    The external properties, **props**, are passed into the Component by another
    Component's render function through the constructor. These values are owned
    by the external caller and should not be modified by this Component.
    They may be accessed via the field props (self.props), which is a PropsDict.
    A PropsDict allows iteration, get item (self.props["value"]), and get attribute
    (self.props.value), but not set item or set attribute. This limitation
    is set to protect the user from accidentally modifying props, which may cause
    bugs. (Note though that a mutable prop, e.g. a list, can still be modified;
    be careful not to do so)

    The internal properties, the **state**, belong to this Component, and may be
    used to keep track of internal state. You may set the state as
    attributes of the Component object, for instance self.my_state.
    You can initialize the state as usual in the constructor (e.g. self.my_state = {"a": 1}),
    and the state persists so long as the Component is still mounted.

    In most cases, changes in state would ideally trigger a rerender.
    There are two ways to ensure this.
    First, you may use the set_state function to set the state::

        self.set_state(mystate=1, myotherstate=2)

    You may also use the self.render_changes() context manager::

        with self.render_changes():
            self.mystate = 1
            self.myotherstate = 2

    When the context manager exits, a state change will be triggered.
    The render_changes() context manager also ensures that all state changes
    happen atomically: if an exception occurs inside the context manager,
    all changes will be unwound. This helps ensure consistency in the
    Component's state.

    Note if you set self.mystate = 1 outside the render_changes() context manager,
    this change will not trigger a re-render. This might be occasionally useful
    but usually is unintended.

    The main function of Component is render, which should return the subcomponents
    of this component. These may be your own higher-level components as well as
    the core Components, such as Label, Button, and View.
    Components may be composed in a tree like fashion:
    one special prop is children, which will always be defined (defaults to an
    empty list).
    To better enable the visualization of the tree-structure of a Component
    in the code,
    the call method of a Component has been overriden to set the arguments
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

    The render function is called when self.should_update(newprops, newstate)
    returns True. This function is called when the props change (as set by the
    render function of this component) or when the state changes (when
    using set_state or render_changes()). By default, all changes in newprops
    and newstate will trigger a re-render.

    When the component is rendered,
    the render function is called. This output is then compared against the output
    of the previous render (if that exists). The two renders are diffed,
    and on certain conditions, the Component objects from the previous render
    are maintained and updated with new props.

    Two Components belonging to different classes will always be re-rendered,
    and Components belonging to the same class are assumed to be the same
    and thus maintained (preserving the old state).

    When comparing a list of Components, the Component's **_key** attribute will
    be compared. Components with the same _key and same class are assumed to be
    the same. You can set the key using the set_key method, which returns the component
    to allow for chaining::

        View(layout="row")(
            MyComponent("Hello").set_key("hello"),
            MyComponent("World").set_key("world"),
        )

    If the _key is not provided, the diff algorithm will assign automatic keys
    based on index, which could result in subpar performance due to unnecessary rerenders.
    To ensure control over the rerender process, it is recommended to set_keys
    whenever you have a list of children.
    """

    _render_changes_context = None
    _render_unwind_context = None
    _ignored_variables = set()
    _edifice_internal_parent = None
    _controller = None
    _edifice_internal_references = None

    def __init__(self):
        super().__setattr__("_ignored_variables", set())
        super().__setattr__("_edifice_internal_references", set())
        if not hasattr(self, "_props"):
            self._props = {"children": []}

    def register_props(self, props: tp.Mapping[tp.Text, tp.Any]):
        """Register props.

        Call this function if you do not use the register_props decorator and you have
        props to register.

        Args:
            props: a dictionary representing the props to register.
        """
        if not hasattr(self, "_props"):
            self._props = {"children": []}
        self._props.update(props)

    def set_key(self, key: tp.Text):
        """Sets the key of the component.

        The key is used by the re-rendering logic to match a new list of components
        with an existing list of components.
        The algorithm will assume that components with the same key are logically the same.
        If the key is not provided, the list index will be used as the key;
        however, providing the key may provide more accurate results, leading to efficiency gains.

        Example::

            # inside a render call
            return edifice.View()(
                edifice.Label("Hello").set_key("en"),
                edifice.Label("Bonjour").set_key("fr"),
                edifice.Label("Hola").set_key("es"),
            )

        Args:
            key: the key to label the component with
        Returns:
            The component itself.
        """
        self._key = key
        return self

    def register_ref(self, reference: Reference):
        """Registers provided reference to this component.

        During render, the provided reference will be set to point to the currently rendered instance of this component
        (i.e. if another instance of the Component is rendered and the RenderEngine decides to reconcile the existing
        and current instances, the reference will eventually point to that previously existing Component.

        Args:
            reference: the Reference to register
        Returns:
            The component itself.
        """
        self._edifice_internal_references.add(reference)
        return self

    @property
    def children(self):
        """The children of this component."""
        return self._props["children"]

    @property
    def props(self) -> PropsDict:
        """The props of this component."""
        return PropsDict(self._props)

    @contextlib.contextmanager
    def render_changes(self, ignored_variables: tp.Optional[tp.Sequence[tp.Text]] = None):
        """Context manager for managing changes to state.

        This context manager provides two functions:
        - Make a group of assignments to state atomically: if an exception occurs,
        all changes will be rolled back.
        - Renders changes to the state upon successful completion.

        Note that this context manager will not keep track of changes to mutable objects.

        Args:
            ignored_variables: an optional sequence of variables for the manager to ignore.
                               These changes will not be reverted upon exception.
        """
        entered = False
        ignored_variables = ignored_variables or set()
        ignored_variables = set(ignored_variables)
        exception_raised = False
        if self._render_changes_context is None:
            super().__setattr__("_render_changes_context", {})
            super().__setattr__("_render_unwind_context", {})
            super().__setattr__("_ignored_variables", ignored_variables)
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
                super().__setattr__("_render_changes_context", None)
                super().__setattr__("_render_unwind_context", None)
                super().__setattr__("_ignored_variables", set())
                for k, v in unwind_context.items():
                    super().__setattr__(k, v)
                if not exception_raised:
                    self.set_state(**changes_context)

    def __setattr__(self, k, v):
        changes_context = self._render_changes_context
        ignored_variables = self._ignored_variables
        if changes_context is not None and k not in ignored_variables:
            unwind_context = self._render_unwind_context
            if k not in unwind_context:
                unwind_context[k] = super().__getattribute__(k)
            changes_context[k] = v
        super().__setattr__(k, v)

    def set_state(self, **kwargs):
        """Set state and render changes.

        The keywords are the names of the state attributes of the class, e.g.
        for the state self.mystate, you call set_state with set_state(mystate=2).
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
                self._controller._request_rerender([self], kwargs)
        except Exception as e:
            for s in old_vals:
                super().__setattr__(s, old_vals[s])
            raise e

    def should_update(self, newprops: PropsDict, newstate: tp.Mapping[tp.Text, tp.Any]) -> bool:
        """Determines if the component should rerender upon receiving new props and state.

        The arguments, newprops and newstate, reflect the props and state that change: they
        may be a subset of the props and the state. When this function is called,
        all props and state of this Component are the old values, so you can compare
        `component.props` and `newprops` to determine changes.

        By default, this function returns true, even if props and state are unchanged.

        Args:
            newprops: the new set of props
            newstate: the new set of state
        Returns:
            Whether or not the Component should be rerendered.
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

    def render(self):
        """Logic for rendering, must be overridden.

        The render logic for this component, not implemented for this abstract class.
        The render function itself should be purely stateless, because the application
        state should not depend on whether or not the render function is called.

        Args:
            None
        Returns:
            A Component object.
        """
        raise NotImplementedError


def make_component(f):
    """Decorator turning a render function into a Component.

    Some components do not have internal state, and these components are often little more than
    a render function. Creating a Component class results in a lot of boiler plate code::

        class MySimpleComp(Component):
            @register_props
            def __init__(self, prop1, prop2, prop3):
                super().__init__()

            def render(self):
                # Only here is there actual logic.

    To cut down on the amount of boilerplate, you can use the make_component decorator::

        @make_component
        def MySimpleComp(self, prop1, prop2, prop3, children):
            # Here you put what you'd normally put in the render logic
            # Note that you can access prop1 via the variable, or via self.props
            return View()(Label(prop1), Label(self.prop2), Label(prop3))

    Of course, you could have written::

        # No decorator
        def MySimpleComp(prop1, prop2, prop3):
            return View()(Label(prop1), Label(self.prop2), Label(prop3))

    instead. The difference is, with the decorator, an actual Component object is created,
    which can be viewed, for example, in the inspector.
    If this component uses :doc:`State Values or State Managers</state>`,
    only this component and (possibly) its children will be re-rendered.
    If you don't use the decorator, the returned components are directly attached to the
    Component that called the function, and so any re-renders will have to start from that level.

    Args:
        f: the function to wrap. Its first argument must be self, and children must be one of its parameters.
    Returns:
        Component class.
    """
    varnames = f.__code__.co_varnames[1:]
    signature = inspect.signature(f).parameters
    defaults = {
        k: v.default for k, v in signature.items() if v.default is not inspect.Parameter.empty and k[0] != "_"
    }
    if "children" not in signature:
        raise ValueError("All function components must take children as last argument.")

    class MyComponent(Component):

        def __init__(self, *args, **kwargs):
            name_to_val = defaults.copy()
            name_to_val.update(filter((lambda tup: (tup[0][0] != "_")), zip(varnames, args)))
            name_to_val.update(((k, v) for (k, v) in kwargs.items() if k[0] != "_"))
            name_to_val["children"] = name_to_val.get("children") or []
            self.register_props(name_to_val)
            super().__init__()

        def render(self):
            return f(self, **self.props._d)
    MyComponent.__name__ = f.__name__
    return MyComponent


def register_props(f):
    """Decorator for Component __init__ method to record props.

    This decorator will record all arguments (both vector and keyword arguments)
    of the __init__ function as belonging to the props of the component.
    It will call Component.register_props to store these arguments in the
    props field of the Component.

    Arguments that begin with an underscore will be ignored.

    Example::

        class MyComponent(Component):

            @register_props
            def __init__(self, a, b=2, c="xyz", _d=None):
                pass

            def render(self):
                return View()(
                    Label(self.props.a),
                    Label(self.props.b),
                    Label(self.props.c),
                )

    MyComponent(5, c="w") will then have props.a=5, props.b=2, and props.c="w".
    props._d is undefined

    Args:
        f: the __init__ function of a Component subclass
    Returns:
        decorated function

    """
    varnames = f.__code__.co_varnames[1:]
    signature = inspect.signature(f).parameters
    defaults = {
        k: v.default for k, v in signature.items() if v.default is not inspect.Parameter.empty and k[0] != "_"
    }

    @functools.wraps(f)
    def func(self, *args, **kwargs):
        name_to_val = defaults.copy()
        name_to_val.update(filter((lambda tup: (tup[0][0] != "_")), zip(varnames, args)))
        name_to_val.update(((k, v) for (k, v) in kwargs.items() if k[0] != "_"))
        self.register_props(name_to_val)
        Component.__init__(self)
        f(self, *args, **kwargs)

    return func


class BaseComponent(Component):
    """Base Component, whose rendering is defined by the backend."""

class WidgetComponent(BaseComponent):
    pass

class LayoutComponent(BaseComponent):
    pass

class RootComponent(BaseComponent):

    def _qt_update_commands(self, children, newprops, newstate):
        del children, newprops, newstate
        return []
