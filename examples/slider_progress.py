import typing as tp
from edifice import App, Window, View, component, ProgressBar, Slider, SpinInput, Label
from edifice.engine import TreeBuilder
from edifice.hooks import use_state

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtGui import QValidator
    from PyQt6.QtCore import Qt
else:
    from PySide6.QtGui import QValidator
    from PySide6.QtCore import Qt


def to_percent(x):
    return f"{float(x)/10.0}%"


def from_percent(x):
    try:
        v = float(x.rstrip("%"))
        if v >= 0 and v <= 100.0:
            return int(v * 10.0)
        else:
            return QValidator.State.Intermediate
    except Exception:
        return QValidator.State.Invalid


@component
def MyComponent(self):
    x, x_set = use_state(0)

    y, y_set = use_state(0)

    def second_slider(value: int):
        x_set(value)

    tree = TreeBuilder()
    # with put(View(layout="column")) as root:
    with tree + View(layout="column"):
        tree += Slider(x, min_value=0, max_value=100, on_change=x_set)
        tree += Slider(x, min_value=0, max_value=100, on_change=second_slider)
        tree += ProgressBar(
            x,
            min_value=0,
            max_value=100,
            # format="%p% is the progress",
            format=f"{x}% is the progress",
        )
        tree += ProgressBar(0, min_value=0, max_value=0, format="Loading…")
        tree += ProgressBar(
            y,
            min_value=0,
            max_value=1000,
            format="%p% is the progress",
            orientation=Qt.Orientation.Vertical,
            style={"max-height": "100px"},
        )
        tree += SpinInput(
            y,
            min_value=0,
            max_value=1000,
            value_to_text=to_percent,
            text_to_value=from_percent,
            on_change=y_set,
            style={
                "font-size": "20px",
            },
        )
        tree += Label(to_percent(y))

    return tree.root()


@component
def Main(self):
    return Window()(MyComponent())


if __name__ == "__main__":
    App(Main()).start()
