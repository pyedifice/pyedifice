"""
An edifice application is created by rendering a Component with an App.
Let's examine what these objects are to understand what this statement means.

Components are the basic building blocks of your GUI.
A Component object is a stateful container wrapping a stateless render function,
which describes what to render given the current Component state.
Components can be composed of other components,
both native components (View, Button, Text) and other composite
components created by you or others.

Components have both internal state and external properties.
The external properties, **props**, are passed into the Component by another
Component::

    class Foo(Component):
        @edifice.register_props  # don't worry about this for now
        def __init__(self, a, b, c):  # a, b, c are the props
            pass

    Foo(a=1, b=2, c=3)  # Create a Foo with props a=1, b=2, c=3.

These values are owned by the external caller and should not be modified by this Component.
They may be accessed via the field props (:code:`self.props`), which is a PropsDict.
A PropsDict allows iteration, get item (:code:`self.props["value"]`), and get attribute
(:code:`self.props.value`), but not set item or set attribute.

The internal state, henceforth referred to as the **state**, belong to the Component.
These are attributes of the Component object, for instance self.my_state.
You can initialize the state as usual in the constructor (e.g. self.my_state = {"a": 1}),
and the state persists so long as the Component is still mounted.

Changes in state and props will automatically trigger a re-render
(unless you override this behavior by modifying `should_update`).
State should be changed using either the `component.set_state` function
or the `component.render_changes()` context manager.
See documentation for Component for more details.

The main method of Component is render, which should describe the rendered UI
given the current Component state.
The render result is composed of your own higher-level components as well as
the core Components, such as Label, Button, and View.
Components may be composed in a tree like fashion:
one special prop is children, which will always be defined (defaults to an
empty list).
To better enable the visualization of the tree-structure of a Component
in the code,
the call method of a Component has been overriden to set the arguments
of the call as children of the component.
This allows you to write tree-like code remniscent of HTML::

    def render(self):
        return View(layout="column")(
            View(layout="row")(
                Label("Username: "),
                TextInput()
            ),
            View(layout="row")(
                Label("Email: "),
                TextInput()
            ),
        )

In HTML/XML, this would be written as:

.. code-block:: xml

    <View layout="column">
        <View layout="row">
            <Label text="Username: " />
            <TextInput />
        </View>
        <View layout="row">
            <Label text="Email: " />
            <TextInput />
    </View>

You can thus describe your entire application as a single root Component,
which is composed of various sub-components representing different parts of your application.  
Each Component is responsible for managing its own state,
updating it as necessary given user interactions and events.
Because state is self-contained, you can compose Components arbitarily,
including across projects.
Edifice provides a few higher level components that are defined using the
same API provided to users.

One central tenet of Edifice is the importance of managing state.
The most complex part of any application is not fancy widgets or animations,
but maintaining consistent state, so that what the user sees is accurate
(this is very important -- you don't want to show Apple stock prices
when other parts of your UI indicates the user is looking at Microsoft!)
The Component abstraction ensures that the UI is a pure and side effect free
function of the state, so that if you serialize the state and play it back,
you get the same UI.

Of course, we don't live in a functional utopia devoid of any mutable state,
so equally important is managing ownership of the state.
There should be only one ground truth value for any state variable,
and any copies of this state should always refer back to the ground truth value.
In the simplest case, state is managed by a Component,
and passed down to children through props.
The child cannot modify the prop directly; doing so would result in two different values of the state.
In order for a child component to modify state in the parent,
the parent has to pass a setter function to the child,
so that any change is done on the ground truth source.
For cases where some central state is shared across
a wide swath of UI components, e.g. currently logged in user,
Edifice provides
:doc:`state values and state managers <state>` to allow this state
to be shared across many different components with the same reactive guarantee:
all state changes will be reflected in the UI.

An App object encapsulates the rendering engine that's responsible
for issuing the commands necessary to render the each of the declared Components.
The App object is created by passing in the root Component,
and it tracks all state changes in the Component tree with the given root.
Calling the start method on the App object will run your application
and display the GUI you created::

    if __name__ == "__main__":
        App(MyApp()).start()

When components are rendered, the render function is called.
This output is then compared against the output
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
    * make_component: A decorator to turn a render function into a
      Component. This is useful if your Component has no internal state.
    * set_trace: An analogue of pdb.set_trace that works with Qt
      (pdb.set_trace interrupts the Qt event flow, causing an unpleasant
      debugging experience). Use this set_trace if you want to set breakpoings.
"""


from ._component import PropsDict, Component, make_component, register_props, Reference
from .state import StateValue, StateManager
from .app import App
from .base_components import *
from .utilities import Timer, set_trace
