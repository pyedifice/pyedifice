#
# python examples/use_effect1.py
#

import asyncio as asyncio
import sys, os
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
from edifice import App, Element, View, Label, Button

class MainComp(Element):
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


    def render(self):

        print("TestComp instance " + str(id(self)))

        x, x_setter = self.use_state(0)

        def setup():
            print("effect setup")
            def cleanup():
                print("effect cleanup")
                pass
            return cleanup
        self.use_effect(setup, x)

        return View(
            style={
                "align":"top"
            }
        )(
            Label(text="Label text"),
            Button(
                title="State " + str(x),
                on_click=lambda ev: x_setter(x+1)
            ),
        )

if __name__ == "__main__":
    my_app = App(MainComp())
    with my_app.start_loop() as loop:
        loop.run_forever()
