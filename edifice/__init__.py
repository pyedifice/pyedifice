"""
An edifice application is created by rendering a Component object with
an App object. Let's examine what these objects are to understand
what this statement means.

The Component class is the basic building block of your GUI.
Components are composed of
other components,
both native components (View, Button, Text) and other composite
components created by you or others.
A Component object is a stateful container wrapping a stateless render function,
which describes how the component is built up from its building blocks
given the current Component state.

Components have both internal and external states.
The external properties, **props**, are passed into the Component by another
Component's render function through the constructor. These values are owned
by the external caller and should not be modified by this Component.
They may be accessed via the field props (self.props), which is a PropsDict.
A PropsDict allows iteration, get item (self.props["value"]), and get attribute
(self.props.value), but not set item or set attribute.

The internal properties, the **state**, belong to this Component, and may be
used to keep track of internal state. You may set the state as
attributes of the Component object, for instance self.my_state.
You can initialize the state as usual in the constructor (e.g. self.my_state = {"a": 1}),
and the state persists so long as the Component is still mounted.

Changes in state and props will automatically trigger a re-render
(unless you override this behavior by modifying `should_update`).
State should be changed using either the `component.set_state` function
or the `component.render_changes()` context manager.
See documentation for Component for more details.

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

You can thus describe your entire application as a single root Component,
which is composed of various sub-components representing different parts of your application.
Each Component is responsible for managing its own state, and each state should be owned
(in the sense of being allowed to freely modify and manage)
by one Component, and can only be passed to sub-components via read-only props.
State flows downward from the parent to the child;
in order for a child component to modify state in the parent,
the parent has to pass a callback or a handle to the child, giving the child access to that state.
This single-direction flow of state might sound limiting, but in reality it makes code
easier to understand and reason about.

An App object encapsulates the rendering engine that's responsible
for issuing the commands necessary to render the each of the declared Components.
The App object is created by passing in the root Component,
and it tracks all state changes in the Component tree with the given root.
Calling the start method on the App object will run your application
and display the GUI you created::

    if __name__ == "__main__":
        App(MyApp()).start()

When components are rendered,
the render function is called. This output is then compared against the output
of the previous render (if that exists). The two renders are diffed,
and on certain conditions, the Component objects from the previous render
are maintained and updated with new props.
Two Components belonging to different classes will always be re-rendered,
and Components belonging to the same class are assumed to be the same
and thus maintained (preserving the old state).
For lists of Components, a more complex procedure (the same as in ReactJS)
will resolve which Components to maintain and which to replace;
see documentation of Component class for details.

Some useful utilities are also provided:
    * register_props: A decorator for the __init__ function that records
      all arguments as props
    * set_trace: An analogue of pdb.set_trace that works with Qt
      (pdb.set_trace interrupts the Qt event flow, causing an unpleasant
      debugging experience). Use this set_trace if you want to set breakpoings.
"""


from ._component import PropsDict, Component, register_props
from .state import StateValue, StateManager
from .app import App
from .base_components import *
from .utilities import Timer, set_trace


if __name__ == "__main__":
    from .runner import runner
    runner()
