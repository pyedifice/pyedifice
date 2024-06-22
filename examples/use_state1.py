#
# python examples/use_state1.py
#

import asyncio as asyncio
from edifice import App, Window, View, Label, Button, component, use_state
from edifice.engine import TreeBuilder


@component
def UseState1(self):
    show, set_show = use_state(False)
    put = TreeBuilder()

    with put(Window()) as root:
        if show:
            with put(View()):
                put(Button(title="Hide", on_click=lambda ev: set_show(False)))
                put(TestComp())
        else:
            with put(View()):
                put(Button(title="Show", on_click=lambda ev: set_show(True)))
        return root


@component
def TestComp(self):
    print("TestComp instance " + str(id(self)))
    x, x_setter = use_state(0)

    async def handle_click(_):
        x_setter(x + 1)

    def click10(_):
        for i in range(10):
            x_setter(lambda y: y + 1)

    with View(style={"align": "top"}) as root:
        root(Button(title="State " + str(x) + " + 1", on_click=handle_click))
        root(Button(title="State " + str(x) + " + 10", on_click=click10))
        root(Button(title="Exit", on_click=lambda ev: asyncio.get_event_loop().call_soon(my_app.stop)))
        for i in range(x):
            root(Label(text=str(i)))
        return root


if __name__ == "__main__":
    my_app = App(UseState1())
    my_app.start()
