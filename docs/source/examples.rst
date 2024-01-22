Examples
========


Calculator
----------

It's easy to create a good-looking program with Edifice.
In this example, we imitate the look of the MacOS *Calculator* app
in 100 lines of code (most of which is implementing the calculator state machine).

The code is available at `calculator.py <https://github.com/pyedifice/pyedifice/tree/master/examples/calculator.py>`_.

.. image:: /image/example_calculator.png
   :width: 300

.. code-block:: shell
   :caption: Run in Python environment

   python -m edifice examples/calculator.py Main

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-calculator

Financial Charting
------------------

In this example, we create a reactive charting application with Edifice.
We allow arbitrary number of plots to be made on the same axis.
For each plot, the source for the x-axis and y-axis data can be specified by the user.
The source data could be the date, the close price, or the volume of a stock.
The data in each axis can also be transformed by an EMA operator,
which computes a moving average over the past n days (with n adjustable by a slider).
And of course, everything is reactive --- there's no "plot" button that the user needs to press to render the chart.

All this is possible in under 200 lines of code and straightforward logic:
there's an underlying description of everything that is plotted.
This description is shown to the user in two ways:
the "textual" description via dropdowns and input elements,
and a visual rendering in the form of a graph.
Users can interact with the textual display and thereby update the plot description.

The code is available at `financial_charts.py <https://github.com/pyedifice/pyedifice/tree/master/examples/financial_charts.py>`_.

.. figure:: /image/example_financial_charting1.png
   :width: 600

.. figure:: /image/example_financial_charting2.png
   :width: 600

.. code-block:: shell
   :caption: Run in Python environment

   python -m edifice examples/financial_charts.py Main

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

   python -m edifice examples/todomvc.py Main

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-todomvc

Harmonic Oscillator
-------------------

An example showing animation. The animation was rendered at 30 FPS (the GIF is only at 12 FPS so you won't be able to tell).
You can interactively set the frequency and damping factors and instantly see the result,
both in a graph and in the animation.
Python of course has great numeric libraries, so we can work with complex numbers.

The code is available at `harmonic_oscillator.py <https://github.com/pyedifice/pyedifice/tree/master/examples/harmonic_oscillator.py>`_.

.. figure:: /image/example_harmonic_oscillator.gif
   :width: 500

.. code-block:: shell
   :caption: Run in Python environment

   python -m edifice examples/harmonic_oscillator.py Main

.. code-block:: shell
   :caption: Run with `Nix <https://determinate.systems/posts/nix-run>`__

   nix run github:pyedifice/pyedifice#example-harmonic-oscillator
