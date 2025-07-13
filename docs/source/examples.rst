Examples
========


Calculator
----------

It's easy to create a good-looking program with Edifice.
In this example, we imitate the look of the MacOS *Calculator* app
in 100 lines of code (most of which is implementing the calculator state machine).

The code is available at `calculator.py <https://github.com/pyedifice/pyedifice/tree/master/examples/calculator.py>`_.

.. figure:: /image/example_calculator.png
   :width: 300

.. code-block:: shell
   :caption: Run in Python environment

   python examples/calculator.py

.. code-block:: shell
   :caption: Run in Python environment with :doc:`Edifice Runner<developer_tools>`

   python -m edifice --inspect examples/calculator.py Main

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-calculator

Financial Charting
------------------

In this example, we create a reactive charting application with Edifice
which fetches stock data from `Yahoo Finance <https://pypi.org/project/yfinance/>`_.

The code is available at `financial_charts.py <https://github.com/pyedifice/pyedifice/tree/master/examples/financial_charts.py>`_.

.. figure:: /image/example_financial_charting4.png
   :width: 600

.. code-block:: shell
   :caption: Run in Python environment

   python examples/financial_charts.py

.. code-block:: shell
   :caption: Run in Python environment with :doc:`Edifice Runner<developer_tools>`

   python -m edifice --inspect examples/financial_charts.py Main

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-financial-charting


TodoMVC
-------

An implementation of `TodoMVC <https://todomvc.com/>`_ in Edifice.

**TodoMVC** is a simple todo list program written in many JavaScript frameworks,
so that web developers can compare the frameworks by comparing the **TodoMVC**
implementations.

For comparison, the Edifice **TodoMVC** program is available at
`todomvc.py <https://github.com/pyedifice/pyedifice/tree/master/examples/todomvc.py>`_.

.. figure:: /image/example_todomvc.png
   :width: 500

.. code-block:: shell
   :caption: Run in Python environment

   python examples/todomvc.py

.. code-block:: shell
   :caption: Run in Python environment with :doc:`Edifice Runner<developer_tools>`

   python -m edifice --inspect examples/todomvc.py Main

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-todomvc

Harmonic Oscillator
-------------------

An example of animation in Edifice.

The code is available at `harmonic_oscillator.py <https://github.com/pyedifice/pyedifice/tree/master/examples/harmonic_oscillator.py>`_.

.. figure:: /image/example_harmonic_oscillator2.png
   :width: 500

.. code-block:: shell
   :caption: Run in Python environment

   python examples/harmonic_oscillator.py

.. code-block:: shell
   :caption: Run in Python environment with :doc:`Edifice Runner<developer_tools>`

   python -m edifice --inspect examples/harmonic_oscillator.py Main

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-harmonic-oscillator


|

|

|

|

7GUIs Tasks
===========

These examples implement
`The 7 Tasks <https://7guis.github.io/7guis/tasks>`_
in Edifice for
`7Guis: A GUI Programming Benchmark <https://7guis.github.io/7guis/>`_

Counter
-------

   `Counter <https://7guis.github.io/7guis/tasks#counter>`_ serves as a gentle introduction to the basics of the
   language, paradigm and toolkit for one of the simplest GUI applications imaginable.

`7guis_01_counter.py <https://github.com/pyedifice/pyedifice/tree/master/examples/7guis/7guis_01_counter.py>`_

.. code-block:: shell
   :caption: Run in Python environment

   python examples/7guis/7guis_01_counter.py

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-7guis-01-counter

Temperature Converter
--------------------

   `Temperature Converter <https://7guis.github.io/7guis/tasks#temp>`_
   increases the complexity of Counter by having bidirectional data flow between the Celsius and Fahrenheit inputs and
   the need to check the user input for validity.

`7guis_02_temperature_converter.py <https://github.com/pyedifice/pyedifice/tree/master/examples/7guis/7guis_02_temperature_converter.py>`_

.. code-block:: shell
   :caption: Run in Python environment

   python examples/7guis/7guis_02_temperature_converter.py

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-7guis-02-temperature-converter

Flight Booker
-------------

   The focus of `Flight Booker <https://7guis.github.io/7guis/tasks#flight>`_ lies on modelling constraints between
   widgets on the one hand and modelling constraints within a widget on the other hand.

`7guis_03_flight_booker.py <https://github.com/pyedifice/pyedifice/tree/master/examples/7guis/7guis_03_flight_booker.py>`_

.. code-block:: shell
   :caption: Run in Python environment

   python examples/7guis/7guis_03_flight_booker.py

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-7guis-03-flight-booker

Timer
-----

   `Timer <https://7guis.github.io/7guis/tasks#timer>`_ deals with concurrency in the sense that a timer process that
   updates the elapsed time runs concurrently to the user’s interactions with the GUI application.

`7guis_04_timer.py <https://github.com/pyedifice/pyedifice/tree/master/examples/7guis/7guis_04_timer.py>`_

.. code-block:: shell
   :caption: Run in Python environment

   python examples/7guis/7guis_04_timer.py

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-7guis-04-timer

CRUD
----

   `CRUD <https://7guis.github.io/7guis/tasks#crud>`_ (Create, Read, Update and Delete) represents a typical graphical
   business application.

`7guis_05_crud.py <https://github.com/pyedifice/pyedifice/tree/master/examples/7guis/7guis_05_crud.py>`_

.. code-block:: shell
   :caption: Run in Python environment

   python examples/7guis/7guis_05_crud.py

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-7guis-05-crud

Circle Drawer
-------------

   `Circle Drawer <https://7guis.github.io/7guis/tasks#circle>`_ ’s goal is, among other things, to test how good the
   common challenge of implementing an undo/redo functionality for a GUI application can be solved.

`7guis_06_circle_drawer.py <https://github.com/pyedifice/pyedifice/tree/master/examples/7guis/7guis_06_circle_drawer.py>`_

.. code-block:: shell
   :caption: Run in Python environment (requires `pyqtgraph <https://pypi.org/project/pyqtgraph/>`_)

   python examples/7guis/7guis_06_circle_drawer.py

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-7guis-06-circle-drawer

Cells
-----

   `Cells <https://7guis.github.io/7guis/tasks#cells>`_ is a more authentic and involved task that tests if a
   particular approach also scales to a somewhat bigger application. The two primary GUI-related challenges are
   intelligent propagation of changes and widget customization.

`7guis_07_cells.py <https://github.com/pyedifice/pyedifice/tree/master/examples/7guis/7guis_07_cells.py>`_

This is only a partial implementation of **Cells**. The basic GUI works but the formula language evaluation is not
fully implemented yet.

The spreadsheet is *10×10* instead of *100×100*.

Formulas which are working:

- `=2` evaluates to `2`
- `=B2` evaluates to the value of cell `B2`, recursively.

.. code-block:: shell
   :caption: Run in Python environment

   python examples/7guis/7guis_07_cells.py

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-7guis-07-cells