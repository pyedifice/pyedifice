from __future__ import annotations

import typing as tp

from edifice.base_components.base_components import CommandType, QtWidgetElement
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6":
    pass
else:
    pass

from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

if tp.TYPE_CHECKING:
    from matplotlib.backend_bases import MouseEvent


class MatplotlibFigure(QtWidgetElement):
    """
    A **matplotlib** `Figure <https://matplotlib.org/stable/api/figure_api.html#matplotlib.figure.Figure>`_.

    Requires `matplotlib <https://matplotlib.org/stable/>`_.

    Example::

        from matplotlib.axes import Axes
        import numpy as np
        from edifice.extra import MatplotlibFigure

        def plot_fun(ax:Axes):
            time_range = np.linspace(-10, 10, num=120)
            ax.plot(time_range, np.sin(time_range))

        MatplotlibFigure(plot_fun=plot_fun)

    Args:
        plot_fun:
            Function which takes **matplotlib**
            `Axes <https://matplotlib.org/stable/api/axes_api.html>`_
            and calls
            `Axes.plot <https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.plot.html>`_.
        on_figure_mouse_move:
            Handler for mouse move
            `MouseEvent <https://matplotlib.org/stable/api/backend_bases_api.html#matplotlib.backend_bases.MouseEvent>`_.
    """

    def __init__(
        self,
        plot_fun: tp.Callable[[Axes], None],
        on_figure_mouse_move: tp.Callable[[MouseEvent], None] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props(
            {
                "plot_fun": plot_fun,
                "on_figure_mouse_move": on_figure_mouse_move,
            },
        )
        self.underlying: FigureCanvasQTAgg | None = None
        self.subplots: Axes | None = None
        self.current_plot_fun: tp.Callable[[Axes], None] | None = None
        self.on_mouse_move_connect_id: int | None = None

    def _qt_update_commands(self, children, newprops):
        if self.underlying is None:
            # Default to maximum figsize https://matplotlib.org/stable/api/figure_api.html#matplotlib.figure.figaspect
            # Constrain the Figure by putting it in a smaller View, it will resize itself correctly.
            self.underlying = FigureCanvasQTAgg(Figure(figsize=(16.0, 16.0)))
            self.subplots = tp.cast(Axes, self.underlying.figure.subplots())  # TODO is this cast valid?
        assert self.underlying is not None
        assert self.subplots is not None

        commands = super()._qt_update_commands_super(children, newprops, self.underlying, None)

        if "plot_fun" in newprops:

            def _command_plot_fun(self):
                self.current_plot_fun = tp.cast(tp.Callable[[Axes], None], self.props.plot_fun)
                self.subplots.clear()
                self.current_plot_fun(self.subplots)
                self.underlying.draw()
                # alternately we could do draw_idle() here, but I don't think it's
                # any better and it messes up the mouse events.

            commands.append(CommandType(_command_plot_fun, self))
        if "on_figure_mouse_move" in newprops:

            def _command_mouse_move(self):
                if self.on_mouse_move_connect_id is not None:
                    self.underlying.mpl_disconnect(self.on_mouse_move_connect_id)
                if newprops["on_figure_mouse_move"] is not None:
                    self.on_mouse_move_connect_id = self.underlying.mpl_connect(
                        "motion_notify_event",
                        newprops["on_figure_mouse_move"],
                    )
                else:
                    self.on_mouse_move_connect_id = None

            commands.append(CommandType(_command_mouse_move, self))
        return commands
