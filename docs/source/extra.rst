Extra Elements
==============

Edifice provides a few extra Elements that provide useful but non-core
features.

These Elements have additional dependencies, so they are
not included in the :code:`edifice` module.

Importing one of these extra Elements will require the installation of the
additional dependencies.

.. code-block:: python

    from edifice.extra.matplotlib_figure import MatplotlibFigure

User contributions are of course welcome!

.. currentmodule:: edifice.extra
.. autosummary::
   :toctree: stubs
   :recursive:
   :template: custom-class.rst

   pyqtgraph_plot.PyQtPlot
   matplotlib_figure.MatplotlibFigure
   numpy_image.NumpyImage
   numpy_image.NumpyArray

.. autosummary::
   :toctree: stubs

   numpy_image.NumpyArray_to_QImage