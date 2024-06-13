
# https://legacy.reactjs.org/docs/composition-vs-inheritance.html#containment

import sys
import os
import typing as tp
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))

import edifice as ed

@ed.component
def MyComponent(
    self: ed.Element,
    children:list[ed.Element]=[],
):
    bgcolor = "blue"
    with ed.View(
        layout="column",
        style={"align": "top"},
    ):
        for child in children:
            with ed.View(
                style={"background-color": bgcolor, "padding": 10},
            ):
                ed.child_place(child)
            bgcolor = "blue" if bgcolor == "green" else "green"

@ed.component
def Main(self):
    strings: tp.Sequence[str] = "Callables which take other callables as arguments may indicate that their parameter types are dependent on".split(" ")
    with ed.Window():
        with ed.View(style={"padding": 20}):
            x, x_set = ed.use_state(0)
            ed.Slider(
                value=x,
                on_change=x_set,
                min_value=0,
                max_value=len(strings),
                style={"min-width": 200},
            )
            with MyComponent():
                for i in range(0, x):
                    ed.Label(text=strings[i])


if __name__ == "__main__":
    ed.App(Main()).start()
