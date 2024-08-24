import typing as tp

from edifice.base_components.base_components import CommandType, QtWidgetElement

# Import PySide6 or PyQt6 before importing pyqtgraph so that pyqtgraph detects the same
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    pass
else:
    pass

import pyqtgraph as pg


class PyQtPlot(QtWidgetElement[pg.PlotWidget]):
    """
    A **PyQtGraph**
    `PlotWidget <https://pyqtgraph.readthedocs.io/en/latest/api_reference/widgets/plotwidget.html>`_.

    Requires
    `PyQtGraph <https://pyqtgraph.readthedocs.io/en/latest/>`_.

    It’s important to import **edifice** before importing **pyqtgraph**, so that **pyqtgraph**
    `detects the same PyQt6 or PySide6 <https://pyqtgraph.readthedocs.io/en/latest/getting_started/how_to_use.html#pyqt-and-pyside>`_
    package used by **edifice**.

    Example::

        import numpy as np
        from edifice import View, component
        from edifice.extra import PyQtPlot
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

    Example::

        def plot_fun(plot_item: pg.PlotItem):
            plot_item.setMouseEnabled(x=False, y=False)
            plot_item.hideButtons()
            ...

    A more complete way to disable mouse interaction is to set the
    :code:`PlotWidget` to be transparent for mouse events.

    Example::

        def plot_fun(plot_item: pg.PlotItem):
            cast(
                pg.PlotWidget, plot_item.getViewWidget()
            ).setAttribute(PySide6.QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    Args:
        plot_fun:
            Function which takes a **PyQtGraph**
            `PlotItem <https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/plotitem.html>`_
            and calls
            `plot() <https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/plotitem.html#pyqtgraph.PlotItem.plot>`_.

            Edifice will call
            `clear() <https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/plotitem.html#pyqtgraph.PlotItem.clear>`_
            before calling :code:`plot_fun`.
    """

    def __init__(self, plot_fun: tp.Callable[[pg.PlotItem], None], **kwargs):
        super().__init__(**kwargs)
        self._register_props(
            {
                "plot_fun": plot_fun,
            },
        )

    def _qt_update_commands(self, children, newprops):
        if self.underlying is None:
            self.underlying = pg.PlotWidget()

        commands = super()._qt_update_commands_super(children, newprops, self.underlying)

        if "plot_fun" in newprops:
            plot_fun = tp.cast(tp.Callable[[pg.PlotItem], None], self.props.plot_fun)
            plot_widget = tp.cast(pg.PlotWidget, self.underlying)
            plot_item = tp.cast(pg.PlotItem, plot_widget.getPlotItem())

            def _update_plot():
                plot_item.clear()
                plot_fun(plot_item)

            commands.append(CommandType(_update_plot))

        return commands
