#
# python examples/use_state1.py
#

import asyncio as asyncio
from edifice import App, Window, View, Label, Button, component, use_state


@component
def UseState1(self):
    show, set_show = use_state(False)

    with Window().render():
        if show:
            with View().render():
                Button(title="Hide", on_click=lambda ev: set_show(False)).render()
                TestComp().render()
        else:
            with View().render():
                Button(title="Show", on_click=lambda ev: set_show(True)).render()


@component
def TestComp(self):
    print("TestComp instance " + str(id(self)))
    x, x_setter = use_state(0)

    async def handle_click(_):
        x_setter(x + 1)

    def click10(_):
        for i in range(10):
            x_setter(lambda y: y + 1)

    with View(style={"align": "top"}).render():
        Button(title="State " + str(x) + " + 1", on_click=handle_click).render()
        Button(title="State " + str(x) + " + 10", on_click=click10).render()
        Button(title="Exit", on_click=lambda ev: asyncio.get_event_loop().call_soon(my_app.stop)).render()
        for i in range(x):
            Label(text=str(i)).render()


if __name__ == "__main__":
    my_app = App(UseState1())
    my_app.start()
