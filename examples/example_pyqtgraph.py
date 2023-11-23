#
# python examples/example_pyqtgraph.py
#

import os
import sys
import typing as tp
import numpy as np

# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))

import edifice as ed
from edifice.components.pyqtgraph_plot import Plot
import pyqtgraph as pg

@ed.component
def Component(self):

    def plot_fn(plotwidget:pg.PlotWidget):
        xs = np.linspace(-10, 10, 100)
        ys = np.sin(xs)
        pi = tp.cast(pg.PlotItem, plotwidget.plotItem)
        pi.plot(x=xs, y=ys, clear=True)

    with ed.View():
        ed.Label("pyqtgraph example")
        Plot(plot_fun=plot_fn)


@ed.component
def Main(self):
    with ed.Window("PyQtGraph Example"):
        with ed.View():
            Component()

if __name__ == "__main__":
    ed.App(Main()).start()
