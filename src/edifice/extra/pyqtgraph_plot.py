import typing as tp

from edifice.engine import CommandType, PropsDiff, QtWidgetElement

# Import PySide6 or PyQt6 before importing pyqtgraph so that pyqtgraph detects the same
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    pass
else:
    pass

import pyqtgraph as pg


class PyQtPlot(QtWidgetElement[pg.PlotWidget]): # type: ignore  # noqa: PGH003
    """
    A **PyQtGraph**
    `PlotWidget <https://pyqtgraph.readthedocs.io/en/latest/api_reference/widgets/plotwidget.html>`_.

    Requires
    `PyQtGraph <https://pyqtgraph.readthedocs.io/en/latest/>`_.

    .. rubric:: Props

    All **props** from :class:`edifice.QtWidgetElement` plus:

    Args:
        plot_fun:
            Function which takes a **PyQtGraph**
            `PlotItem <https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/plotitem.html>`_
            and calls
            `plot() <https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/plotitem.html#pyqtgraph.PlotItem.plot>`_.

            Edifice will call
            `clear() <https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/plotitem.html#pyqtgraph.PlotItem.clear>`_
            before calling :code:`plot_fun`.

    .. rubric:: Usage

    .. important::
        It’s important to import **edifice** before importing **pyqtgraph**, so that **pyqtgraph**
        `detects the same PyQt6 or PySide6 <https://pyqtgraph.readthedocs.io/en/latest/getting_started/how_to_use.html#pyqt-and-pyside>`_
        package used by **edifice**.

    .. code-block:: python

        import numpy as np
        from edifice import View, component
        from edifice.extra.pyqtgraph_plot import PyQtPlot
        import pyqtgraph as pg

        @component
        def Component(self):

            def plot_fun(plot_item: pg.PlotItem):
                xs = np.linspace(-10, 10, 100)
                ys = np.sin(xs)
                plot_item.plot(x=xs, y=ys)

            PyQtPlot(plot_fun=plot_fun)


    If you want a non-interactive plot that doesn’t respond to the mouse,
    you can disable mouse interaction with the plot by setting properties
    on the `PlotItem <https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/plotitem.html>`_.

    .. code-block:: python
        :caption: Disable mouse interaction

        def plot_fun(plot_item: pg.PlotItem):
            plot_item.setMouseEnabled(x=False, y=False)
            plot_item.hideButtons()
            ...

    A more complete way to disable mouse interaction is to set the
    :code:`PlotWidget` to be transparent for mouse events.

    .. code-block:: python
        :caption: Disable mouse interaction

        def plot_fun(plot_item: pg.PlotItem):
            cast(
                pg.PlotWidget, plot_item.getViewWidget()
            ).setAttribute(PySide6.QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    """

    def __init__(self, plot_fun: tp.Callable[[pg.PlotItem], None], **kwargs):
        super().__init__(**kwargs)
        self._register_props(
            {
                "plot_fun": plot_fun,
            },
        )

    def _qt_update_commands(self, widget_trees, diff_props: PropsDiff):
        if self.underlying is None:
            self.underlying = pg.PlotWidget()

        commands = super()._qt_update_commands_super(widget_trees, diff_props, self.underlying) # type: ignore  # noqa: PGH003

        match diff_props.get("plot_fun"):
            case _, propnew:
                plot_fun = tp.cast(tp.Callable[[pg.PlotItem], None], propnew)
                plot_widget = tp.cast(pg.PlotWidget, self.underlying)
                plot_item = tp.cast(pg.PlotItem, plot_widget.getPlotItem())

                def _update_plot(plot_item=plot_item, plot_fun=plot_fun):
                    plot_item.clear()
                    plot_fun(plot_item)

                commands.append(CommandType(_update_plot))

        return commands
