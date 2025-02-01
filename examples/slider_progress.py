import asyncio
import typing as tp

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QColor, QValidator
    from PyQt6.QtWidgets import QApplication, QSizePolicy
else:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QPalette, QValidator
    from PySide6.QtWidgets import QApplication, QSizePolicy


def to_percent(x):
    return f"{float(x)/10.0}%"


def from_percent(x):
    try:
        v = float(x.rstrip("%"))
        if v >= 0 and v <= 100.0:
            return int(v * 10.0)
        else:  # noqa: RET505
            return QValidator.State.Intermediate
    except Exception:  # noqa: BLE001
        return QValidator.State.Invalid


@ed.component
def BusyWaitIndicator(
    self,
    visible: bool = True,
    size: int | None = None,
    color: QColor | None = None,
):
    """
    Animated busy wait indicator which looks like ⬤⬤⬤⬤⬤

    If not visible, will still occupy the same layout space but will be
    transparent and animation will not run.
    """

    color_: QColor
    color_ = color if color else QApplication.palette().color(QPalette.ColorRole.Text)
    tick, tick_set = ed.use_state(0)

    async def animation():
        if visible:
            while True:
                await asyncio.sleep(0.2)
                tick_set(lambda t: (t + 1) % 5)

    ed.use_async(animation, visible)

    with ed.HBoxView(
        size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
    ):
        for i in range(0, 5):
            ed.Label(
                text="⬤",
                style={
                    "color": QColor(
                        color_.red(),
                        color_.green(),
                        color_.blue(),
                        40 + (((i - tick) % 5) * 20) if visible else 0,
                    ),
                }
                | {"font-size": size}
                if size
                else {},
            )


@ed.component
def MyComponent(self):
    x, x_set = ed.use_state(0)

    y, y_set = ed.use_state(0)

    def second_slider(value: int):
        x_set(value)

    busywait, busywait_set = ed.use_state(True)

    with ed.VBoxView():
        with ed.HBoxView():
            ed.CheckBox(
                text="Busy Wait Indicator",
                checked=busywait,
                on_change=busywait_set,
            )
            BusyWaitIndicator(visible=busywait, size=8)
        ed.Slider(x, min_value=0, max_value=100, on_change=x_set)
        ed.Slider(x, min_value=0, max_value=100, on_change=second_slider, enable_mouse_scroll=False)
        ed.ProgressBar(
            x,
            min_value=0,
            max_value=100,
            # format="%p% is the progress",
            format=f"{x}% is the progress",
        )
        ed.ProgressBar(0, min_value=0, max_value=0, format="Loading…")
        ed.ProgressBar(
            y,
            min_value=0,
            max_value=1000,
            format="%p% is the progress",
            orientation=Qt.Orientation.Vertical,
            style={"max-height": "100px"},
        )
        ed.SpinInput(
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
        ed.Label(to_percent(y))

        with ed.VScrollView(style={"height": 80}):
            # It's important that if enable_mouse_scroll is False, then wheel scrolls the VScrollView
            ed.Slider(x, min_value=0, max_value=100, on_change=x_set, enable_mouse_scroll=False)
            ed.Slider(x, min_value=0, max_value=100, on_change=x_set, enable_mouse_scroll=False)
            ed.Slider(x, min_value=0, max_value=100, on_change=x_set, enable_mouse_scroll=False)
            ed.Slider(x, min_value=0, max_value=100, on_change=x_set)
            ed.Slider(x, min_value=0, max_value=100, on_change=x_set, enable_mouse_scroll=False)
            ed.Slider(x, min_value=0, max_value=100, on_change=x_set, enable_mouse_scroll=False)
            ed.Slider(x, min_value=0, max_value=100, on_change=x_set, enable_mouse_scroll=False)
            ed.Slider(x, min_value=0, max_value=100, on_change=x_set, enable_mouse_scroll=False)


@ed.component
def Main(self):
    with ed.Window():
        MyComponent()


if __name__ == "__main__":
    ed.App(Main()).start()
