Developer Tools
===============

The Edifice Runner provides some useful tools for developing Edifice applications.

Dynamic hot-reload
------------------

.. figure:: /image/edifice-workflow.gif

To enable dynamic hot-reload, run your application through the Edifice Runner.
On the command line::

    python -m edifice path/to/your/app.py MyRootElement

This will run :code:`app.py`, mounting the :code:`MyRootElement` as the root,
listening to changes to all Python files contained in
path/to/your (and recursively in all sub directories)
and dynamically reloading all changes.

If you want to explicitly specify another path to listen to, use the :code:`--dir` flag::

    python -m edifice --dir directory/to/watch path/to/your/app.py RootElement

.. caution::
    It is important to import the module directly, via :code:`import path.to.module as module`
    or :code:`from path.to import module`. If you import the Element class directly,
    e.g. :code:`from path.to.module import MyElement`, all references to MyElement will permanently point
    to the original version.

Dyanamic hot-reload is very useful for fine-tuning the presentation styles
of Elements deep within your application.
You can test if the margin should be *10px* or *15px* instantly without closing the app,
reopening it, and waiting for everything to load.

All unaffected component states (i.e. states of components defined outside the file) will be maintained
during hot-reload.
If you structure your program in a modular way across multiple files,
only a few components would need to be reloaded,
saving you the time of navigating through your app to get to the changed widget.

.. caution::
    Dynamic hot-reload currently will not work for the root
    :func:`@component<component>` which contains the :class:`Window`.

    It will only work for child components of the root component.

    So it’s a good idea to structure your application with a
    root Main :func:`@component<component>` that only contains the :class:`Window`,
    like this.

    .. code-block:: python

        @component
        def HelloWorld(self):
            Label("Hello, World!")

        @component
        def Main(self):
            with Window():
                HelloWorld()

        if __name__ == "__main__":
            App(Main()).start()

You will find there are other limitations to dynamic hot-reload. It will work
for changes to style and layout and text, but if you make more drastic changes
like introducing new component types or changing the Hooks then the hot-reloader
often fail and then you will need to restart the application.

Element Inspector
-------------------

.. figure:: /image/inspector.png

To launch the Element Inspector, use the :code:`--inspect` flag for the Edifice Runner::

    python -m edifice --inspect path/to/your/app.py RootElement

The Element Inspector, like the Inspect Elements tool of web browsers
or the React inspector tool,
allows you to inspect the internal state of your components.
It displays the entire Element Tree, as well as the props and state of
every component.
