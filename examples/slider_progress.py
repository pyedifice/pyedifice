import sys
import os
import typing as tp
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
from edifice import App, Window, View, component, ProgressBar, Slider
from edifice.hooks import use_state

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import Qt
else:
    from PySide6.QtCore import Qt

@component
def MyComponent(self):
    x, x_set = use_state(0)

    with View(layout="column"):

        Slider(x, min_value=0, max_value=100, on_change=x_set)
        ProgressBar(
            x,
            min_value=0,
            max_value=100,
            format="%p% is the progress",
        )
        ProgressBar(
            0,
            min_value=0,
            max_value=0,
            format="Loading…"
        )
        ProgressBar(
            x,
            min_value=0,
            max_value=100,
            format="%p% is the progress",
            orientation=Qt.Orientation.Vertical,
        )


@component
def Main(self):
    with Window():
        MyComponent()

if __name__ == "__main__":
    App(Main()).start()
