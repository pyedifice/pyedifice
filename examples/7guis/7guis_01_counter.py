#
# https://7guis.github.io/7guis/tasks#counter
#

from __future__ import annotations

import edifice as ed


@ed.component
def Main(self):
    ed.use_palette_edifice()
    count, count_set = ed.use_state(0)

    with ed.Window(title="Counter"):
        with ed.HBoxView(style={"padding": 10}):
            ed.Label(text=str(count), style={"align": "center"})
            ed.Button(title="Count", on_click=lambda _ev: count_set(count + 1))


if __name__ == "__main__":
    ed.App(Main()).start()
