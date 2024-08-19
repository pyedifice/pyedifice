Base Elements
===============

.. automodule:: edifice.base_components

.. currentmodule:: edifice
.. autosummary::
   :toctree: stubs
   :recursive:
   :template: custom-class.rst

   QtWidgetElement
   Window
   ExportList
   VBoxView
   HBoxView
   FixView
   VScrollView
   HScrollView
   FixScrollView
   TabView
   GridView
   TableGridView
   FlowView
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

For every base Element, user interactions generate events, and you can specify
how to handle the event by passing a callback function (which is either a
function or an asyncio coroutine).
These callbacks can be passed into the base Element as props, for example
the :code:`on_click` callback that can be passed to every widget,
or the :code:`on_change` callback for checkboxes, radio buttons, sliders,
and text input.
The callback function is passed an argument describing the event, for example
a click object holding click information (location of cursor, etc)
or the new value of the input.

These callbacks run in the same thread as the main application.
This is handy, as you don't have to worry about locking and race conditions.
However, a lengthy operation will block the application from interacting with the user,
which is generally a bad user experience.
For such cases, you can use an asyncio `coroutine <https://docs.python.org/3/library/asyncio-task.html>`_.

Consider this code::

    @component
    def MyComponent(self):

        results, set_results = use_state("")
        counter, set_counter = use_state(0)

        def on_click(event:QMouseEvent):
            r = fetch_from_network()
            set_results(r)

        with edifice.View():
            edifice.Label(results)
            edifice.Label(counter)
            edifice.Button("Fetch", on_click=on_click)
            edifice.Button("Increment", on_click=lambda e: set_counter(counter + 1)

When the Fetch button is clicked, the event handler will call a lengthy :code:`fetch_from_network` function,
blocking the application from further progress.
In the mean time, if the user clicks the increment button, nothing will happen until the fetch is complete.

To allow the rest of the application to run while the fetch is happening, you can define
the :code:`on_click` handler as a coroutine::

    @component
    def MyComponent(self):

        results, set_results = use_state("")
        counter, set_counter = use_state(0)
        loading, set_loading = use_state(False)

        async def on_click(event:QMouseEvent):
            set_loading(True)
            r = await fetch_from_network()
            set_results(r)
            set_loading(False)

        with edifice.View():
            edifice.Label(results)
            if loading:
                edifice.Label("Loading")
            edifice.Label(counter)
            edifice.Button("Fetch", on_click=on_click)
            edifice.Button("Increment", on_click=lambda e: set_counter(counter + 1)

While the :code:`fetch_from_network` function is running, control is returned to the event loop,
allowing the application to continue handling button clicks.

See docs for :class:`QtWidgetElement<edifice.QtWidgetElement>` for a list of supported events.
