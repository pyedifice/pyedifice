#
# python examples/flowview1.py
#

import os, sys
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
import edifice as ed
from edifice.components.flow_view import FlowView
from edifice.components.button_view import ButtonView

@ed.component
def myComponent(self):
    def mkElement(j):
         with ed.View(
            style={
                "margin": 5
            }
        ):
            with ButtonView(
                style={
                    "margin":5
                }
            ):
                ed.Label(
                    text="<div style='font-size:20px'>Label " + chr(ord("🦄")+j) + "</>",
                    style={
                        "margin":5
                    }
                )
    with ed.View(
        layout="column",
        style={
            # We cannot align to center, it doesn't work with FlowView. TODO
            # "align":"center"
            }
    ):
        with FlowView():
            for i in range(100):
                mkElement(i)

if __name__ == "__main__":
    ed.App(myComponent()).start()
