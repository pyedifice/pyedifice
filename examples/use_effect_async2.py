#
# python examples/use_effect_async1.py
#

import asyncio as asyncio
from edifice import App, Window, View, component, TextInput
from edifice.hooks import use_state, use_async


@component
def MainComp(self):
    x, x_set = use_state("")

    async def effect():
        await asyncio.sleep(0.5)
        print(x)

    use_async(effect, x)
    with Window().render():
        with View().render():
            TextInput(text=x, on_change=x_set)


if __name__ == "__main__":
    my_app = App(MainComp())
    my_app.start()
