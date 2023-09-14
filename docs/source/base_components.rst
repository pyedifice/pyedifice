Base Components
===============

.. automodule:: edifice.base_components

.. currentmodule:: edifice
.. autosummary::
   :toctree: stubs
   :recursive:
   :template: custom-class.rst

   QtWidgetComponent
   Window
   View
   ScrollView
   TabView
   GridView
   Label
   Image
   ImageSvg
   Icon
   IconButton
   Button
   TextInput
   CheckBox
   RadioButton
   Slider

Events
------

For every base component, user interactions generate events, and you can specify how to handle the event by passing a callback function (which is either a function or an asyncio coroutine).
These callbacks can be passed into the base component as props, for example the :code:`on_click` callback that can be passed to every widget,
or the :code:`on_change` callback for checkboxes, radio buttons, sliders, and text input.
The callback function is passed an argument describing the event, for example a click object holding click information (location of cursor, etc)
or the new value of the input.

These callbacks run in the same thread as the main application.
This is handy, as you don't have to worry about locking and race conditions.
However, a lengthy operation will block the application from interacting with the user,
which is generally a bad user experience.
For such cases, you can use an asyncio `coroutine <https://docs.python.org/3/library/asyncio-task.html>`_.

Consider this code::

    class Component(edifice.Component):

        def __init__(self):
            super().__init__()
            self.results = ""
            self.counter = 0

        def on_click(self, e):
            results = fetch_from_network()
            self.set_state(results=results)

        def render(self):
            return edifice.View()(
                edifice.Label(self.results),
                edifice.Label(self.counter),
                edifice.Button("Fetch", on_click=self.on_click),
                edifice.Button("Increment", on_click=lambda e: self.set_state(counter=self.counter + 1))
            )

When the Fetch button is clicked, the event handler will call a lengthy :code:`fetch_from_network` function,
blocking the application from further progress.
In the mean time, if the user clicks the increment button, nothing will happen until the fetch is complete.

To allow the rest of the application to run while the fetch is happening, you can define
the :code:`on_click` handler as a coroutine::

    class Component(edifice.Component):

        def __init__(self):
            super().__init__()
            self.results = ""
            self.counter = 0
            self.loading = False

        async def on_click(self, e):
            self.set_state(loading=True)
            results = await asyncio.to_thread(fetch_from_network)
            self.set_state(loading=False, results=results)

        def render(self):
            return edifice.View()(
                edifice.Label(self.results),
                self.loading and edifice.Label("Loading"),
                edifice.Label(self.counter),
                edifice.Button("Fetch", on_click=self.on_click),
                edifice.Button("Increment", on_click=lambda e: self.set_state(counter=self.counter + 1))
            )

While the :code:`fetch_from_network` function is running, control is returned to the event loop,
allowing the application to continue handling button clicks.

See docs for :class:`QtWidgetComponent<edifice.QtWidgetComponent>` for a list of supported events.


.. _custom_widget:

Custom Widgets
--------------

Not all widgets are currently supported by Edifice.
Edifice provides :code:`CustomWidget` to allow you to bind arbitrary
QtWidgets to an Edifice component.
The two methods to override are :code:`create_widget`,
which should return the Qt widget,
and :code:`paint`,
which takes the current widget and new props,
and should update the widget according to the new props.

.. currentmodule:: edifice
.. autosummary::
   :toctree: stubs
   :recursive:
   :template: custom-class.rst

   CustomWidget

