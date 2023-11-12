.. edifice documentation master file, created by
   sphinx-quickstart on Sun Jan  3 14:46:57 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Edifice
=======

Declarative GUI framework for Python and Qt

.. image:: /image/example_calculator.png
   :width: 200

.. image:: /image/example_harmonic_oscillator.gif
   :width: 250


.. code-block:: shell
    :caption: Installation

    pip install pyedifice

.. code-block:: python
    :caption: *Hello World* in Edifice

    import edifice
    from edifice import App, Label

    App(Label("Hello World!")).start()

Edifice is a Python library for building declarative application user interfaces.

- Modern **declarative** UI paradigm from web development.
- **100% Python** application development, no language inter-op.
- A **native** desktop app instead of a bundled web browser.
- Fast iteration via **hot reloading**.

This modern declarative UI paradigm is also known as
“`Model-View-Update <https://thomasbandt.com/model-view-update>`_,”
or “`The Elm Architecture <https://guide.elm-lang.org/architecture/>`_.”

Edifice uses `PySide6 <https://doc.qt.io/qtforpython-6/>`_
or `PyQt6 <https://www.riverbankcomputing.com/static/Docs/PyQt6/introduction.html>`_
as a backend. So Edifice is like
`React <https://react.dev/>`_, but with
Python instead of JavaScript, and `Qt Widgets <https://doc.qt.io/qt-6/qtwidgets-index.html>`_
instead of the HTML DOM.
If you have experience with React,
you will find Edifice very easy to pick up.

Getting Started
---------------

The easiest way to get started is via the :doc:`tutorial`.
To understand the core conception behind Edifice,
see :doc:`edifice`.

Why Edifice?
------------

The premise of Edifice is that
GUI designers should only need to worry about *what* is rendered on the screen,
not *how* the content is rendered.
Most existing GUI libraries in Python, such as Tkinter and Qt, operate imperatively.
To create a dynamic application using these libraries,
you must not only think about what to display to the user given state changes,
but also how to issue the commands to achieve the desired effect.

Edifice allows you to describe what should be rendered given the current state,
leaving the how to the library.
User interactions update the state, and state changes update the GUI.
You only need to specify what is to be displayed given the current state and how
user interactions modify this state.
Edifice will ensure that
the displayed widgets always correspond to the internal state.
For example, you can write:

.. code-block:: python

	number, set_number = use_state(0)

    with View():
        Button("Add 5", on_click=set_number(number + 5)
        Label(str(number))

and get the expected result: the GUI always displays
a button and a label displaying the current value of :code:`number`.
Clicking the button adds 5 to the number,
and Edifice will handle updating the GUI.

Edifice is designed to make GUI applications easier for humans to reason about.
Thus, the displayed GUI always reflect the internal state,
even if an exception occurs part way through rendering —
in that case, the state changes are unwound,
the display is unchanged.

Declarative UIs are also easier for developer tools to work with.
Edifice provides two key features to make development easier:

- Dynamic reloading of changed source code. This is especially useful for tweaking the looks of your application, allowing you to test if the margin should be 10px or 15px instantly without closing the app, reopening it, and waiting for everything to load.
- Element inspector. Similar to the Inspect Elements tool of a browser, the component inspector will show you all Elements in your application along with the props and state, allowing you to examine the internal state of your complex component without writing a million print statements.
  Since the UI is specified as a (pure) function of state, the state you see completely describes your application,
  and you can even do things like rewinding to a previous state.

QML is another declarative GUI framework for Qt. Edifice differs from QML in these aspects:

- Edifice interfaces are created purely in Python, whereas QML is written using a custom markup language.
- Because Edifice interfaces are built in Python code, binding Python code to the declared UI is much more straightforward.
- Edifice makes it easy to create dynamic applications. It's easy to create, shuffle, and destroy widgets because the interface is written in Python code. QML assumes a much more static interface.

An analogy is, QML is like HTML + JavaScript, whereas Edifice is like React.js.
While QML and HTML are both declarative UI frameworks,
they require imperative logic to add dynamism.
Edifice and React allow fully dynamic applications to be specified declaratively.

Edifice is still currently under development, and some Qt widgets/functionality are not supported.
However, it is easy to interface with Qt, either :ref:`incorporating a Qt Widget<custom_widget>` into an Edifice component,
:doc:`use Qt commands directly<stubs/edifice.Reference>` with an existing Edifice component,
or :doc:`incorporating Edifice components<stubs/stubs/edifice.App.export_widgets>` in a Qt application.


Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   tutorial
   examples
   edifice
   base_components
   hooks
   utilities
   styling
   developer_tools
   versions
   future

License and Code Availability
-----------------------------

Edifice is released under the `MIT License <https://en.wikipedia.org/wiki/MIT_License>`_.

Edifice uses Qt under the hood, and both PyQt6 and PySide6 are supported.
Note that PyQt6 is distributed with the *GPL* license while PySide6 is distributed
under the more flexible *LGPL* license.
See `PyQt vs PySide Licensing <https://www.pythonguis.com/faq/pyqt-vs-pyside/>`_.

The source code is avaliable `on GitHub <https://github.com/pyedifice/pyedifice>`_.

Support
-------

Submit bug reports or feature requests on
`Github Issues <https://github.com/pyedifice/pyedifice/issues>`_.

Submit any questions on
`Github Discussions <https://github.com/pyedifice/pyedifice/discussions>`_.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
