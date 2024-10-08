#
# python examples/flowview1.py
#

import edifice as ed


@ed.component
def Main(self):
    chars, chars_set = ed.use_state(50)
    with ed.Window():
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
                # for i in range(chars):
                for i in range(100-chars, 100):
                    with ed.VBoxView(style={"padding": 5}).set_key(chr(ord("🦄") + i)):
                        with ed.ButtonView(style={"padding": 5}):
                            ed.Label(
                                text="Label " + chr(ord("🦄") + i),
                                style={
                                    "margin": 5,
                                    "font-size": 20,
                                    "font-family": "Segoe UI Emoji",
                                },
                            )
        ed.Label("end", style={"align":"top"})


if __name__ == "__main__":
    ed.App(Main()).start()
