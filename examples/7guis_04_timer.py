#
# https://7guis.github.io/7guis/tasks#timer
#

from __future__ import annotations

import asyncio

import edifice as ed


@ed.component
def Main(self):
    elapsed_time, elapsed_time_set = ed.use_state(0.0)
    duration, duration_set = ed.use_state(20)

    async def timer_tick():
        while True:
            elapsed_time_set(lambda old: min(old + 0.1, float(duration)))
            await asyncio.sleep(0.1)

    ed.use_async(timer_tick, duration)

    with ed.Window(title="Timer"):
        with ed.VBoxView(style={"padding": 10}):
            with ed.HBoxView():
                ed.Label(text="Elapsed Time:")
                if duration > 0:
                    ed.ProgressBar(
                        value=int(elapsed_time / float(duration) * 1000.0),
                        min_value=0,
                        max_value=1000,
                        format="",
                    )
            ed.Label(
                text=f"{elapsed_time:.1f}",
                style={"margin-top": 10, "margin-bottom": 10},
            )
            with ed.HBoxView():
                ed.Label(text="Duration:")
                ed.Slider(
                    value=duration,
                    min_value=0,
                    max_value=30,
                    on_change=duration_set,
                )
            ed.Button(
                title="Reset",
                on_click=lambda _: elapsed_time_set(0.0),
            )


if __name__ == "__main__":
    ed.App(Main()).start()
