Examples
========


Calculator
----------

It's easy to create a good-looking program with Edifice.
In this example, we imitate the look of the MacOS *Calculator* app
in 100 lines of code (most of which is implementing the calculator state machine).

Source code `calculator.py <https://github.com/pyedifice/pyedifice/tree/master/examples/calculator.py>`_.

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

Source code `financial_charts.py <https://github.com/pyedifice/pyedifice/tree/master/examples/financial_charts.py>`_.

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

For comparison, see the Edifice **TodoMVC** source code
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

Source code `harmonic_oscillator.py <https://github.com/pyedifice/pyedifice/tree/master/examples/harmonic_oscillator.py>`_.

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

Source code `7guis_01_counter.py <https://github.com/pyedifice/pyedifice/tree/master/examples/7guis/7guis_01_counter.py>`_

.. figure:: /image/7guis_01_counter.png

..

   `Counter <https://7guis.github.io/7guis/tasks#counter>`_ serves as a gentle introduction to the basics of the
   language, paradigm and toolkit for one of the simplest GUI applications imaginable.

.. code-block:: shell
   :caption: Run in Python environment

   python examples/7guis/7guis_01_counter.py

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-7guis-01-counter

Temperature Converter
--------------------

Source code `7guis_02_temperature_converter.py <https://github.com/pyedifice/pyedifice/tree/master/examples/7guis/7guis_02_temperature_converter.py>`_

.. figure:: /image/7guis_02_temperature_converter.png

..

   `Temperature Converter <https://7guis.github.io/7guis/tasks#temp>`_
   increases the complexity of Counter by having bidirectional data flow between the Celsius and Fahrenheit inputs and
   the need to check the user input for validity.

.. code-block:: shell
   :caption: Run in Python environment

   python examples/7guis/7guis_02_temperature_converter.py

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-7guis-02-temperature-converter

Flight Booker
-------------

Source code `7guis_03_flight_booker.py <https://github.com/pyedifice/pyedifice/tree/master/examples/7guis/7guis_03_flight_booker.py>`_

.. figure:: /image/7guis_03_flight_booker.png

..

   The focus of `Flight Booker <https://7guis.github.io/7guis/tasks#flight>`_ lies on modelling constraints between
   widgets on the one hand and modelling constraints within a widget on the other hand.

.. code-block:: shell
   :caption: Run in Python environment

   python examples/7guis/7guis_03_flight_booker.py

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-7guis-03-flight-booker

Timer
-----

Source code `7guis_04_timer.py <https://github.com/pyedifice/pyedifice/tree/master/examples/7guis/7guis_04_timer.py>`_

.. figure:: /image/7guis_04_timer.png

..

   `Timer <https://7guis.github.io/7guis/tasks#timer>`_ deals with concurrency in the sense that a timer process that
   updates the elapsed time runs concurrently to the user’s interactions with the GUI application.

.. code-block:: shell
   :caption: Run in Python environment

   python examples/7guis/7guis_04_timer.py

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-7guis-04-timer

CRUD
----

Source code `7guis_05_crud.py <https://github.com/pyedifice/pyedifice/tree/master/examples/7guis/7guis_05_crud.py>`_

.. figure:: /image/7guis_05_crud.png

..

   `CRUD <https://7guis.github.io/7guis/tasks#crud>`_ (Create, Read, Update and Delete) represents a typical graphical
   business application.

.. code-block:: shell
   :caption: Run in Python environment

   python examples/7guis/7guis_05_crud.py

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-7guis-05-crud

Circle Drawer
-------------

Source code `7guis_06_circle_drawer.py <https://github.com/pyedifice/pyedifice/tree/master/examples/7guis/7guis_06_circle_drawer.py>`_

.. figure:: /image/7guis_06_circle_drawer.png

..

   `Circle Drawer <https://7guis.github.io/7guis/tasks#circle>`_ ’s goal is, among other things, to test how good the
   common challenge of implementing an undo/redo functionality for a GUI application can be solved.

.. code-block:: shell
   :caption: Run in Python environment

   python examples/7guis/7guis_06_circle_drawer.py

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-7guis-06-circle-drawer

Cells
-----

Source code `7guis_07_cells.py <https://github.com/pyedifice/pyedifice/tree/master/examples/7guis/7guis_07_cells.py>`_

.. figure:: /image/7guis_07_cells.png

..

   `Cells <https://7guis.github.io/7guis/tasks#cells>`_ is a more authentic and involved task that tests if a
   particular approach also scales to a somewhat bigger application. The two primary GUI-related challenges are
   intelligent propagation of changes and widget customization.

.. code-block:: shell
   :caption: Run in Python environment

   python examples/7guis/7guis_07_cells.py

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-7guis-07-cells

This is a modified implementation of **Cells**.

The spreadsheet is *10×10* instead of *100×100*.

We can use the
`Qt supported HTML subset <https://doc.qt.io/qtforpython-6.5/overviews/richtext-html-subset.html>`_
to markup text in the cells.

Cells Formulas
^^^^^^^^^^^^^^

I didn’t feel like implementing the whole
`SCells spreadsheet formula language <https://www.artima.com/pins1ed/the-scells-spreadsheet.html#33.3>`_
so instead the spreadsheet formula language is Python.

If a cell begins with an equals sign :code:`=` then it is parsed as a formula expression.
The formula expression following :code:`=` will be passed to Python
`eval <https://docs.python.org/3/library/functions.html#eval>`_
with one variable in scope: :code:`sheet`.

.. code-block:: python
   :caption: sheet variable type

   sheet:tuple[tuple[int | float | str, ...], ...]

The formula expression can use the :code:`sheet` variable to access the other cells
in the spreadsheet.
The :code:`sheet` variable is the spreadsheet as a tuple of tuples.
It is column-major order, and the indices are *0*-based.
The formula expression must evaluate to :code:`int`, :code:`float`, or :code:`str`.

Python
`filtered list comprehensions <https://docs.python.org/3.13/tutorial/datastructures.html#list-comprehensions>`_
are good for writing formulas. The
`Common Sequence Operations <https://docs.python.org/3.13/library/stdtypes.html#common-sequence-operations>`_
also supply a lot of the features of a spreadsheet formula language.

.. code-block:: python
   :caption: Example formula: Copy the value from column *5*, row *6*

   =sheet[5][6]

.. code-block:: python
   :caption: Example formula: Sum all numbers in column *0*

   =sum(x for x in sheet[0] if isinstance(x, (int, float)))

.. code-block:: python
   :caption: Example formula: Join all strings in row *0*

   =",".join(col[0] for col in sheet if isinstance(col[0], str))

.. code-block:: python
   :caption: Example formula: The maximum of all numbers in the range of  columns *0 to 2*, rows *0 to 4*

   =max(x for c in sheet[:3] for x in c[:5] if isinstance(x, (int, float)))

.. code-block:: python
   :caption: Example formula: Sum of all numbers in the range of columns *1 to 2*, rows *1 to 4*

   =sum(x for c in sheet[1:3] for x in c[1:5] if isinstance(x, (int, float)))