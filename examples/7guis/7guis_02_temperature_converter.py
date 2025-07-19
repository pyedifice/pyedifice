#
# https://7guis.github.io/7guis/tasks#temp
#

from __future__ import annotations

import edifice as ed


@ed.component
def Main(self):
    ed.use_palette_edifice()
    tc, tc_set = ed.use_state("0")
    tf, tf_set = ed.use_state("32")

    def tc_changed(celsius: str):
        tc_set(celsius)
        try:
            tf_set(str(float(celsius) * 9 / 5 + 32))
        except ValueError:
            pass

    def tf_changed(fahrenheit: str):
        tf_set(fahrenheit)
        try:
            tc_set(str((float(fahrenheit) - 32) * 5 / 9))
        except ValueError:
            pass

    with ed.Window(title="TempConv"):
        with ed.HBoxView(style={"padding": 10}):
            ed.TextInput(text=tc, on_change=tc_changed)
            ed.Label(text="Celsius = ", style={"margin-left": 10})
            ed.TextInput(text=tf, on_change=tf_changed, style={"margin-left": 10})
            ed.Label(text="Fahrenheit", style={"margin-left": 10})


if __name__ == "__main__":
    ed.App(Main()).start()
