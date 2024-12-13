import typing as tp

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QWheelEvent
else:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QWheelEvent

@ed.component
def MyComponent(self):

    s1, s1_set = ed.use_state(0)
    s2, s2_set = ed.use_state(0)
    s1_wheel, s1_wheel_set = ed.use_state(True)

    def wheel_move(event:QWheelEvent):
        y_delta = event.angleDelta().y() // 120
        s1_set(lambda s: s + y_delta)

    with ed.VBoxView():
        with ed.HBoxView():
                ed.ScrollBar(
                    value=s1,
                    minimum=0,
                    maximum=100,
                    orientation=Qt.Orientation.Vertical,
                    on_value_changed=s1_set,
                    focus_policy=Qt.FocusPolicy.StrongFocus,
                )
                with ed.VBoxView():
                    ed.Label(
                        text=f"Vertical ScrollBar: {s1}",
                        on_mouse_wheel=wheel_move if s1_wheel else None,
                        style={
                            "padding": 30,
                            "border": "3px solid orange",
                        },
                    )
                    ed.CheckBox(
                        checked = s1_wheel,
                        text="Label Wheel Capture",
                        on_change=s1_wheel_set,
                    )

        ed.Label(text=f"Horizontal ScrollBar: {s2}")
        ed.ScrollBar(
            value=s2,
            minimum=0,
            maximum=10,
            orientation=Qt.Orientation.Horizontal,
            on_value_changed=s2_set,
            focus_policy=Qt.FocusPolicy.StrongFocus,
        )
        ed.ScrollBar(
            value=s2,
            minimum=0,
            maximum=10,
            orientation=Qt.Orientation.Horizontal,
            focus_policy=Qt.FocusPolicy.StrongFocus,
        )
        with ed.VScrollView():
            with ed.HBoxView(
                style={
                    "width": 200,
                    "height": 1000,
                },
            ):
                ed.Label(text="Label1")

@ed.component
def Main(self):
    with ed.Window(
        style={"padding": 30},
        _size_open=(800, 600),
    ):
        MyComponent()


if __name__ == "__main__":
    ed.App(Main()).start()
