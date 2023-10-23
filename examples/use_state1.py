#
# python examples/use_state1.py
#

import asyncio as asyncio
import sys, os
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
from edifice import App, Element, View, Label, Button

class UseState1(Element):
    def __init__(self):
        super().__init__()

    def render(self):
        show, set_show = self.use_state(False)
        if show:
            return View()(
                Button(
                    title="Hide",
                    on_click=lambda ev: set_show(False)
                ),
                TestComp()
            )
        else:
            return View()(
                Button(
                    title="Show",
                    on_click=lambda ev: set_show(True)
                )
            )
class TestComp(Element):
    def __init__(self):
        super().__init__()
        self.count = 0

    async def handle_click(self, _):
        self.set_state(count=self.count + 1)

    def render(self):
        print("TestComp instance " + str(id(self)))
        x, x_setter = self.use_state(0)
        return View(
            style={
                "align":"top"
            }
        )(
            Button(
                title="Count " + str(self.count),
                on_click=self.handle_click
            ),
            Button(
                title="State " + str(x),
                on_click=lambda ev: x_setter(x+1)
            ),
            Button(
                title="Exit",
                on_click=lambda ev: asyncio.get_event_loop().call_soon(asyncio.get_event_loop().stop)
            ),
            *[Label(text=str(i)) for i in range(x)],
        )

if __name__ == "__main__":
    my_app = App(UseState1())
    with my_app.start_loop() as loop:
        loop.run_forever()
