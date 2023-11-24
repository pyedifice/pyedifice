#
# python examples/example_pyqtgraph.py
#

import os
import sys
import typing as tp
import numpy as np

# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt6":
    from PyQt6 import QtGui
else:
    from PySide6 import QtGui

import edifice as ed
from edifice.components.pyqtgraph_plot import Plot
import pyqtgraph as pg

pg.setConfigOption("antialias", True)

@ed.component
def Component(self):

    x_min, x_min_set = ed.use_state(-10.0)

    def plot_fn(plot_item:pg.PlotItem):
        grad = QtGui.QLinearGradient(0, -1.0, 0, 1.0)
        grad.setColorAt(0.0, pg.mkColor((127,127,127,0)))
        grad.setColorAt(0.8, pg.mkColor((127,127,127,100)))
        brush = QtGui.QBrush(grad)

        pen = pg.mkPen(width=2, color=pg.mkColor((255,255,255,255)))

        xs = np.linspace(x_min, x_min + 20.0, 100)
        ys = np.sin(xs)
        plot_item.plot(x=xs, y=ys, pen=pen, fillLevel=-1.0, brush=brush)

    with ed.View():
        with ed.ButtonView(
            on_trigger=lambda _: x_min_set(x_min + 1.0),
            style={
                "width": "200px",
                "height": "50px",
                "margin": "10px",
            },
        ):
            ed.Label("Increment x_min")
        Plot(plot_fun=plot_fn)

@ed.component
def Main(self):
    with ed.Window("PyQtGraph Example"):
        with ed.View():
            Component()

if __name__ == "__main__":
    ed.App(Main()).start()
