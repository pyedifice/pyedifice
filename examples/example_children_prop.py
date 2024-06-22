# https://legacy.reactjs.org/docs/composition-vs-inheritance.html#containment

import typing as tp

import edifice as ed


@ed.component
def MyComponent(
    self: ed.Element,
    children: list[ed.Element] = [],
):
    bgcolor = "blue"
    put = ed.TreeBuilder()
    with put(
        ed.View(
            layout="column",
            style={"align": "top"},
        )
    ) as root:
        for child in children:
            with put(
                ed.View(
                    style={"background-color": bgcolor, "padding": 10},
                )
            ):
                put(child)
            bgcolor = "blue" if bgcolor == "green" else "green"
    return root


@ed.component
def Main(self):
    strings: tp.Sequence[
        str
    ] = "Callables which take other callables as arguments may indicate that their parameter types are dependent on".split(
        " "
    )
    x, x_set = ed.use_state(0)
    put = ed.TreeBuilder()
    with put(ed.Window()) as root:
        with put(ed.View(style={"padding": 20})):
            put(
                ed.Slider(
                    value=x,
                    on_change=x_set,
                    min_value=0,
                    max_value=len(strings),
                    style={"min-width": 200},
                )
            )
            with put(MyComponent()):
                for i in range(0, x):
                    put(ed.Label(text=strings[i]))
    return root


if __name__ == "__main__":
    ed.App(Main()).start()
