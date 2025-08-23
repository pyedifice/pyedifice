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

    def wheel_move(event: QWheelEvent):
        y_delta = event.angleDelta().y() // 120
        s1_set(lambda s: s + y_delta)

    scroll_events, scroll_events_set = ed.use_state(True)

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
                    checked=s1_wheel,
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
        ed.CheckBox(
            checked=scroll_events,
            text="Scroll Events",
            on_change=scroll_events_set,
        )
        with ed.VScrollView(
            on_scroll_vertical=lambda x: print(f"Vertical Scroll: {x}") if scroll_events else None,  # noqa: T201
            on_scroll_horizontal=lambda x: print(f"Horizontal Scroll: {x}") if scroll_events else None,  # noqa: T201
            on_range_vertical=lambda x1, x2: print(f"Vertical Range: {x1} {x2}") if scroll_events else None,  # noqa: T201
            on_range_horizontal=lambda x1, x2: print(f"Horizontal Range: {x1} {x2}") if scroll_events else None,  # noqa: T201
        ):
            with ed.HBoxView(
                style={
                    "width": 1000,
                    "height": 1000,
                },
            ):
                ed.Label(text="Label1")
        with ed.TableGridView():
            with ed.TableGridRow():
                v_policy_horizontal, v_policy_horizontal_set = ed.use_state(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                h_policy_vertical, h_policy_vertical_set = ed.use_state(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                with ed.VScrollView(
                    scrollbar_policy_horizontal=v_policy_horizontal,
                    scrollbar_policy_vertical=h_policy_vertical,
                ):
                    ed.Dropdown(
                        options=[
                            "vertical ScrollBarAsNeeded",
                            "vertical ScrollBarAlwaysOff",
                            "vertical ScrollBarAlwaysOn",
                        ],
                        selection=h_policy_vertical.value,
                        on_select=lambda val: h_policy_vertical_set(Qt.ScrollBarPolicy(val)),
                    )
                    ed.Dropdown(
                        options=[
                            "horizontal ScrollBarAsNeeded",
                            "horizontal ScrollBarAlwaysOff",
                            "horizontal ScrollBarAlwaysOn",
                        ],
                        selection=v_policy_horizontal.value,
                        on_select=lambda val: v_policy_horizontal_set(Qt.ScrollBarPolicy(val)),
                    )
                    ed.Label(
                        text="VScrollView",
                        style={"width": 200, "height": 200},
                        word_wrap=True,
                    )


@ed.component
def Main(self):
    with ed.Window(
        style={"padding": 30},
        _size_open=(800, 600),
    ):
        MyComponent()


if __name__ == "__main__":
    ed.App(Main()).start()
