import typing as tp
from ..base_components import QtWidgetElement
from ..engine import _CommandType

from ..qt import QT_VERSION
if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

import pyqtgraph as pg

class Plot(QtWidgetElement):
    """
    A
    `PlotWidget <https://pyqtgraph.readthedocs.io/en/latest/api_reference/widgets/plotwidget.html>`_.

    Requires
    `PyQtGraph <https://pyqtgraph.readthedocs.io/en/latest/>`_.

    Args:
        plot_fun:
            Function which takes **PyQtGraph**
            `PlotWidget <https://pyqtgraph.readthedocs.io/en/latest/api_reference/widgets/plotwidget.html>`_.
            and calls
            `plot() <https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/plotitem.html#pyqtgraph.PlotItem.plot>`_.
    """

    def __init__(
        self,
        plot_fun: tp.Callable[[pg.PlotWidget], None],
        **kwargs
    ):
        self._register_props({
            "plot_fun": plot_fun,
        })
        super().__init__(**kwargs)
        self.current_plot_fun : tp.Callable[[pg.PlotWidget], None] | None = None

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self.underlying = pg.PlotWidget()
        commands: list[_CommandType] = []
        if "plot_fun" in newprops:
            self.current_plot_fun = tp.cast(tp.Callable[[pg.PlotWidget], None], self.props.plot_fun)
            self.current_plot_fun(self.underlying)
        commands.extend(super()._qt_update_commands(children, newprops, newstate, self.underlying, None))
        return commands
