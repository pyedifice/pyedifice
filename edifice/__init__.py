"""

Declaring Element Trees
-----------------------

An edifice application is created by rendering a :class:`Element` with an
:class:`App`.

The rendering for an Edifice application is done by declaring a tree of Elements
starting with a single root :func:`component`, and then declaring its children.

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

The internal **state**, belongs to the Element.
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
            with VBoxView():
                with HBoxView():
                    Label("Username: ")
                    TextInput()
                with HBoxView():
                    Label("Email: ")
                    TextInput()

In HTML/XML, this would be written as:

.. code-block:: xml

    <Window>
        <VBoxView>
            <HBoxView>
                <Label text="Username: " />
                <TextInput />
            </HBoxView>
            <HBoxView>
                <Label text="Email: " />
                <TextInput />
        </VBoxView>
    </Window>

You describe your entire application as a single root Element,
which has child Elements representing different parts of your application.
Each Element is responsible for managing its own state,

An :class:`App` provides the rendering engine that's responsible
for issuing the commands necessary to render the each of the declared Elements.
The :class:`App` object is created by passing in the root :class:`Element`,
and it tracks all state changes in the Element tree with the given root.
Calling the :func:`App.start` method on the App object will run your application
and display the GUI you created::

    if __name__ == "__main__":
        App(MyApp()).start()


Model-View-Update
-----------------

Edifice, like React, uses the `Elm Architecture <https://guide.elm-lang.org/architecture/>`_,
also known as Model-View-Update.
This means that there is a one-way information flow from Model to View to
Update and then back to Model.

====== =======
Model  The **state** of the application.
View   The declarative render function, which takes the **state** and renders an Element tree.
Update Event handlers which change the **state**.
====== =======

It is the one-way information flow of Model-View-Update which makes
this style of GUI programming scale up well to complicated user interfaces.

Rendering
---------

Conceptually, Edifice (and ReactJS) works like this: Every time there is a
change (Update) to the **state** (Model), the render function (View) is
called and it renders the entire Element tree of Qt Widgets from scratch.

That sounds expensive and slow, and it would be if it weren't for the diffing
algorithm.
The diffing algorithm compares the new Element tree with the old Element tree
and makes minimal changes to the Qt Widgets.

The diffing algorithm
---------------------

When Elements are rendered,
the result is then compared against the result
of the previous render. The two renders are diffed,
and on certain conditions, the Element objects from the previous render
are updated with new props.

The diffing algorithm will compare a parents Element’s children
from the previous render with the children from the new render.

Two Elements belonging to different classes will always be re-rendered,
and Elements belonging to the same class are assumed to be the same
and thus maintained (preserving the old state).

When a parent Element has many child Elements of the same class,
a more complex procedure (the same as in ReactJS)
will determine which Elements to maintain and which to replace.

When comparing the child Elements, the Element’s
:code:`_key` attribute will
be compared. Elements with the same :code:`_key` and same class are assumed to be
the same. You can set the key using the :func:`Element.set_key` method::

    with HBoxView():
        MyElement("Hello").set_key("hello")
        MyElement("World").set_key("world")

If the :code:`_key` is not provided, the diff algorithm will guess which
Elements to maintain based on the order of the children.
To ensure control over the rerender process, it is recommended to :func:`Element.set_key`
whenever you have many children of the same class.
"""

from .engine import QtWidgetElement, Element, component, Reference, child_place, qt_component
from .app import App
from .utilities import alert, file_dialog, set_trace
from .hooks import use_state, use_effect, use_async, use_ref, use_async_call, use_effect_final

from .base_components import (
    Window,
    ExportList,
    View,
    VBoxView,
    HBoxView,
    FixView,
    ScrollView,
    VScrollView,
    HScrollView,
    FixScrollView,
    TabView,
    GridView,
    Label,
    ImageSvg,
    Icon,
    IconButton,
    Button,
    TextInput,
    TextInputMultiline,
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
    "App",
    "Button",
    "ButtonView",
    "CheckBox",
    "CustomWidget",
    "Dropdown",
    "Element",
    "ExportList",
    "FlowView",
    "GridView",
    "Icon",
    "IconButton",
    "Image",
    "ImageSvg",
    "Label",
    "ProgressBar",
    "QtWidgetElement",
    "RadioButton",
    "Reference",
    "ScrollView",
    "VScrollView",
    "HScrollView",
    "FixScrollView",
    "Slider",
    "SpinInput",
    "TabView",
    "TableGridView",
    "TextInput",
    "TextInputMultiline",
    "View",
    "VBoxView",
    "HBoxView",
    "FixView",
    "Window",
    "alert",
    "child_place",
    "component",
    "file_dialog",
    "qt_component",
    "set_trace",
    "use_async",
    "use_async_call",
    "use_effect",
    "use_effect_final",
    "use_ref",
    "use_state",
]
