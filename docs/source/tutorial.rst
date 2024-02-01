Tutorial
========

.. figure:: /image/example_tutorial.png

This tutorial will help you create your first Edifice app.
We will create an app that converts measurements in different units.

First, install Edifice::

    pip install pyedifice

.. note::

    Edifice supports both the PySide6 library and the PyQt6 library
    for Qt bindings (both are covered in the automated unit tests).
    Edifice prefers the PySide6 library but both are supported.

    If you would prefer to use the PyQt6 library and do not wish to
    install PySide6, you can run::

        pip install qasync  # A dependency required for asyncio integration
        pip install typing-extensions
        pip install --no-dependencies pyedifice

    You can switch to using PyQt6 by setting the :code:`EDIFICE_QT_VERSION` environment variable to :code:`PyQt6`::

        # Add to your bashrc
        export EDIFICE_QT_VERSION=PyQt6


Let us create the basic skeleton of our UI.
Copy this code into a new file, for example tutorial.py::

    from edifice import App, Label, TextInput, View, Window, component

    @component
    def MyApp(self):
        with Window(): # Top of every App must be a Window
            with View(layout="row"): # Top Window must have one static child
                Label("Measurement in meters:")
                TextInput("")
                Label("Measurement in feet:")

    if __name__ == "__main__":
        App(MyApp()).start()

What does this code do?
First we define a function :code:`MyApp` which is decorated by
:func:`edifice.component`.
The :code:`MyApp` component is the top-level Element of our application.

:class:`View<edifice.View>` is an example of
a base :class:`QtWidgetElement <edifice.QtWidgetElement>`.
The View receives :code:`layout="row"` as an argument in its constructor.
We refer to layout as a **"prop"** of the View Element — it is a property
passed to the View.

The View can have children. To establish the View as a parent Element and
then declare its children, we use a
`with statement <https://docs.python.org/3/reference/compound_stmts.html#with>`_
context. Elements inside the :code:`with` context are children.

In HTML or XML, you might have written it as:

.. code-block:: xml

    <Window>
        <View layout="row">
            <Label text="Measurement in meters" />
            <TextInput text="" />
            <Label text="Measurement in feet" />
        </View>
    </Window>

We pass the component :code:`MyApp`
to an :class:`App<edifice.App>`,
which is responsible for actually doing the rendering.
It takes the description of each Element, and it decides when and how to render it and its children.
It does so by monitoring the state of each Element, and it will re-render
when the Element state changes.

As you might expect, you can run this application simply with :code:`python tutorial.py`.
However, let us take advantage of Edifice's :doc:`dynamic loading capability<developer_tools>`,
so that we do not have to continually close the app and re-issue the command every time we change something.
To run the app with dynamic loading, do::

    python -m edifice tutorial.py MyApp

You should see a basic form emerge. However, it's not pretty, and it doesn't really do anything.

We can change the formatting of the Labels, TextInputs, and Views using :doc:`styling<styling>`,
which is broadly similar to CSS styling.
Here, what we need is to add margins between the view and window boundary,
make the Labels shorter, and add a margin between the label and text input.
For example::

    from edifice import App, Label, TextInput, View, Window, component

    @component
    def MyApp(self):
        meters_label_style = {"width": 170}
        feet_label_style = {"margin-left": 20, "width": 200}
        input_style = {"padding": 2, "width": 120}
        with Window():
            with View(layout="row", style={"margin": 10, "width": 560}):
                Label("Measurement in meters:", style=meters_label_style)
                TextInput("", style=input_style)
                Label("Measurement in feet:", style=feet_label_style)

    if __name__ == "__main__":
        App(MyApp()).start()

If you want to make adjustments to this styling, you can simply edit your source file, and all changes will automatically
be reflected.

Our application still doesn't do anything, however. Let's add an :code:`on_change`
event handler to the input boxes.
This function will be called whenever the contents in the text input changes,
allowing us to ensure that the numbers in the input
box and in the label are in sync::

    from edifice import App, Label, TextInput, View, Window, component, use_state

    METERS_TO_FEET = 3.28084

    def str_to_float(s):
        try:
            return float(s)
        except ValueError:
            return 0.0

    @component
    def MyApp(self):

        meters, meters_set = use_state("0.0")

        feet = "%.3f" % (str_to_float(meters) * METERS_TO_FEET)

        meters_label_style = {"width": 170}
        feet_label_style = {"margin-left": 20, "width": 200}
        input_style = {"padding": 2, "width": 120}

        with Window():
            with View(layout="row", style={"margin": 10, "width": 560}):
                Label("Measurement in meters:", style=meters_label_style)
                TextInput(meters, style=input_style, on_change=meters_set)
                Label(f"Measurement in feet: {feet}", style=feet_label_style)

    if __name__ == "__main__":
        App(MyApp()).start()

Meters is a **state** variable in our component :code:`MyApp`,
so we have to use the :func:`edifice.use_state` hook.
:func:`edifice.use_state` returns a tuple with the current value
of :code:`meters`, and also a function which we can use to set
a new value for :code:`meters`.
We expect all changes to :code:`meters` to be reflected in the UI.
Think of the component function as a map from the state,
:code:`meters`, to UI Elements.

In the component function, we read the value of meters and convert it to feet,
and we populate the text input and label with the meters and feet respectively.
For the text input, we add an :code:`on_change` callback.
This function is called whenever the content of the text input changes.

In the :code:`on_change` callback, we call the :code:`meters_set` function.
The :code:`meters_set` function will set :code:`meters` to the new value of the input box,
and it will trigger a re-render.

If you want to see the state changes in action, you can open the Element Inspector::

    python -m edifice --inspect tutorial.py MyApp

The Element Inspector allows you to see the current state and props for all components in an UI (which, of course,
was created with Edifice). Play around with the application and see how the state changes.

Now suppose we want to add conversion from feet to meters. Instead of copying our code and repeating
it for each measurement pair, we can factor out the conversion logic into its own component::

    from edifice import App, Label, TextInput, View, Window, component, use_state

    METERS_TO_FEET = 3.28084

    def str_to_float(s):
        try:
            return float(s)
        except ValueError:
            return 0.0

    @component
    def ConversionWidget(self, from_unit, to_unit, factor):

        current_text, current_text_set = use_state("0.0")

        to_text = "%.3f" % (str_to_float(current_text) * self.props.factor)

        from_label_style = {"width": 170}
        to_label_style = {"margin-left": 60, "width": 200}
        input_style = {"padding": 2, "width": 120}

        with View(layout="row", style={"margin": 10, "width": 560}):
            Label(f"Measurement in {self.props.from_unit}:", style=from_label_style)
            TextInput(current_text, style=input_style, on_change=current_text_set)
            Label(f"Measurement in {self.props.to_unit}: {to_text}", style=to_label_style)

    @component
    def MyApp(self):
        with Window():
            with View(layout="column", style={}):
                ConversionWidget("meters", "feet", METERS_TO_FEET)
                ConversionWidget("feet", "meters", 1 / METERS_TO_FEET)

    if __name__ == "__main__":
        App(MyApp()).start()

Factoring out the logic makes it trivial to add conversions between pounds and
kilograms, liters and gallons, etc.
