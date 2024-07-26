# https://legacy.reactjs.org/docs/composition-vs-inheritance.html#containment

from __future__ import annotations

import typing as tp

import edifice as ed


@ed.component
def Leaf(self: ed.Element, text: str) -> None:
    # Check that the component lifecycle is correct for child_place
    def printcreatedestroy():
        print("  mount " + text)

        def printdestroy():
            print("unmount " + text)

        return printdestroy

    ed.use_effect(printcreatedestroy, ())

    ed.Label(text=text)


@ed.component
def ViewBackground(self: ed.Element, bgcolor: str, children: tuple[ed.Element, ...] = ()) -> None:
    with ed.VBoxView(style={"background-color": bgcolor, "padding": 10}):
        ed.child_place(children[0])


@ed.component
def MyComponent(
    self: ed.Element,
    *,
    children: tuple[ed.Element, ...] = (),
) -> None:
    bgcolor = "blue"
    with ed.VBoxView(
        style={"align": "top"},
    ):
        for child in children:
            # This is a bit wierd.
            # To get the correct lifecycle for the Leaf, we need to use the
            # the _key of the child.
            # That's not terrible though.
            with ViewBackground(bgcolor).set_key(child._key):
                ed.child_place(child)
            bgcolor = "blue" if bgcolor == "green" else "green"


@ed.component
def Main(self: ed.Element) -> None:
    strings: tp.Sequence[str] = (
        "Callables which take other callables as arguments may indicate that their parameter types are dependent on".split(
            " ",
        )
    )
    with ed.Window():
        with ed.VBoxView(style={"padding": 20}):
            a, a_set = ed.use_state(0)
            ed.Slider(
                value=a,
                on_change=a_set,
                min_value=0,
                max_value=len(strings),
                style={"min-width": 200},
            )
            x, x_set = ed.use_state(0)
            ed.Slider(
                value=x,
                on_change=x_set,
                min_value=0,
                max_value=len(strings),
                style={"min-width": 200},
            )
            with MyComponent():
                for i in range(a, x):
                    Leaf(text=strings[i]).set_key(strings[i])


if __name__ == "__main__":
    ed.App(Main()).start()
