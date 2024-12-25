from __future__ import annotations

import operator
from pathlib import Path
from typing import TYPE_CHECKING, cast

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not TYPE_CHECKING:
    from PyQt6.QtWidgets import QFileDialog
else:
    from PySide6.QtWidgets import QFileDialog

from edifice import (
    App,
    Button,
    ButtonView,
    Element,
    HBoxView,
    Icon,
    Label,
    Slider,
    VBoxView,
    Video,
    Window,
    component,
    use_effect,
    use_state,
)


@component
def VideoExample(self: Element) -> None:
    video_path, set_video_path = use_state(cast(Path | None, None))
    target_position, set_target_position = use_state(0.0)
    duration, set_duration = use_state(0.0)
    position, set_position = use_state(0.0)
    paused, set_paused = use_state(False)
    stopped, set_stopped = use_state(False)
    moving_position, set_moving_position = use_state(False)
    volume, set_volume = use_state(100)

    def toggle_play() -> None:
        if stopped:
            set_stopped(False)
            set_paused(False)
        else:
            set_paused(operator.not_)

    def auto_pause() -> None:
        if position >= duration and not moving_position:
            set_stopped(True)

    use_effect(auto_pause, (position, duration, moving_position))

    def select_a_video_file() -> None:
        video_file, _file_filter = QFileDialog.getOpenFileName(caption="Select a video file")
        if video_file:
            set_stopped(False)
            set_paused(False)
            set_moving_position(False)
            set_video_path(Path(video_file))

    with VBoxView(style={"width": 400, "align": "top"}):
        with HBoxView(style={"padding-bottom": 5}):
            Button(
                title="Select a video file" if video_path is None else video_path.stem,
                on_click=lambda _: select_a_video_file(),
            )

        if video_path is None:
            return

        with HBoxView(style={"height": 240, "width": 400}):
            Video(
                str(video_path),
                paused=paused or moving_position,
                stop=stopped,
                volume=volume,
                position=target_position,
                on_position_changed=set_position,
                on_duration_changed=set_duration,
                style={"height": 240},
            )
        if duration > 0:
            Slider(
                int(100 * position / duration),
                on_change=lambda v: set_target_position(v * duration / 100),
                on_mouse_down=lambda _: set_moving_position(True),
                on_mouse_up=lambda _: set_moving_position(False),
            )
        with HBoxView(style={"align": "left"}):
            with HBoxView(style={"width": 150, "align": "left", "padding-right": 10}):
                if volume > 0:
                    Icon(
                        name="headphones",
                        size=20,
                        style={"padding-right": 5, "padding-left": 10},
                    )
                else:
                    Icon(
                        name="slash",
                        size=20,
                        style={"padding-right": 5, "padding-left": 10},
                    )
                Slider(value=volume, on_change=set_volume)
            with ButtonView(
                on_trigger=lambda _: toggle_play(),
                style={"padding": 10, "width": 100, "align": "center"},
            ):
                if not paused and not stopped:
                    Icon(name="pause", size=15)
                else:
                    Icon(name="play", size=15)
            if duration > 0:
                with HBoxView(style={"width": 150, "align": "center", "padding-left": 10}):
                    Label(text=f"{position:0.1f}s / {duration:.1f}s")


@component
def Main(self: Element) -> None:
    with Window(
        style={
            "min-width": 405,
            "min-height": 405,
        },
    ):
        with HBoxView():
            VideoExample()


def main_loop() -> None:
    app = App(Main())
    app.start()


if __name__ == "__main__":
    main_loop()
