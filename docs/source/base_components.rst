Base Elements
===============

.. automodule:: edifice.base_components

Base Elements are the building blocks for an Edifice application.

Each Base Element manages an underlying
`QWidget <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWidget.html>`_.

All Base Elements in this module inherit from :class:`QtWidgetElement<edifice.QtWidgetElement>`
and its props.
This means that all Base Elements can be made to respond to clicks by passing
a handler function to the :code:`on_click` prop. All Base Elements are
stylable using the :code:`style` prop, see :doc:`Styling<styling>`.

.. currentmodule:: edifice
.. autosummary::
   :toctree: stubs
   :recursive:
   :template: custom-class.rst

   QtWidgetElement

Base Elements can roughly be divided into Root Elements, Layout Elements,
and Content Elements.

Root Base Elements
------------------

The root parent Element of every Edifice application is a :class:`Window<edifice.Window>`.

Or an :class:`ExportList<edifice.ExportList>` for exporting components to
a normal PySide6/PyQt6 app.

.. currentmodule:: edifice
.. autosummary::
   :toctree: stubs
   :recursive:
   :template: custom-class.rst

   Window
   ExportList

Layout Base Elements
--------------------

Each Layout Base Element manages an underlying
`QLayout <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLayout.html>`_,
and can have children (like the :code:`<div>` HTML tag).

To render a Layout Base Element, always use the :code:`with` statement
and indent the element’s children::

    with VBoxView():
        with HBoxView():
            Label("Hello")
            Label("World")

All of the Layout Base Elements have the name suffix :code:`View`.

.. currentmodule:: edifice
.. autosummary::
   :toctree: stubs
   :recursive:
   :template: custom-class.rst

   VBoxView
   HBoxView
   FixView
   VScrollView
   HScrollView
   FixScrollView
   TabView
   GridView
   TableGridView
   TableGridRow
   FlowView
   WindowPopView

Content Base Elements
---------------------

Content Base Elements render a single Qt Widget and mostly do not have children.

.. currentmodule:: edifice
.. autosummary::
   :toctree: stubs
   :recursive:
   :template: custom-class.rst

   Label
   Image
   ImageSvg
   Icon
   IconButton
   Button
   ButtonView
   TextInput
   TextInputMultiline
   SpinInput
   CheckBox
   RadioButton
   Slider
   ProgressBar
   Dropdown

Events
------

Each user interaction with a Base Element generates events, and you can specify
how to handle the event by providing a callback function.

These callbacks are passed into the Base Element as **props**, for example
the :code:`on_click` **prop** of :class:`QtWidgetElement<edifice.QtWidgetElement>`,
or the :code:`on_change` **prop** for checkboxes, radio buttons, sliders,
and text input.
When the event occurs the callback function will be called with an argument
describing the event.

Usually, what you want to do in an event handler callback is to update some
state with a :func:`use_state() <edifice.use_state>` **setter function**.

These callbacks run in the same thread as the main application.
This is handy, as you don't have to worry about locking and race conditions.
However, a lengthy operation will block the application from interacting with the user,
which is generally a bad user experience.

Consider this code::

    @component
    def MyComponent(self):

        results, set_results = use_state("")

        def on_click(event:QMouseEvent):
            r = fetch_from_network()
            set_results(r)

        with VBoxView():
            Button("Fetch", on_click=on_click)
            if results:
                Label(results)

When the Fetch button is clicked, the event handler will call a lengthy :code:`fetch_from_network` function,
blocking the application from further progress.
In the mean time, if the user clicks the increment button, nothing will happen until the fetch is complete.

For such cases, you can use an async callback function.

To allow the rest of the application to run while the fetch is happening, you can define
the :code:`on_click` handler as a coroutine::

    @component
    def MyComponent(self):

        results, set_results = use_state("")
        loading, set_loading = use_state(False)

        async def on_click(event:QMouseEvent):
            set_loading(True)
            r = await fetch_from_network()
            set_results(r)
            set_loading(False)

        with VBoxView():
            Button("Fetch", on_click=on_click)
            if loading:
                Label("Loading")
            elif results:
                Label(results)

While the :code:`fetch_from_network` function is running, control is returned to the event loop,
allowing the application to continue handling button clicks.

.. note::

    In some cases you may have a bug from a race condition where the async
    event handler completes after the Element has been unmounted.

    For such cases use :func:`use_async_call<edifice.use_async_call>`.

Use the :func:`use_async_call<edifice.use_async_call>` Hook for an asynchronous event handler
which will cancel automatically when :code:`MyComponent` is unmounted, or
when the Fetch button is pressed again::

    @component
    def MyComponent(self):

        results, set_results = use_state("")
        loading, set_loading = use_state(False)

        async def on_click(event:QMouseEvent):
            set_loading(True)
            r = await fetch_from_network()
            set_results(r)
            set_loading(False)

        on_click_handler, cancel_click_handler = use_async_call(on_click)

        with VBoxView():
            Button("Fetch", on_click=on_click_handler)
            if loading:
                Label("Loading")
            elif results:
                Label(results)

.. _custom_widget:

Custom Base Elements
--------------------

Not all QtWidgets are supported by Edifice.
Edifice provides :class:`CustomWidget` to allow you to bind arbitrary
QtWidgets to an Edifice Element.

.. currentmodule:: edifice
.. autosummary::
   :toctree: stubs
   :recursive:
   :template: custom-class.rst

   CustomWidget

