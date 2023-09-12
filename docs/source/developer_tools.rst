Developer Tools
===============

The declarative nature of Edifice makes it easy for development tools
to introspect application code.
Edifice comes with two tools to aid in development:

- Dynamic reloading: changes in source file will automatically be reloaded by the App. This is especially for adjusting styling and testing out layouts.
- Component inspector: say goodbye to (most but not all) print statements. You can look at the state and props of every component to diagnose what went wrong.

Dynamic reloading
-----------------

.. figure:: edifice-workflow.gif

One of the most tedious aspects of UI development is testing minor tweaks.
Suppose you just want to get the background color right.
In many frameworks, you would have to:

1. Edit the color in the source code
2. (sometimes) Recompile the code
3. Press/type the run/reload command
4. Wait for the app to startup
5. (if you are testing changes deep in your application) Interact with your
   app to create the conditions for displaying the component you are tweaking.
6. Examine results, and restart the cycle.

Even if you are tweaking components that are displayed as soon as the application opens,
this cycle takes a couple of seconds and more importantly requires multiple
context switches.
The fact that any UI tweak requires multiple iterations of this cycle makes you want to tear your hair out.

Edifice dynamic reloading allows you to skip directly from 1 to 6 when
you run your program through the Edifice runner.
As soon as you save a file,
the runner would reload components defined in that file,
without needing to close your app and restarting it.
All external references to these components will point to the new one.

.. caution::
    It is important to import the module directly, via :code:`import path.to.module as module`
    or :code:`from path.to import module`. If you import the Component class directly,
    e.g. :code:`from path.to.module import MyComponent`, all references to MyComponent will permanently point
    to the original version.

All unaffected component states (i.e. states of components defined outside the file) will be maintained.
If you structure your program in a modular way across multiple files,
only a few components would need to be reloaded,
saving you the time of navigating through your app to get to the changed widget.

Running your app through Edifice is extremely simple.
On the command line::

    python -m edifice path/to/your/app.py RootComponent

This will run app.py, mounting the specified Component as the root,
listening to changes to all Python files contained in
path/to/your (and recursively in all sub directories)
and dynamically reloading all changes.
If you want to explicitly specify another path to listen to, use the --dir flag::

    python -m edifice --dir directory/to/watch path/to/your/app.py RootComponent


Component Inspector
-------------------

.. figure:: inspector.png

Another pain point of GUI development (and even more generally) is figuring out
the internal state of your application for debugging purposes.
Quite frequently, you would resort to print statements
(which are now easier to add due to dynamic reloading,
since you don't have to restart your app to see new prints).
We of course do not presume we can replace the full utility of print statements,
but we offer a tool, Component Inspector, which can eliminate many cases of
"shoot I forgot to print this variable".

The Component Inspector, like the Inspect Elements tool of web browsers
or the React inspector tool,
allows you to peer into the internal state of your components.
It displays the entire Component Tree, as well as the props and state of
every component,
so you do not have to worry about printing those values.

To launch the inspector, use the :code:`--inspect` flag for the Edifice runner::

    python -m edifice --inspect path/to/your/app.py RootComponent

Currently the inspector, like Edifice, is in a very early alpha stage.
In future iterations, we plan to add the following features to the Component Inspector:

- Support logging of state changes
- A visual debugger
- Highlighting of the displayed widgets corresponding to each Component.
- Injecting state into the application
