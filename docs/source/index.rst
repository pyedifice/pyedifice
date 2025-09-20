.. edifice documentation master file, created by
   sphinx-quickstart on Sun Jan  3 14:46:57 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. currentmodule:: edifice

Edifice
=======

Edifice is a Python library declarative framework for application user
interfaces.

- Modern **declarative** UI paradigm from web development.
- **100% Python** application development, no language inter-op.
- A **native** Qt desktop app instead of a bundled web browser.
- Fast iteration via **hot-reloading**.

Edifice uses `PySide6 <https://doc.qt.io/qtforpython-6/>`_
or `PyQt6 <https://www.riverbankcomputing.com/static/Docs/PyQt6/introduction.html>`_
as a backend. Edifice is like
`React <https://react.dev/>`_, but with Python instead of JavaScript, and
`Qt Widgets <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/index.html>`_
instead of the HTML DOM.

If you have React experience, you’ll find Edifice easy to learn.
Edifice has function Components, Props, and Hooks just like React.

Getting Started
---------------

.. code-block:: shell
    :caption: Installation from `pypi.org/project/pyedifice <https://pypi.org/project/pyedifice/>`_

    pip install PySide6-Essentials
    pip install pyedifice

.. code-block:: python
    :caption: *Hello World* in Edifice

    from edifice import App, Label, Window, component

    @component
    def HelloWorld(self):
        with Window():
            Label("Hello World!")

    if __name__ == "__main__":
        App(HelloWorld()).start()


For more, see the :doc:`tutorial`.
To understand the core concepts behind Edifice,
see :doc:`edifice`.

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   tutorial

.. toctree::
   :maxdepth: 1

   examples

.. toctree::
   :maxdepth: 2

   api

.. toctree::
   :maxdepth: 2

   developer_tools

.. toctree::
   :maxdepth: 1

   versions

Why Edifice?
------------

Declarative
^^^^^^^^^^^

Most existing GUI libraries in Python, such as Tkinter and Qt, operate imperatively.
To create a dynamic application using these libraries,
you must not only think about *what* widgets to display to the user,
but also *how* to issue the commands to modify the widgets.

With Edifice the developer
need only declare *what* is rendered,
not *how* the content is rendered.

User interactions update the application state, the state renders to a widget tree,
and Edifice modifies the existing widget tree to reflect the new state.

Edifice code looks like this:

.. code-block:: python

    number, set_number = use_state(0)

    with VBoxView():
        Button(title="Add 5", on_click=lambda event: set_number(number+5))
        Label(text=str(number))
        if number > 30 and number < 70:
            Label(
                text="Number is mid",
                style={"color": "green"},
            )

The GUI displays
a button and a label with the current value of :code:`number`.
Clicking the button will add 5 to the :code:`number`.
If the :code:`number` is “mid” then another label will reveal that fact.

Put a GUI on useful Python code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The whole point of Edifice is that it’s a way to put a GUI on useful Python
code. If you have a Python script which does a long-running computation,
Edifice provides an API for running that script while presenting
a responsive GUI to the user.

1. Paste the script into an :code:`worker()` function.
2. Call :func:`run_subprocess_with_callback`
   on that :code:`worker` function with a :func:`use_async`
   Hook. Replace the :code:`print` statements with calls to
   :code:`callback`.

Developer Tools
^^^^^^^^^^^^^^^

- Dynamic hot-reloading of source code changes.
- Element Inspector.

See :doc:`developer_tools` for more details.

Edifice vs. Qt Quick
^^^^^^^^^^^^^^^^^^^^

`Qt Quick <https://doc.qt.io/qtforpython-6/PySide6/QtQuick/>`_ is Qt’s declarative GUI framework for Qt.

Qt Quick programs are written in Python + the
special `QML <https://doc.qt.io/qtforpython-6/overviews/qtdoc-qmlapplications.html>`_ language + JavaScript.

Edifice programs are written in Python.

Because Edifice programs are only Python, binding to the
UI is much more straightforward.
Edifice makes it easy to dynamically create, mutate, shuffle, and destroy
sections of the UI with Python control flow statements
:code:`if` :code:`for` :code:`match`.
Qt Quick assumes a much more static interface.

Qt Quick is like DOM + HTML + JavaScript, whereas Edifice is like React.
QML and HTML are both declarative UI languages but
they require imperative logic in another language for dynamism.
Edifice and React allow fully dynamic applications to be specified
declaratively in one language.

Extendable
^^^^^^^^^^

Edifice does not support every feature of Qt,
but it is easy to interface with Qt, either :ref:`incorporating a Qt Widget<custom_widget>` into an Edifice component,
:doc:`use Qt commands directly<stubs/edifice.Reference>` with an existing Edifice component,
or :doc:`incorporating Edifice components<stubs/stubs/edifice.App.export_widgets>` in a Qt application.

Setuptools Build System
-----------------------

The *Setuptools* :code:`pyproject.toml` specifies the package dependecies.

Because Edifice supports PySide6 and PyQt6 at the same time, neither
are required by :code:`dependencies`. A project which depends
on Edifice should also depend on either
`PySide6-Essentials <https://pypi.org/project/PySide6-Essentials/>`_
or
`PySide6 <https://pypi.org/project/PySide6/>`_
or
`PyQt6 <https://pypi.org/project/PyQt6/>`_.

Add an Edifice dependency to :code:`pyproject.toml`:

.. code-block:: toml

    dependencies = [
        "pyedifice",
        "PySide6-Essentials",
    ]

There are optional dependency groups provided for PySide6-Essentials and PyQt6:

.. code-block:: toml

    dependencies = [
        "pyedifice [PySide6-Essentials]"
    ]

The `requirements.txt` is generated by

.. code-block:: shell

    uv export --format requirements-txt --no-dev > requirements.txt


License and Code Availability
-----------------------------

The source code is avaliable `on github/pyedifice <https://github.com/pyedifice/pyedifice>`_.

Edifice is released under the `MIT License <https://en.wikipedia.org/wiki/MIT_License>`_.

Edifice uses Qt under the hood, and both PyQt6 and PySide6 are supported.
Note that PyQt6 is distributed with the *GPL* license while PySide6 is distributed
under the more flexible *LGPL* license.

See `PyQt vs PySide Licensing <https://www.pythonguis.com/faq/pyqt-vs-pyside/>`_.

    **Can I use PySide for commercial applications?**

    Yes, and you don't need to release your source code to customers. The LGPL only requires you to release any changes you make to PySide itself.

Support
-------

Submit bug reports or feature requests on
`Github Issues <https://github.com/pyedifice/pyedifice/issues>`_.

Submit questions on
`Github Discussions <https://github.com/pyedifice/pyedifice/discussions>`_.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
