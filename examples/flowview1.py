#
# python -m edifice examples/flowview1.py FlowView1
#

import edifice as ed
from edifice.components.flow_view import FlowView
from edifice.components.button_view import ButtonView

class FlowView1(ed.Component):

    def __init__(self):
        super().__init__()

    def render(self):
        def mkElement(j):
            return ed.View(
                style={
                    "margin": 5
                }
            )( ButtonView(
                    style={
                        "margin":5
                    }
                )(ed.Label(
                    text="<div style='font-size:20px'>Label " + chr(ord("🦄")+j) + "</>",
                    style={
                        "margin":5
                    }
            )))
        # return FlowView()(
        #     *[mkElement(i) for i in range(100)]
        return ed.View(
          layout="column",
          style={
              "align":"center"
              }
        )(FlowView()(
            *[mkElement(i) for i in range(100)]
        ))

if __name__ == "__main__":
    ed.App(FlowView1()).start()
