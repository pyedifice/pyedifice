#
# python examples/flowview1.py
#

import edifice as ed
from edifice import FlowView
from edifice import ButtonView
from edifice.engine import TreeBuilder


@ed.component
def myComponent(self):
    def mkElement(j):
        return ed.View(style={"margin": 5})(
            ButtonView(style={"margin": 5})(
                ed.Label(text="<div style='font-size:20px'>Label " + chr(ord("🦄") + j) + "</>", style={"margin": 5}),
            )
        )

    put = TreeBuilder()
    with put(ed.Window()) as root:
        with put(
            ed.View(
                layout="column",
                style={
                    # We cannot align to center, it doesn't work with FlowView. TODO
                    # "align":"center"
                },
            )
        ):
            with put(FlowView()):
                for i in range(100):
                    put(mkElement(i))
        return root


if __name__ == "__main__":
    ed.App(myComponent()).start()
