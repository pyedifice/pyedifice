#
# python examples/flowview1.py
#

import edifice as ed


@ed.component
def Main(self):
    with ed.Window():
        with ed.VBoxView(
            style={
                # We cannot align to center, it doesn't work with FlowView. TODO
                # "align":"center"
            },
        ):
            with ed.FlowView():
                for i in range(100):
                    with ed.VBoxView(style={"margin": 5}):
                        with ed.ButtonView(style={"margin": 5}):
                            ed.Label(
                                text="<div style='font-size:20px'>Label " + chr(ord("🦄") + i) + "</>",
                                style={"margin": 5},
                            )


if __name__ == "__main__":
    ed.App(Main()).start()
