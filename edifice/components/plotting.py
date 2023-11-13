import time
import threading
from typing import TYPE_CHECKING
from ..base_components import CustomWidget

from ..qt import QT_VERSION
if QT_VERSION == "PyQt6" and not TYPE_CHECKING:
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

try:
    MATPLOTLIB_LOADED = True
    from matplotlib.backends.backend_qtagg import FigureCanvasQT as FigureCanvas
    from matplotlib.figure import Figure as MatplotlibFigure
except ImportError:
    MATPLOTLIB_LOADED = False


class Figure(CustomWidget):

    def __init__(self, plot_fun):
        if not MATPLOTLIB_LOADED:
            raise ValueError("To use the Figure component, you must install matplotlib, e.g. by `pip install matplotlib`")
        self._register_props({
            "plot_fun": plot_fun,
        })
        super().__init__()
        self.figure_added = False
        self.figure_canvas = None
        self.subplots = None
        self.current_plot_fun = None
        self.current_plotted_fun = None
        self.plot_thread_should_run = True
        self.plot_thread = threading.Thread(target=self.plot)

    def _did_mount(self):
        self.plot_thread.start()

    def _will_unmount(self):
        self.plot_thread_should_run = False
        self.plot_thread.join()

    def plot(self):
        time.sleep(0.5)
        while self.plot_thread_should_run:
            plot_fun = self.current_plot_fun
            if plot_fun is not None and self.current_plotted_fun != plot_fun:
                assert self.subplots is not None
                assert self.figure_canvas is not None
                self.subplots.clear() # type: ignore[reportGeneralTypeIssues]
                plot_fun(self.subplots)
                self.figure_canvas.draw()
                self.figure_canvas.figure.tight_layout()
                self.current_plotted_fun = plot_fun
            time.sleep(.016)

    def create_widget(self):
        widget = QtWidgets.QWidget()
        QtWidgets.QVBoxLayout(widget)
        self.figure_added = False
        return widget

    def paint(self, widget, newprops):
        if "plot_fun" in newprops:
            if self.figure_added:
                self.current_plot_fun = self.props.plot_fun
            else:
                self.figure_canvas = FigureCanvas(MatplotlibFigure(figsize=(5, 3)))
                self.subplots = self.figure_canvas.figure.subplots()
                self.current_plot_fun = self.props.plot_fun
                widget.layout().addWidget(self.figure_canvas)
                self.figure_added = True
