#
# python examples/flowview1.py
#

import edifice as ed
from edifice import FlowView
from edifice import ButtonView


@ed.component
def myComponent(self):
    def mkElement(j):
        with ed.View(style={"margin": 5}):
            with ButtonView(style={"margin": 5}):
                ed.Label(text="<div style='font-size:20px'>Label " + chr(ord("🦄") + j) + "</>", style={"margin": 5})

    with ed.Window():
        with ed.View(
            layout="column",
            style={
                # We cannot align to center, it doesn't work with FlowView. TODO
                # "align":"center"
            },
        ):
            with FlowView():
                for i in range(100):
                    mkElement(i)


if __name__ == "__main__":
    ed.App(myComponent()).start()
