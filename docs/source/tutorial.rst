Tutorial
========

.. figure:: /image/example_tutorial.png

This tutorial will help you create your first Edifice app.
We will create an app that converts measurements in different units.

First, install Qt and Edifice::

    pip install PySide6
    pip install pyedifice

.. note::

    Edifice supports both the PySide6 library and the PyQt6 library
    for Qt bindings.

    Edifice prefers the PySide6 library but both are supported.

    If you would prefer to use the PyQt6 library and do not wish to
    install PySide6, you can run::

        pip install PyQt6
        pip install pyedifice

    You can switch to using PyQt6 by setting the :code:`EDIFICE_QT_VERSION` environment variable to :code:`PyQt6`::

        export EDIFICE_QT_VERSION=PyQt6


Let’s create the basic skeleton of our UI.
Copy this code into a new file, for example tutorial.py::

    from edifice import App, Label, TextInput, HBoxView, Window, component

    @component
    def MyApp(self):
        with Window(): # Top of every App must be a Window
            with HBoxView():
                Label("Measurement in meters:")
                TextInput("")
                Label("Measurement in feet:")

    if __name__ == "__main__":
        App(MyApp()).start()

What does this code do?
First we define a function :code:`MyApp` which is decorated by
:func:`component<edifice.component>`.
The :code:`MyApp` component is the top-level Element of our application.

:class:`HBoxView<edifice.HBoxView>` is an example of
a base :class:`QtWidgetElement <edifice.QtWidgetElement>`.
The HBoxView can have children. To establish the HBoxView as a parent Element and
then declare its children, we use a
`with statement <https://docs.python.org/3/reference/compound_stmts.html#with>`_
context. Elements inside the :code:`with` context are children.

In HTML or XML, we might have written it as:

.. code-block:: xml

    <Window>
        <HBoxView>
            <Label text="Measurement in meters" />
            <TextInput text="" />
            <Label text="Measurement in feet" />
        </HBoxView>
    </Window>

We pass the component :code:`MyApp`
to an :class:`App<edifice.App>`,
which is responsible for actually doing the rendering.
It takes the description of each Element, and it decides when and how to render it and its children.
It does so by monitoring the **state** of each Element, and it will re-render
when the Element **state** changes.

As you might expect, you can run this application with :code:`python tutorial.py`.
However, let us take advantage of Edifice's :doc:`dynamic loading capability<developer_tools>`,
so that we do not have to continually close the app and re-issue the command every time we change something.
To run the app with dynamic loading, first install watchdog::

    pip install watchdog

then do::

    python -m edifice tutorial.py MyApp

You should see a basic form emerge. However, it's not pretty, and it doesn't really do anything.

We can change the formatting of the :class:`Label<edifice.Label>`, :class:`TextInput<edifice.TextInput>`, and
:class:`HBoxView<edifice.HBoxView>` using Qt :doc:`styling<styling>`,
which is similar to CSS styling.
Here, we want to add padding between the HBoxView and Window boundary,
make the Labels shorter, and add a margin between the Label and TextInput.
For example::

    from edifice import App, Label, TextInput, HBoxView, Window, component

    @component
    def MyApp(self):

        meters_label_style = {"min-width": 170}
        feet_label_style = {"margin-left": 20, "width": 220}
        input_style = {"padding": 2, "width": 120}

        with Window():
            with HBoxView(style={"padding": 10}):
                Label("Measurement in meters:", style=meters_label_style)
                TextInput("", style=input_style)
                Label("Measurement in feet:", style=feet_label_style)

    if __name__ == "__main__":
        App(MyApp()).start()

When we are running :code:`MyApp` with dynamic loading, Edifice will detect the change
to the source file and reload :code:`MyApp` at runtime so that we can see the styling
changes immediately.

Our application still doesn't do anything, however. Let's add an :code:`on_change`
event handler **prop** for the :class:`TextInput<edifice.TextInput>`.
the :code:`on_change` **prop** function will be called whenever the contents in the
text input changes due to user action::

    from edifice import App, Label, TextInput, HBoxView, Window, component, use_state

    METERS_TO_FEET = 3.28084

    @component
    def MyApp(self):

        meters, meters_set = use_state("0.0")

        meters_label_style = {"width": 170}
        feet_label_style = {"margin-left": 20, "width": 220}
        input_style = {"padding": 2, "width": 120}

        with Window():
            with HBoxView(style={"padding": 10}):
                Label("Measurement in meters:", style=meters_label_style)
                TextInput(meters, style=input_style, on_change=meters_set)
                Label(f"Measurement in feet: {feet}", style=feet_label_style)
                try:
                    feet = "%.3f" % (float(meters) * METERS_TO_FEET)
                    Label(f"Measurement in feet: {feet}", style=feet_label_style)
                except ValueError: # Could not convert string to float
                    pass # So don't render the Label

    if __name__ == "__main__":
        App(MyApp()).start()

:code:`meters` is a **state** variable in our component :code:`MyApp`,
so we have to use the :func:`use_state()<edifice.use_state>` hook.
:func:`use_state()<edifice.use_state>` returns a tuple with the current value
of :code:`meters`, and also a **state** setter function which we can use to set
a new value for :code:`meters`.

- :code:`meters` has type :code:`str`.
- :code:`meters_set` setter function has type :code:`Callable[[str], None]`.

We assigned the :code:`meters_set` **state** setter function as
the :code:`on_change` **prop** for the :class:`TextInput<edifice.TextInput>`.
Whenever the user types in the text input, the state will be set and
the UI will re-render.

Think of the component function as a map from the
:code:`meters` **state** to an Element tree.

In the component function, we read the value of :code:`meters` and convert it to feet,
and we render the text input and label Elements.

If we want to see the **state** changes in action, we can open the Element Inspector::

    python -m edifice --inspect tutorial.py MyApp

The Element Inspector allows us to see the current **state** and **props** for all Elements in a UI.
Play around with the application and see how the **state** changes.

Now we want to add conversion from feet to meters. Instead of copying our code and repeating
it for each measurement pair, we can factor out the conversion logic into its own component.
We pass the conversion parameters into the component as **props** arguments::

    from edifice import App, Label, TextInput, HBoxView, Window, component, use_state

    METERS_TO_FEET = 3.28084

    @component
    def ConversionWidget(self, from_unit, to_unit, factor):

        current_text, current_text_set = use_state("0.0")

        from_label_style = {"min-width": 170}
        to_label_style = {"margin-left": 60, "min-width": 220}
        input_style = {"padding": 2, "width": 120}

        with HBoxView(style={"padding": 10}):
            Label(f"Measurement in {from_unit}:", style=from_label_style)
            TextInput(current_text, style=input_style, on_change=current_text_set)
            try:
                to_text = "%.3f" % (float(current_text) * factor)
                Label(f"Measurement in {to_unit}: {to_text}", style=to_label_style)
            except ValueError: # Could not convert string to float
                pass # So don't render the Label


    @component
    def MyApp(self):
        with Window(title="Measurement Conversion"):
            ConversionWidget("meters", "feet", METERS_TO_FEET)
            ConversionWidget("feet", "meters", 1 / METERS_TO_FEET)

    if __name__ == "__main__":
        App(MyApp()).start()
