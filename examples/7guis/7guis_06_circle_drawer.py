#
# https://7guis.github.io/7guis/tasks#circle
#

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, cast

import edifice as ed
from edifice.extra.pyqtgraph_plot import PyQtPlot
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not TYPE_CHECKING:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QBrush, QMouseEvent
    from PyQt6.QtWidgets import QGraphicsEllipseItem, QSizePolicy
else:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QBrush, QMouseEvent
    from PySide6.QtWidgets import QGraphicsEllipseItem, QSizePolicy

import pyqtgraph as pg

pg.setConfigOption("antialias", True)
pg.setConfigOption("background", "white")
pg.setConfigOption("foreground", "black")


@dataclass(frozen=True)
class Circle:
    circle_index: int
    x: float
    y: float
    radius: float


@dataclass(frozen=True)
class ActionAdjust:
    circle_index: int
    radius_new: float


@ed.component
def Main(self):

    width = 600
    height = 400
    radius_default = 25.0

    # History of circle actions. Most recent action is history[-1].
    # It is always true that history[i].circle_index == i.
    history, history_set = ed.use_state(cast(list[Circle | ActionAdjust], []))
    # If an action in the history is at index <= history_index then it has been undone.
    history_index, history_index_set = ed.use_state(cast(int, 0))
    # Index of the currently selected circle in the history, or None if no circle is selected.
    circle_selected, circle_selected_set = ed.use_state(cast(int | None, None))

    # Fold the circles with their adjustments up to the current history index.
    folded_circles: OrderedDict[int, Circle] = OrderedDict()
    for action in history[:history_index]:
        match action:
            case Circle(circle_index=circle_index):
                folded_circles[circle_index] = action
            case ActionAdjust(circle_index=circle_index, radius_new=radius_new):
                folded_circles[circle_index] = replace(
                    folded_circles[circle_index],
                    radius=radius_new,
                )

    def handle_click(event: QMouseEvent):
        # First check if we have right-clicked on an existing circle
        if event.button() == Qt.MouseButton.RightButton:
            for i, circle in reversed(folded_circles.items()):
                x_diff = event.position().x() - circle.x
                y_diff = height - event.position().y() - circle.y
                if (x_diff**2 + y_diff**2) <= circle.radius**2:
                    # If we clicked on an existing circle, select it
                    circle_selected_set(i)
                    return
            circle_selected_set(None)
        # Otherwise if left-click, create a new circle, destroy the undone history.
        elif event.button() == Qt.MouseButton.LeftButton:
            history_set(
                [
                    *history[:history_index],
                    Circle(
                        x=event.position().x(),
                        y=height - event.position().y(),
                        radius=radius_default,
                        circle_index=history_index,
                    ),
                ],
            )
            # When we create a new circle we select the new circle.
            circle_selected_set(history_index)
            history_index_set(history_index + 1)

    def handle_undo(_event: QMouseEvent):
        if history_index > 0:
            history_index_set(history_index - 1)
            # If we undo an action, we also deselect the selected circle.
            circle_selected_set(None)

    def handle_redo(_event: QMouseEvent):
        if history_index < len(history):
            history_index_set(history_index + 1)
            # If we redo an action, we also deselect the selected circle.
            circle_selected_set(None)

    def handle_adjust_value(circle_index: int, radius_new: float):
        # If we adjust a circle, we destroy the undone history.
        new_history = history[:history_index]
        # If the last history item is an adjustment for the same circle,
        # we replace it with the new adjustment.
        if new_history and isinstance(new_history[-1], ActionAdjust) and new_history[-1].circle_index == circle_index:
            new_history[-1] = ActionAdjust(circle_index=circle_index, radius_new=radius_new)
        else:
            new_history.append(ActionAdjust(circle_index=circle_index, radius_new=radius_new))
        history_set(new_history)
        history_index_set(len(new_history))

    def plot_fun(plot_item: pg.PlotItem):
        plot_item.hideButtons()
        plot_item.showAxes(False, showValues=False)
        view_widget = cast("pg.PlotWidget", plot_item.getViewWidget())
        view_widget.setRenderHint(pg.QtGui.QPainter.RenderHint.Antialiasing)
        view_box = cast("pg.ViewBox", plot_item.getViewBox())
        view_box.setMouseEnabled(x=False, y=False)
        view_box.setMenuEnabled(False)
        view_box.setRange(
            xRange=(0.0, width),
            yRange=(0.0, height),
            padding=0.0,
            disableAutoRange=True,
        )
        for i, circle in folded_circles.items():
            circle_item = QGraphicsEllipseItem(
                circle.x - circle.radius,
                circle.y - circle.radius,
                circle.radius * 2,
                circle.radius * 2,
            )
            circle_item.setPen(pg.mkPen(color="black", width=2))
            if circle_selected is not None and circle_selected == i:
                circle_item.setBrush(QBrush("grey"))
            plot_item.addItem(circle_item)

    with ed.Window(title="Circle Drawer"):
        with ed.VBoxView(style={"padding": 10}):
            with ed.HBoxView(style={"padding-bottom": 10, "align": "center"}):
                ed.Button(
                    title="Undo",
                    size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
                    on_click=handle_undo,
                    enabled=history_index > 0,
                )
                ed.Button(
                    title="Redo",
                    size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
                    on_click=handle_redo,
                    enabled=history_index < len(history),
                )
            with ed.VBoxView(style={"width": width, "height": height}):
                PyQtPlot(
                    plot_fun=plot_fun,
                    on_click=handle_click,
                    style={"width": width, "height": height},
                )
        if circle_selected is not None:
            with ed.WindowPopView(
                title="Adjust Circle",
                on_close=lambda _: circle_selected_set(None),
            ):
                with ed.VBoxView(
                    style={"padding": 20, "align": Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop},
                ):
                    circle = folded_circles[circle_selected]
                    ed.Label(text=f"Adjust the diameter of circle at ({circle.x}, {circle.y}).")
                    with ed.HBoxView(style={"padding-top": 10, "align": Qt.AlignmentFlag.AlignHCenter}):
                        with ed.HBoxView(style={"width": 200}):
                            ed.Slider(
                                value=int(circle.radius),
                                min_value=0,
                                max_value=100,
                                on_change=lambda new_value: handle_adjust_value(circle_selected, float(new_value)),
                            )


if __name__ == "__main__":
    ed.App(Main()).start()
