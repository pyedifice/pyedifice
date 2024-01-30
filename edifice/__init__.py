"""

Declaring Element Trees
-----------------------

An edifice application is created by rendering a :class:`Element` with an
:class:`App`.
Let's examine what these objects are to understand what this statement means.

The rendering for an Edifice application is done by declaring a tree of Elements
starting with a single root Element, and then declaring its children.

An Element may be either a
:doc:`Base Element <base_components>`
or a :func:`component` Element.

A :func:`component` Element is a function which renders an
:class:`Element` tree.

Elements have both internal state and external properties.
The external properties, **props**, are passed into the Element::

    @component
    def Foo(self, a, b, c): # a, b, c are the props

    Foo(a=1, b=2, c=3)  # Render a Foo with props a=1, b=2, c=3.

These values are owned by the external caller and should not be modified by this Element.

The internal state, henceforth referred to as the **state**, belong to the Element.
In a :func:`component` Element, the internal state is managed by :doc:`hooks`.

Changes in **state** or **props** will automatically trigger a re-render.

Declaring an Element tree in a :func:`component` Element render function looks
like this.
To declare an Element to be the parent of some other
child Elements in the tree, use the parent as a
`with statement context manager <https://docs.python.org/3/reference/datamodel.html#context-managers>`_::

    @component
    def MyApp(self):
        with Window():
            with View(layout="column"):
                with View(layout="row"):
                    Label("Username: ")
                    TextInput()
                with View(layout="row"):
                    Label("Email: ")
                    TextInput()

In HTML/XML, this would be written as:

.. code-block:: xml

    <Window>
        <View layout="column">
            <View layout="row">
                <Label text="Username: " />
                <TextInput />
            </View>
            <View layout="row">
                <Label text="Email: " />
                <TextInput />
        </View>
    </Window>

You can thus describe your entire application as a single root Element,
which is composed of various sub-Elements representing different parts of your application.
Each Element is responsible for managing its own state,
updating it as necessary given user interactions and events.
Because state is self-contained, you can compose Elements arbitarily,
including across projects.

Model-View-Update
-----------------

Edifice, like React, uses the `Elm Architecture <https://guide.elm-lang.org/architecture/>`_,
also known as Model-View-Update.
This means that there is a one-way information flow from Model to View to
Update and then back to Model.

====== =======
Model  The **state** of the application.
View   The declarative render function.
Update Event handlers which change the **state**.
====== =======

It is the one-way information flow of Model-View-Update which makes
this style of GUI programming scale up well to complicated user interfaces.

Rendering
---------

An :class:`App` encapsulates the rendering engine that's responsible
for issuing the commands necessary to render the each of the declared Elements.
The :class:`App` object is created by passing in the root :class:`Element`,
and it tracks all state changes in the Element tree with the given root.
Calling the :func:`App.start` method on the App object will run your application
and display the GUI you created::

    if __name__ == "__main__":
        App(MyApp()).start()

When Elements are rendered,
the result is then compared against the result
of the previous render (if that exists). The two renders are diffed,
and on certain conditions, the Element objects from the previous render
are updated with new props.
Two Elements belonging to different classes will always be re-rendered,
and Elements belonging to the same class are assumed to be the same
and thus maintained (preserving the old state).

When parent Element has many child Elements of the same class,
a more complex procedure (the same as in ReactJS)
will determine which Elements to maintain and which to replace.
When comparing the child Elements, the Element’s
:code:`_key` attribute will
be compared. Elements with the same :code:`_key` and same class are assumed to be
the same. You can set the key using the :func:`Element.set_key` method::

    with View(layout="row"):
        MyElement("Hello").set_key("hello")
        MyElement("World").set_key("world")

If the :code:`_key` is not provided, the diff algorithm will assign automatic keys
based on index, which could result in subpar performance due to unnecessary rerenders.
To ensure control over the rerender process, it is recommended to :func:`Element.set_key`
whenever you have many children of the same class.
"""

from ._component import Element, component, Reference
from .app import App
from .utilities import alert, file_dialog, set_trace
from .hooks import use_state, use_effect, use_async, use_ref, use_async_call

from .base_components import (
    QtWidgetElement,
    Window,
    ExportList,
    View,
    ScrollView,
    TabView,
    GridView,
    Label,
    ImageSvg,
    Icon,
    IconButton,
    Button,
    TextInput,
    CheckBox,
    RadioButton,
    Slider,
    ProgressBar,
    Dropdown,
    CustomWidget,
    ButtonView,
    FlowView,
    Image,
    TableGridView,
    SpinInput,
)

__all__ = [
    "Element",
    "component",
    "Reference",
    "App",
    "alert",
    "file_dialog",
    "set_trace",
    "use_state",
    "use_effect",
    "use_async",
    "use_ref",
    "use_async_call",
    "QtWidgetElement",
    "Window",
    "ExportList",
    "View",
    "ScrollView",
    "TabView",
    "GridView",
    "Label",
    "ImageSvg",
    "Icon",
    "IconButton",
    "Button",
    "TextInput",
    "CheckBox",
    "RadioButton",
    "Slider",
    "ProgressBar",
    "Dropdown",
    "CustomWidget",
    "ButtonView",
    "FlowView",
    "Image",
    "TableGridView",
    "SpinInput",
]
