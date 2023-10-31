"""
An edifice application is created by rendering a :class:`Element` with an
:class:`App`.
Let's examine what these objects are to understand what this statement means.

Elements are the basic building blocks of your GUI.
A Element object is a stateful container wrapping a stateless render function,
which describes what to render given the current Element state.
Elements can be composed of other components,
both native components
(:class:`View`, :class:`Button`, :class:`Label`)
and other composite Elements created by you or others.

Elements have both internal state and external properties.
The external properties, **props**, are passed into the Element by another
Element::

    class Foo(Element):
        @edifice.register_props  # don't worry about this for now
        def __init__(self, a, b, c):  # a, b, c are the props
            pass

    Foo(a=1, b=2, c=3)  # Create a Foo with props a=1, b=2, c=3.

These values are owned by the external caller and should not be modified by this Element.
They may be accessed via the field props :code:`self.props`, which is a
:class:`PropsDict`.
A :class:`PropsDict` allows iteration, “get item” :code:`self.props["value"]`,
and “get attribute” :code:`self.props.value`, but not “set item” or “set attribute”.

The internal state, henceforth referred to as the **state**, belong to the Element.
These are attributes of the Element object, for instance :code:`self.my_state`.
You can initialize the state as usual in the constructor
(e.g. :code:`self.my_state = {"a": 1}`),
and the state persists so long as the Element is still mounted.

Changes in state and props will automatically trigger a re-render
(unless you override this behavior by modifying :func:`Element.should_update`).
State should be changed using either the :func:`Element.set_state` function
or the :func:`Element.render_changes` context manager.
See documentation for :class:`Element` for more details.

The main method of Element is :func:`Element.render`, which should describe the rendered UI
given the current Element state.
The render result is composed of your own higher-level components as well as
the core Elements, such as
:class:`Label`, :class:`Button`, and :class:`View`.
Elements may be composed in a tree like fashion:
one special prop is :code:`children`, which will always be defined (defaults to an
empty list).
To better enable the visualization of the tree-structure of a Element
in the code,
the :code:`call()` method of Element has been overriden to set the arguments
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

You can thus describe your entire application as a single root Element,
which is composed of various sub-components representing different parts of your application.
Each Element is responsible for managing its own state,
updating it as necessary given user interactions and events.
Because state is self-contained, you can compose Elements arbitarily,
including across projects.
Edifice provides a few higher level components that are defined using the
same API provided to users.

One central tenet of Edifice is the importance of managing state.
The most complex part of any application is not fancy widgets or animations,
but maintaining consistent state, so that what the user sees is accurate
(this is very important -- you don't want to show Apple stock prices
when other parts of your UI indicates the user is looking at Microsoft!)
The Element abstraction ensures that the UI is a pure and side effect free
function of the state, so that if you serialize the state and play it back,
you get the same UI.

Of course, we don't live in a functional utopia devoid of any mutable state,
so equally important is managing ownership of the state.
There should be only one ground truth value for any state variable,
and any copies of this state should always refer back to the ground truth value.
In the simplest case, state is managed by a Element,
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
for issuing the commands necessary to render the each of the declared Elements.
The :class:`App` object is created by passing in the root :class:`Element`,
and it tracks all state changes in the Element tree with the given root.
Calling the :func:`App.start` method on the App object will run your application
and display the GUI you created::

    if __name__ == "__main__":
        App(MyApp()).start()

When components are rendered, the :func:`Element.render` function is called.
This output is then compared against the output
of the previous render (if that exists). The two renders are diffed,
and on certain conditions, the Element objects from the previous render
are maintained and updated with new props.
Two Elements belonging to different classes will always be re-rendered,
and Elements belonging to the same class are assumed to be the same
and thus maintained (preserving the old state).

For lists of Elements, a more complex procedure (the same as in ReactJS)
will determine which Elements to maintain and which to replace;
see documentation of :class:`Element` class for details.

Some useful utilities are also provided:

* :func:`register_props` : A decorator for the :code:`__init__` function that records
  all arguments as props.
* :func:`component`: A decorator to turn a render function into a
  Element. This is useful if your Element has no internal state.
* :func:`edifice.utilities.set_trace`: An analogue of :code:`pdb.set_trace` that works with Qt
  (:code:`pdb.set_trace` interrupts the Qt event flow, causing an unpleasant
  debugging experience). Use this :code:`set_trace` if you want to set breakpoings.
"""


from ._component import PropsDict, Element, component, register_props, Reference
from .state import StateValue, StateManager
from .app import App
from .base_components import *
from .utilities import alert, file_dialog, Timer, set_trace
