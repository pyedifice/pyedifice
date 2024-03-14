import typing as tp
from ..base_components import QtWidgetElement
from ..engine import _CommandType

# Import PySide6 or PyQt6 before importing pyqtgraph so that pyqtgraph detects the same
from ..qt import QT_VERSION
if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtGui import QMouseEvent
    from PyQt6.QtCore import QMetaObject
else:
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtCore import QMetaObject, QPointF

import pyqtgraph as pg

# class CustomPlotWidget(pg.PlotWidget):
#     def __init__(self, *args, **kargs):
#         super().__init__(*args, **kargs)
#         self._on_mouse_move: tp.Callable[[QMouseEvent], None] | None = None
#         # self.scene().sigMouseMoved.connect(self._mouse_move)
#
#     # def mouseMoveEvent(self, ev:QMouseEvent):
#     #     super().mouseMoveEvent(ev)
#     #     if self._on_mouse_move is not None:
#     #         self._on_mouse_move(ev)

class PyQtPlot(QtWidgetElement):
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

                with View():
                    PyQtPlot(plot_fun=plot_fun)

    Args:
        plot_fun:
            Function which takes a **PyQtGraph**
            `PlotItem <https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/plotitem.html>`_
            and calls
            `plot() <https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/plotitem.html#pyqtgraph.PlotItem.plot>`_.

            Edifice will call
            `clear() <https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/plotitem.html#pyqtgraph.PlotItem.clear>`_
            before calling :code:`plot_fun`.
        on_plot_mouse_move:
            Handler for mouse move
            `QMouseEvent <https://doc.qt.io/qtforpython/PySide6/QtGui/QMouseEvent.html>`_.
    """

    def __init__(
        self,
        plot_fun: tp.Callable[[pg.PlotItem], None],
        # on_plot_mouse_move: tp.Callable[[QMouseEvent], None] | None = None,
        on_plot_mouse_move: tp.Callable[[QPointF], None] | None = None,
        **kwargs
    ):
        self._register_props({
            "plot_fun": plot_fun,
            "on_plot_mouse_move": on_plot_mouse_move,
        })
        super().__init__(**kwargs)
        self._mouse_moved_connection : QMetaObject.Connection | None = None

    def _qt_update_commands(self, children, newprops, newstate):
        if self.underlying is None:
            self.underlying = pg.PlotWidget()
            # Disable mouse interaction
            # https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/viewbox.html#pyqtgraph.ViewBox.setMouseEnabled
            self.underlying.setMouseEnabled(x=False, y=False)

        commands = super()._qt_update_commands_super(children, newprops, newstate, self.underlying)

        if "plot_fun" in newprops:
            plot_fun = tp.cast(tp.Callable[[pg.PlotItem], None], newprops.plot_fun)
            plot_widget = tp.cast(pg.PlotWidget, self.underlying)
            plot_item = tp.cast(pg.PlotItem, plot_widget.getPlotItem())
            def _update_plot():
                plot_item.clear()
                plot_fun(plot_item)
            commands.append(_CommandType(_update_plot))
        if "on_plot_mouse_move" in newprops:
            plot_widget = tp.cast(pg.PlotWidget, self.underlying)
            # plot_widget._on_mouse_move = newprops.on_plot_mouse_move
            if self._mouse_moved_connection is not None:
                plot_widget.sigSceneMouseMoved.disconnect(self._mouse_moved_connection)
                self._mouse_moved_connection = None
            if newprops.on_plot_mouse_move is not None:
                # self._mouse_moved_connection = plot_widget.sigSceneMouseMoved.connect(newprops.on_plot_mouse_move)
                self._mouse_moved_connection = plot_widget.scene().sigMouseMoved.connect(newprops.on_plot_mouse_move)
            # scene = plot_widget.sceneObj()

        return commands
