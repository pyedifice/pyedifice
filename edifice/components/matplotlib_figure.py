import typing as tp
from ..base_components import QtWidgetElement
from ..engine import _CommandType

from ..qt import QT_VERSION
if QT_VERSION == "PyQt6":
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.axes import Axes

class MatplotlibFigure(QtWidgetElement):
    """
    Interactive **matplotlib** `Figure <https://matplotlib.org/stable/api/figure_api.html#matplotlib.figure.Figure>`_.

    Requires `matplotlib <https://matplotlib.org/stable/>`_.

    Args:
        plot_fun:
            Function which takes **matplotlib**
            `Axes <https://matplotlib.org/stable/api/axes_api.html>`_
            and calls
            `Axes.plot <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.plot.html>`_.
    """

    def __init__(
        self,
        plot_fun: tp.Callable[[Axes], None],
        **kwargs
    ):
        self._register_props({
            "plot_fun": plot_fun,
        })
        super().__init__(**kwargs)
        self.underlying : FigureCanvasQTAgg | None =  None
        self.subplots : Axes | None = None
        self.current_plot_fun : tp.Callable[[Axes], None] | None = None

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            # Default to maximum figsize https://matplotlib.org/stable/api/figure_api.html#matplotlib.figure.figaspect
            # Constrain the Figure by putting it in a smaller View, it will resize itself correctly.
            self.underlying = FigureCanvasQTAgg(Figure(figsize=(16.0,16.0)))
            self.subplots = self.underlying.figure.subplots()
        assert self.underlying is not None
        assert self.subplots is not None
        commands: list[_CommandType] = []
        if "plot_fun" in newprops:
            self.current_plot_fun = tp.cast(tp.Callable[[Axes], None], self.props.plot_fun)
            self.subplots.clear()
            self.current_plot_fun(self.subplots)
            self.underlying.draw_idle()
        commands.extend(super()._qt_update_commands(children, newprops, newstate, self.underlying, None))
        return commands
