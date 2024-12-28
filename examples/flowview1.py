#
# python examples/flowview1.py
#

import typing as tp

import edifice as ed


@ed.component
def Thing(self, chrord:int, callback:tp.Callable[[], None]):
    with ed.VBoxView(style={"padding": 5}):
        with ed.ButtonView(
            style={"padding": 5},
            on_click=lambda _ev: callback(),
        ):
            ed.Label(
                text="Label " + chr(chrord),
                style={
                    "margin": 5,
                    "font-size": 20,
                    "font-family": "Segoe UI Emoji",
                },
            )
            ed.Label(text=str(id(callback)))

@ed.component
def Main(self):
    chars, chars_set = ed.use_state(50)
    x, x_set = ed.use_state(0)

    # def bind_funcaller():
    #     def funcaller():
    #         print("funcaller")
    #     return funcaller

    def funcaller():
        print("funcaller")

    funcallback = ed.use_memo(lambda: funcaller, ())

    with ed.Window(style={"align":"top"}):
        ed.Slider(
            value=chars,
            on_change=chars_set,
        )
        with ed.VBoxView(
            style={
                # We cannot align to center, it doesn't work with FlowView. TODO
                # "align":"center"
            },
        ):
            with ed.FlowView():
                for i in range(chars):
                # for i in range(100-chars, 100):
                    chrord = ord("🦄") + i
                    Thing(chrord, funcallback).set_key(chr(chrord))
        ed.Label("end", style={"align":"top"})
        ed.Slider(
            value=x,
            on_change=x_set,
        )


if __name__ == "__main__":
    ed.App(Main()).start()
