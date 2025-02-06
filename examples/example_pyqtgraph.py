#
# python examples/example_pyqtgraph.py
#

import typing as tp

import numpy as np

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtGui
else:
    from PySide6 import QtGui

import pyqtgraph as pg

import edifice as ed
from edifice.extra.pyqtgraph_plot import PyQtPlot

pg.setConfigOption("antialias", True)


@ed.component
def Component(self):
    x_min, x_min_set = ed.use_state(-10.0)

    def plot_fn(plot_item: pg.PlotItem):
        plot_item.setMouseEnabled(x=False, y=False)  # type: ignore  # noqa: PGH003
        plot_item.hideButtons()
        grad = QtGui.QLinearGradient(0, -1.0, 0, 1.0)
        grad.setColorAt(0.0, pg.mkColor((127, 127, 127, 0)))
        grad.setColorAt(0.8, pg.mkColor((127, 127, 127, 100)))
        brush = QtGui.QBrush(grad)

        pen = pg.mkPen(width=2, color=pg.mkColor((255, 255, 255, 255)))

        xs = np.linspace(x_min, x_min + 20.0, 100)
        ys = np.sin(xs)
        plot_item.plot(x=xs, y=ys, pen=pen, fillLevel=-1.0, brush=brush)

    with ed.VBoxView():
        with ed.HBoxView(style={"align": "left"}):
            with ed.ButtonView(
                on_trigger=lambda _: x_min_set(x_min + 1.0),
                style={"padding": 10},
            ):
                ed.Label("Increment x_min")
            ed.Label(
                text="F11 toggle full screen",
                style={"margin-left": 10},
            )
        PyQtPlot(
            plot_fun=plot_fn,
        )


@ed.component
def Main(self):
    full_screen, full_screen_set = ed.use_state(False)

    def handle_key_down(event: QtGui.QKeyEvent):
        if event.key() == QtGui.Qt.Key.Key_F11:
            full_screen_set(not full_screen)

    def handle_window_state(old_state, new_state):
        # print(f"Window state changed from {old_state} to {new_state}")
        pass

    with ed.Window(
        title="PyQtPlot Example",
        _size_open=(800, 600),
        full_screen=full_screen,
        on_key_down=handle_key_down,
        on_window_state_change=handle_window_state,
    ):
        Component()


if __name__ == "__main__":
    ed.App(Main()).start()
