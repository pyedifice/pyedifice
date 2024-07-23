#
# python examples/use_effect1.py
#

import asyncio as asyncio
from edifice import App, Window, View, Label, Button, component
from edifice.engine import TreeBuilder
from edifice.hooks import use_state, use_effect


@component
def MainComp(self):
    show, set_show = use_state(False)
    put = TreeBuilder()
    with put(Window(on_close=lambda ev: print("Window will close"))) as root:
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

    def setup():
        print("effect setup")

        def cleanup():
            print("effect cleanup")
            pass

        return cleanup

    use_effect(setup, x)

    def setup_always():
        print("effect setup always")

        def cleanup():
            print("effect cleanup always")
            pass

        return cleanup

    use_effect(setup_always, None)

    with View(style={"align": "top"}) as root:
        root(Label(text="Label text"))
        root(Button(title="State " + str(x), on_click=lambda ev: x_setter(x + 1)))
        root(Button(title="State Unchanged", on_click=lambda ev: x_setter(lambda y: y)))
        return root


if __name__ == "__main__":
    my_app = App(MainComp())
    my_app.start()
