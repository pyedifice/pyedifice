#
# python examples/use_state1.py
#

import asyncio

from edifice import App, Button, Label, VBoxView, Window, component, use_state, use_stop


@component
def UseState1(self):
    show, set_show = use_state(False)

    with Window():
        if show:
            with VBoxView():
                Label(text="Hide", on_click=lambda _ev: set_show(False))
                TestComp()
        else:
            with VBoxView():
                Label(text="Show", on_click=lambda _ev: set_show(True))


@component
def TestComp(self):
    print("TestComp instance " + str(id(self)))
    x, x_setter = use_state(0)
    stop = use_stop()

    async def handle_click(_):
        x_setter(x + 1)

    def click10(_):
        for _i in range(10):
            x_setter(lambda y: y + 1)

    with VBoxView(style={"align": "top"}):
        Button(title="State " + str(x) + " + 1", on_click=handle_click)
        Button(title="State " + str(x) + " + 10", on_click=click10)
        Button(title="Exit", on_click=lambda _ev: stop())
        for i in range(x):
            Label(text=str(i))


if __name__ == "__main__":
    App(UseState1()).start()
