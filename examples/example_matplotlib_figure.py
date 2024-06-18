#
# python examples/example_matplotlib_figure.py
#

import typing as tp
import edifice as ed
from edifice.extra import MatplotlibFigure
import numpy as np

from matplotlib.backend_bases import MouseEvent
from matplotlib.axes import Axes


@ed.component
def Component(self):
    mouse_hover, mouse_hover_set = ed.use_state(tp.cast(tuple[float, float] | None, None))

    def plot(ax: Axes):
        time_range = np.linspace(-10, 10, num=120)
        ax.plot(time_range, np.sin(time_range))
        if mouse_hover is not None:
            # plot a dot on the plotting function at mouse-x
            x = min([max([mouse_hover[0], time_range[0]]), time_range[-1]])
            ax.plot(x, np.sin(x), "ob")

    plot_fun, plot_fun_set = ed.use_state((lambda figure: plot(figure),))

    def handle_house_move(ev: MouseEvent):
        if ev.xdata is not None and ev.ydata is not None:
            mouse_hover_set((ev.xdata, ev.ydata))
        else:
            mouse_hover_set(None)
        plot_fun_set((lambda figure: plot(figure),))

    MatplotlibFigure(plot_fun[0], on_figure_mouse_move=handle_house_move).render()


@ed.component
def Main(self):
    with ed.Window(
        title="Matplotlib Example",
        style={
            "min-width": "200px",
            "min-height": "200px",
        },
    ).render():
        Component().render()


if __name__ == "__main__":
    ed.App(Main()).start()
