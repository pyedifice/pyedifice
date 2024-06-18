# https://legacy.reactjs.org/docs/composition-vs-inheritance.html#containment

import typing as tp

import edifice as ed


@ed.component
def MyComponent(
    self: ed.Element,
    children: list[ed.Element] = [],
):
    bgcolor = "blue"
    with ed.View(
        layout="column",
        style={"align": "top"},
    ).render():
        for child in children:
            with ed.View(
                style={"background-color": bgcolor, "padding": 10},
            ).render():
                child.render()
            bgcolor = "blue" if bgcolor == "green" else "green"


@ed.component
def Main(self):
    strings: tp.Sequence[
        str
    ] = "Callables which take other callables as arguments may indicate that their parameter types are dependent on".split(
        " "
    )
    with ed.Window().render():
        with ed.View(style={"padding": 20}).render():
            x, x_set = ed.use_state(0)
            ed.Slider(
                value=x,
                on_change=x_set,
                min_value=0,
                max_value=len(strings),
                style={"min-width": 200},
            ).render()
            with MyComponent().render():
                for i in range(0, x):
                    ed.Label(text=strings[i]).render()


if __name__ == "__main__":
    ed.App(Main()).start()
