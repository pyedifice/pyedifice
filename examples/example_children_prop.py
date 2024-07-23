# https://legacy.reactjs.org/docs/composition-vs-inheritance.html#containment

import typing as tp

import edifice as ed


@ed.component
def MyComponent(
    self: ed.Element,
    children: list[ed.Element] = [],
):
    bgcolor = "blue"
    tree = ed.TreeBuilder()
    with tree + ed.View(
        layout="column",
        style={"align": "top"},
    ):
        for child in children:
            with tree + ed.View(
                style={"background-color": bgcolor, "padding": 10},
            ):
                tree += child
            bgcolor = "blue" if bgcolor == "green" else "green"
    return tree.root()


@ed.component
def Main(self):
    strings: tp.Sequence[
        str
    ] = "Callables which take other callables as arguments may indicate that their parameter types are dependent on".split(
        " "
    )
    x, x_set = ed.use_state(0)
    tree = ed.TreeBuilder()
    with tree + ed.Window():
        with tree + ed.View(style={"padding": 20}):
            tree += ed.Slider(
                value=x,
                on_change=x_set,
                min_value=0,
                max_value=len(strings),
                style={"min-width": 200},
            )
            with tree + MyComponent():
                for i in range(0, x):
                    tree += ed.Label(text=strings[i])
    return tree.root()


if __name__ == "__main__":
    ed.App(Main()).start()
