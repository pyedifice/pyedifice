"""The Edifice UI library

The two main classes of this module are Component and App.

The Component class is the basic building block of your GUI.
Your components will be composed of other components:
native components (View, Button, Text) as well as other composite
components created by you or others.

The root component should be a WindowManager, whose children are distinct windows.
Creating a new window is as simple as adding a new child to WindowManager.

To display your component, create an App object and call start::

    if __name__ == "__main__":
        App(MyApp()).start()

These native components are supported:
    * Label: A basic text label
    * TextInput: A one-line text input box
    * Button: A clickable button
    * View: A box allowing you to position child components in a row or column
    * ScrollView: A scrollable view
    * List: A list of components with no inherent semantics. This may be
      passed to other Components, e.g. those that require lists of lists.

Some useful utilities are also provided:
    * register_props: A decorator for the __init__ function that records
      all arguments as props
    * set_trace: An analogue of pdb.set_trace that works with Qt
      (pdb.set_trace interrupts the Qt event flow, causing an unpleasant
      debugging experience). Use this set_trace if you want to set breakpoings.
"""

import contextlib
import functools
import inspect
import itertools
import logging
import typing as tp

import numpy as np
import pandas as pd

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtRemoveInputHook, pyqtRestoreInputHook


StyleType = tp.Optional[tp.Mapping[tp.Text, tp.Text]]


class _ChangeManager(object):
    def __init__(self):
        self.changes = []

    def set(self, obj, key, value):
        old_value = None
        if hasattr(obj, key):
            old_value = getattr(obj, key)
        self.changes.append((obj, key, hasattr(obj, key), old_value, value))
        setattr(obj, key, value)

    def unwind(self):
        for obj, key, had_key, old_value, new_value in reversed(self.changes):
            if had_key:
                setattr(obj, key, old_value)
            else:
                try:
                    delattr(obj, key)
                except AttributeError:
                    logging.warning(
                        "Error while unwinding changes: Unable to delete %s from %s. Setting to None instead" % (
                            key, obj.__class__.__name__))
                    setattr(obj, key, None)

@contextlib.contextmanager
def _storage_manager():
    changes = _ChangeManager()
    try:
        yield changes
    except Exception as e:
        changes.unwind()
        raise e


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

    def __init__(self, dictionary: tp.Mapping[tp.Text, tp.Any]):
        super().__setattr__("_d", dictionary)

    def __getitem__(self, key):
        return self._d[key]

    def __setitem__(self, key, value):
        raise ValueError("Props are immutable")

    @property
    def _keys(self) -> tp.List[tp.Text]:
        """Returns the keys of the props dict as a list."""
        return list(self._d.keys())

    @property
    def _items(self) -> tp.List[tp.Any]:
        """Returns the (key, value) of the props dict as a list."""
        return list(self._d.items())

    def __len__(self):
        return len(self._d)

    def __iter__(self):
        return iter(self._d)

    def __contains__(self, k):
        return k in self._d

    def __getattr__(self, key):
        if key in self._d:
            return self._d[key]
        else:
            raise KeyError("%s not in props" % key)

    def __repr__(self):
        return "PropsDict(%s)" % repr(self._d)

    def __str__(self):
        return "PropsDict(%s)" % str(self._d)

    def __setattr__(self, key, value):
        raise ValueError("Props are immutable")


class Component(object):
    """Component.

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
    empty list). The children prop can be set by calling another Component::

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
    _ignored_variables = set()

    def __init__(self):
        super().__setattr__("_ignored_variables", set())
        if not hasattr(self, "_props"):
            self._props = {"children": []}

    def register_props(self, props: tp.Union[tp.Mapping[tp.Text, tp.Any], PropsDict]):
        """Register props.

        Call this function if you do not use the register_props decorator and you have
        props to register.
        """
        if "children" not in props:
            props["children"] = {}
        self._props = props

    def set_key(self, k: tp.Text):
        self._key = k
        return self

    @property
    def children(self):
        return self.props.children

    @property
    def props(self) -> PropsDict:
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
        if super().__getattribute__("_render_changes_context") is None:
            super().__setattr__("_render_changes_context", {})
            super().__setattr__("_ignored_variables", ignored_variables)
            entered = True
        try:
            yield
        except Exception as e:
            exception_raised = True
            raise e
        finally:
            if entered:
                changes_context = super().__getattribute__("_render_changes_context")
                super().__setattr__("_render_changes_context", None)
                super().__setattr__("_ignored_variables", set())
                if not exception_raised:
                    self.set_state(**changes_context)

    def __getattribute__(self, k):
        changes_context = super().__getattribute__("_render_changes_context")
        ignored_variables = super().__getattribute__("_ignored_variables")
        if changes_context is not None and k in changes_context and k not in ignored_variables:
            return changes_context[k]
        return super().__getattribute__(k)


    def __setattr__(self, k, v):
        changes_context = super().__getattribute__("_render_changes_context")
        ignored_variables = super().__getattribute__("_ignored_variables")
        if changes_context is not None and k not in ignored_variables:
            changes_context[k] = v
        else:
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
                self._controller._request_rerender(self, PropsDict({}), kwargs)
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

        By default, all changes to props and state will trigger a re-render. This behavior
        is probably desirable most of the time, but if you want custom re-rendering logic,
        you can override this function.

        Args:
            newprops: the new set of props
            newstate: the new set of state
        Returns:
            Whether or not the Component should be rerendered.
        """
        def should_update_helper(new_obj, old_obj):
            if isinstance(old_obj, Component) or isinstance(new_obj, Component):
                if old_obj.__class__ != new_obj.__class__:
                    return True
                if old_obj.should_update(new_obj.props, {}):
                    return True
            elif isinstance(old_obj, np_classes) or isinstance(new_obj, np_classes):
                if old_obj.__class__ != new_obj.__class__:
                    return True
                if not np.array_equal(old_obj, new_obj):
                    return True
            elif old_obj != new_obj:
                return True
            return False

        np_classes = (np.ndarray, pd.Series, pd.DataFrame, pd.Index)
        for prop, new_obj in newprops._items:
            old_obj = self.props[prop]
            if should_update_helper(new_obj, old_obj):
                return True
        for state, new_obj in newstate.items():
            old_obj = getattr(self, state)
            if should_update_helper(new_obj, old_obj):
                return True
        return False

    def __call__(self, *args):
        children = [a for a in args if a]
        self._props["children"] = children
        return self

    def __hash__(self):
        return id(self)

    def _tags(self):
        classname = self.__class__.__name__
        return [
            "<%s id=0x%x %s>" % (classname, id(self), " ".join("%s=%s" % (p, val) for (p, val) in self.props._items if p != "children")),
            "</%s>" % (classname),
            "<%s id=0x%x %s />" % (classname, id(self), " ".join("%s=%s" % (p, val) for (p, val) in self.props._items if p != "children")),
        ]

    def __str__(self):
        tags = self._tags()
        if self.children:
            return "%s\n\t%s\n%s" % (tags[0], "\t\n".join(str(child) for child in self.children), tags[1])
        return tags[2]

    def render(self):
        """Logic for rendering, must be overridden.

        The render logic for this component, not implemented for this abstract class.
        The render function itself should be purely stateless, because the application
        state should not depend on whether or not the render function is called.
        """
        raise NotImplementedError


def register_props(f):
    """Decorator for __init__ function to record props.

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
    @functools.wraps(f)
    def func(self, *args, **kwargs):
        varnames = f.__code__.co_varnames[1:]
        defaults = {
            k: v.default for k, v in inspect.signature(f).parameters.items() if v.default is not inspect.Parameter.empty and k[0] != "_"
        }
        name_to_val = defaults
        name_to_val.update(dict(filter((lambda tup: (tup[0][0] != "_")), zip(varnames, args))))
        name_to_val.update(dict((k, v) for (k, v) in kwargs.items() if k[0] != "_"))
        self.register_props(name_to_val)
        f(self, *args, **kwargs)

    return func

class BaseComponent(Component):

    def __init__(self):
        super().__init__()

class WidgetComponent(BaseComponent):

    def __init__(self):
        super().__init__()

class LayoutComponent(BaseComponent):

    def __init__(self):
        super().__init__()


class WindowManager(BaseComponent):
    """Window manager: the root component.

    The WindowManager should lie at the root of your component Tree.
    The children of WindowManager are each displayed in its own window.
    To create a new window, simply append to the list of children::

        class MyApp(Component):

            @register_props
            def __init__(self):
                self.window_texts = []

            def create_window(self):
                nwindows = len(self.window_texts)
                self.set_state(window_texts=self.window_texts + ["Window %s" % (nwindows + 1)])

            def render(self):
                return WindowManager()(
                    View()(
                        Button(title="Create new window", on_click=self.create_window)
                    ),
                    *[Label(s) for s in self.window_texts]
                )

        if __name__ == "__main__":
            App(MyApp()).start()
    """

    def __init__(self):
        super().__init__()

        self._already_rendered = {}
        self._old_rendered_children = []

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        new_children = set()
        for child in children:
            new_children.add(child.component)

        for child in list(self._already_rendered.keys()):
            if child not in new_children:
                del self._already_rendered[child]

        for i, old_child in reversed(list(enumerate(self._old_rendered_children))):
            if old_child not in new_children:
                commands += [(old_child.underlying.close,)]

        self._old_rendered_children = [child.component for child in children]
        for i, child in enumerate(children):
            if child.component not in self._already_rendered:
                commands += [(child.component.underlying.show,)]
            self._already_rendered[child.component] = True
        return commands


def dict_to_style(d, prefix="QWidget"):
    d = d or {}
    stylesheet = prefix + "{%s}" % (";".join("%s: %s" % (k, v) for (k, v) in d.items()))
    return stylesheet

class Button(WidgetComponent):
    """Basic Button

    Props:
        title: the button text
        style: the styling of the button
        on_click: a function that will be called when the button is clicked
    """

    @register_props
    def __init__(self, title: tp.Any = "", style: StyleType = None, on_click: tp.Callable[[], None]=(lambda: None)):
        super(Button, self).__init__()
        self.underlying =  QtWidgets.QPushButton(str(self.props.title))
        self.underlying.setObjectName(str(id(self)))
        self._connected = False

    def _set_on_click(self, on_click):
        if self._connected:
            self.underlying.clicked.disconnect()
        self.underlying.clicked.connect(on_click)
        self._connected = True

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        for prop in newprops:
            if prop == "title":
                commands.append((self.underlying.setText, str(newprops.title)))
            elif prop == "on_click":
                commands.append((self._set_on_click, newprops.on_click))
            elif prop == "style":
                commands.append((self.underlying.setStyleSheet,
                                 dict_to_style(newprops.style, "QWidget#" + str(id(self)))))
        return commands


class Label(WidgetComponent):

    @register_props
    def __init__(self, text: tp.Any = "", style: StyleType = None):
        super().__init__()
        self.underlying = QtWidgets.QLabel(str(self.props.text))
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        for prop in newprops:
            if prop == "text":
                commands += [(self.underlying.setText, str(newprops[prop]))]
            elif prop == "style":
                commands += [(self.underlying.setStyleSheet, dict_to_style(newprops[prop], "QWidget#" + str(id(self))))]
        return commands


class TextInput(WidgetComponent):

    @register_props
    def __init__(self, text: tp.Any = "", on_change: tp.Callable[[tp.Text], None] = (lambda text: None), style: StyleType = None):
        super().__init__()
        self.current_text = text
        self._connected = False
        self.underlying = QtWidgets.QLineEdit(str(self.props.text))
        self.underlying.setObjectName(str(id(self)))

    def set_on_change(self, on_change):
        def on_change_fun(text):
            self.current_text = text
            return on_change(text)
        if self._connected:
            self.underlying.textChanged[str].disconnect()
        self.underlying.textChanged[str].connect(on_change_fun)
        self._connected = True

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        commands += [(self.underlying.setText, str(self.current_text))]
        for prop in newprops:
            if prop == "on_change":
                commands += [(self.set_on_change, newprops[prop])]
            elif prop == "style":
                commands += [(self.underlying.setStyleSheet, dict_to_style(newprops[prop],  "QWidget#" + str(id(self))))]
        return commands


class View(WidgetComponent):

    @register_props
    def __init__(self, layout: tp.Text = "column", style: StyleType = None):
        super().__init__()

        self._already_rendered = {}
        self._old_rendered_children = []
        self.underlying = QtWidgets.QWidget()
        if layout == "column":
            self.underlying_layout = QtWidgets.QVBoxLayout()
        elif layout == "row":
            self.underlying_layout = QtWidgets.QHBoxLayout()
        self.underlying.setLayout(self.underlying_layout)
        self.underlying.setObjectName(str(id(self)))

    def _delete_child(self, i):
        child_node = self.underlying_layout.takeAt(i)
        if child_node.widget():
            child_node.widget().deleteLater()

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        new_children = set()
        for child in children:
            new_children.add(child.component)

        for child in list(self._already_rendered.keys()):
            if child not in new_children:
                del self._already_rendered[child]

        for i, old_child in reversed(list(enumerate(self._old_rendered_children))):
            if old_child not in new_children:
                commands += [(self._delete_child, i)]

        self._old_rendered_children = [child.component for child in children]
        for i, child in enumerate(children):
            if child.component not in self._already_rendered:
                commands += [(self.underlying_layout.insertWidget, i, child.component.underlying)]
            self._already_rendered[child.component] = True

        for prop in newprops:
            if prop == "style":
                commands += [(self.underlying.setStyleSheet, dict_to_style(newprops[prop],  "QWidget#" + str(id(self))))]
        return commands


class ScrollView(WidgetComponent):

    @register_props
    def __init__(self, layout="column", style=None):
        super().__init__()

        self._already_rendered = {}
        self._old_rendered_children = []
        self.underlying = QtWidgets.QScrollArea()
        self.underlying.setWidgetResizable(True)

        self.inner_widget = QtWidgets.QWidget()
        if layout == "column":
            self.scroll_area_layout = QtWidgets.QVBoxLayout()
        elif layout == "row":
            self.scroll_area_layout = QtWidgets.QHBoxLayout()
        self.inner_widget.setLayout(self.scroll_area_layout)
        self.underlying.setWidget(self.inner_widget)
        
        self.underlying.setObjectName(str(id(self)))

    def _delete_child(self, i):
        child_node = self.scroll_area_layout.takeAt(i)
        if child_node.widget():
            child_node.widget().deleteLater()

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []
        new_children = set()
        for child in children:
            new_children.add(child.component)

        for child in list(self._already_rendered.keys()):
            if child not in new_children:
                del self._already_rendered[child]

        for i, old_child in reversed(list(enumerate(self._old_rendered_children))):
            if old_child not in new_children:
                commands += [(self._delete_child, i)]

        self._old_rendered_children = [child.component for child in children]
        for i, child in enumerate(children):
            if child.component not in self._already_rendered:
                commands += [(self.scroll_area_layout.insertWidget, i, child.component.underlying)]
            self._already_rendered[child.component] = True

        for prop in newprops:
            if prop == "style":
                commands += [(self.underlying.setStyleSheet, dict_to_style(newprops[prop],  "QWidget#" + str(id(self))))]
        return commands

class List(BaseComponent):

    @register_props
    def __init__(self):
        super().__init__()

    def _qt_update_commands(self, children, newprops, newstate):
        return []



class Table(WidgetComponent):

    @register_props
    def __init__(self, rows: int, columns: int,
                 row_headers: tp.Sequence[tp.Any] = None, column_headers: tp.Sequence[tp.Any] = None,
                 style: StyleType = None, alternating_row_colors:bool = True):
        super().__init__()

        self._already_rendered = {}
        self._old_rendered_children = []
        self.underlying = QtWidgets.QTableWidget(rows, columns)
        self.underlying.setObjectName(str(id(self)))

    def _delete_child(self, i):
        child_node = self.underlying_layout.takeAt(i)
        if child_node.widget():
            child_node.widget().deleteLater()

    def _qt_update_commands(self, children, newprops, newstate):
        commands = []

        for prop in newprops:
            if prop == "style":
                commands += [(self.underlying.setStyleSheet, dict_to_style(newprops[prop],  "QWidget#" + str(id(self))))]
            elif prop == "rows":
                commands += [(self.underlying.setRowCount, newprops[prop])]
            elif prop == "columns":
                commands += [(self.underlying.setColumnCount, newprops[prop])]
            elif prop == "alternating_row_colors":
                commands += [(self.underlying.setAlternatingRowColors, newprops[prop])]
            elif prop == "row_headers":
                if newprops[prop] is not None:
                    commands += [(self.underlying.setVerticalHeaderLabels, list(map(str, newprops[prop])))]
                else:
                    commands += [(self.underlying.setVerticalHeaderLabels, list(map(str, range(newprops.rows))))]
            elif prop == "column_headers":
                if newprops[prop] is not None:
                    commands += [(self.underlying.setHorizontalHeaderLabels, list(map(str, newprops[prop])))]
                else:
                    commands += [(self.underlying.setHorizontalHeaderLabels, list(map(str, range(newprops.columns))))]

        new_children = set()
        for child in children:
            new_children.add(child.component)

        for child in list(self._already_rendered.keys()):
            if child not in new_children:
                del self._already_rendered[child]

        for i, old_child in reversed(list(enumerate(self._old_rendered_children))):
            if old_child not in new_children:
                for j, el in enumerate(old_child.children):
                    if el:
                        commands += [(self.underlying.setCellWidget, i, j, QtWidgets.QWidget())]

        self._old_rendered_children = [child.component for child in children]
        for i, child in enumerate(children):
            if child.component not in self._already_rendered:
                for j, el in enumerate(child.children):
                    commands += [(self.underlying.setCellWidget, i, j, el.component.underlying)]
            self._already_rendered[child.component] = True
        return commands


class _QtTree(object):
    def __init__(self, component, children):
        self.component = component
        self.children = children

    def gen_qt_commands(self, render_context):
        commands = []
        for child in self.children:
            rendered = child.gen_qt_commands(render_context)
            commands.extend(rendered)

        if not render_context.need_rerender(self.component):
            return commands
        commands.extend(self.component._qt_update_commands(self.children, self.component.props, {}))
        return commands

    def __hash__(self):
        return id(self)

    def print_tree(self, indent=0):
        tags = self.component._tags()
        if self.children:
            print("\t" * indent + tags[0])
            for child in self.children:
                child.print_tree(indent=indent + 1)
            print("\t" * indent + tags[1])
        else:
            print("\t" * indent + tags[2])


class _RenderContext(object):
    def __init__(self, storage_manager):
        self.storage_manager = storage_manager
        self.need_qt_command_reissue = {}
        self.component_to_new_props = {}
        self.component_to_old_props = {}

    def mark_props_change(self, component, newprops):
        d = dict(newprops._items)
        if "children" not in d:
            d["children"] = []
        self.component_to_new_props[component] = newprops
        if component not in self.component_to_old_props:
            self.component_to_old_props[component] = component.props
        self.set(component, "_props", d)

    def get_new_props(self, component):
        if component in self.component_to_new_props:
            return self.component_to_new_props[component]
        return component.props

    def get_old_props(self, component):
        if component in self.component_to_old_props:
            return self.component_to_old_props[component]
        return component.props

    def commit(self):
        for component, newprops in self.component_to_new_props.items():
            component.register_props(newprops)

    def set(self, obj, k, v):
        self.storage_manager.set(obj, k, v)

    def mark_qt_rerender(self, component, need_rerender):
        self.need_qt_command_reissue[component] = need_rerender

    def need_rerender(self, component):
        return self.need_qt_command_reissue.get(component, False)


class App(object):

    def __init__(self, component: Component, title: tp.Text = "Edifice App"):
        self._component_to_rendering = {}
        self._component_to_qt_rendering = {}
        self._root = component
        self._title = title

        self.app = QtWidgets.QApplication([])


    def _update_old_component(self, component, newprops, render_context: _RenderContext):
        if component.should_update(newprops, {}):
            render_context.mark_props_change(component, newprops)
            rerendered_obj = self._render(component, render_context)

            render_context.mark_qt_rerender(rerendered_obj.component, True)
            return rerendered_obj

        render_context.mark_props_change(component, newprops)
        render_context.mark_qt_rerender(component, False)
        # need_qt_command_reissue[self._component_to_qt_rendering[component].component] = False
        return self._component_to_qt_rendering[component]

    def _get_child_using_key(self, d, key, newchild, render_context: _RenderContext):
        if key not in d or d[key].__class__ != newchild.__class__:
            return newchild # self._render(newchild, storage_manager, need_qt_command_reissue)
        self._update_old_component(d[key], newchild.props, render_context)
        return d[key]

    def _attach_keys(self, component, render_context: _RenderContext):
        for i, child in enumerate(component.children):
            if not hasattr(child, "_key"):
                logging.warning("Setting child key to: KEY" + str(i))
                render_context.set(child, "_key", "KEY" + str(i))

    def _render(self, component: Component, render_context: _RenderContext):
        component._controller = self
        if isinstance(component, BaseComponent):
            if len(component.children) > 1:
                self._attach_keys(component, render_context)
            if component not in self._component_to_rendering:
                self._component_to_rendering[component] = component.children
                rendered_children = [self._render(child, render_context) for child in component.children]
                self._component_to_qt_rendering[component] = _QtTree(component, rendered_children) 
                render_context.mark_qt_rerender(component, True)
                return self._component_to_qt_rendering[component]
            else:
                old_children = self._component_to_rendering[component]
                if len(old_children) > 1:
                    self._attach_keys(component, render_context)

                if len(component.children) == 1 and len(old_children) == 1:
                    if component.children[0].__class__ == old_children[0].__class__:
                        self._update_old_component(old_children[0], component.children[0].props, render_context)
                        children = [old_children[0]]
                    else:
                        children = [component.children[0]]
                else:
                    if len(old_children) == 1:
                        if not hasattr(old_children[0], "_key"):
                            render_context.set(old_children[0], "_key", "KEY0")
                    key_to_old_child = {child._key: child for child in old_children}
                    old_child_to_props = {child: child.props for child in old_children}

                    children = [self._get_child_using_key(key_to_old_child, new_child._key, new_child, render_context)
                                for new_child in component.children]
                parent_needs_rerendering = False
                rendered_children = []
                for child1, child2 in zip(children, component.children):
                    if child1 != child2:
                        rendered_children.append(self._component_to_qt_rendering[child1])
                    else:
                        parent_needs_rerendering = True
                        rendered_children.append(self._render(child1, render_context))
                render_context.mark_qt_rerender(component, parent_needs_rerendering)

                self._component_to_rendering[component] = children
                self._component_to_qt_rendering[component] = _QtTree(component, rendered_children) 
                props_dict = dict(component.props._items)
                props_dict["children"] = children
                render_context.mark_props_change(component, PropsDict(props_dict))
                return self._component_to_qt_rendering[component]

        sub_component = component.render()
        old_rendering = None
        if component in self._component_to_rendering:
            old_rendering = self._component_to_rendering[component]

        if sub_component.__class__ == old_rendering.__class__:
            # TODO: Update component will receive props
            # TODO figure out if its subcomponent state or old_rendering state
            self._component_to_qt_rendering[component] = self._update_old_component(
                old_rendering, sub_component.props, render_context)
        else:
            # TODO: delete old component
            self._component_to_rendering[component] = sub_component
            self._component_to_qt_rendering[component] = self._render(sub_component, render_context)

        return self._component_to_qt_rendering[component]

    def _request_rerender(self, component, newprops, newstate):
        with _storage_manager() as storage_manager:
            render_context = _RenderContext(storage_manager)
            qt_tree = self._render(component, render_context)

        qt_tree.print_tree()
        print("need rerendering for: ", render_context.need_qt_command_reissue)
        qt_commands = qt_tree.gen_qt_commands(render_context)
        root = qt_tree.component
        print(qt_commands)
        for command in qt_commands:
            command[0](*command[1:])

        print()
        print()
        print()
        print()
        return root

    def start(self):
        root = self._request_rerender(self._root, {}, {})
        self.app.exec_()


def set_trace():
    '''Set a tracepoint in the Python debugger that works with Qt'''
    import pdb
    import sys
    pyqtRemoveInputHook()
    # set up the debugger
    debugger = pdb.Pdb()
    debugger.reset()
    # custom next to get outside of function scope
    debugger.do_next(None) # run the next command
    users_frame = sys._getframe().f_back # frame where the user invoked `pyqt_set_trace()`
    debugger.interaction(users_frame, None)
    pyqtRestoreInputHook()
