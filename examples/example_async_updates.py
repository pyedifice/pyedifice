#
# python examples/use_effect_async1.py
#

import asyncio as asyncio
from typing import cast
from edifice import App, Window, View, Label, Button, ButtonView, component
from edifice.hooks import use_state, use_async


@component
def MainComp(self):
    show, set_show = use_state(False)
    with Window():
        if show:
            with View(style={"align": "top"}):
                Button(title="Hide", on_click=lambda ev: set_show(False))
                TestComp()
        else:
            with View(style={"align": "top"}):
                Button(title="Show", on_click=lambda ev: set_show(True))


@component
def TestComp(self):
    print("TestComp instance " + str(id(self)))

    x, x_setter = use_state(cast(list[str], []))

    async def fetch():
        print(f"async {x}")
        loop = asyncio.get_running_loop()
        try:
            await asyncio.sleep(0.1)
            loop.call_soon_threadsafe(x_setter, lambda old: [str(len(x))])
        except Exception as ex:
            print(f"async {x} cancelled")
            raise ex

    print(f"use_async(fetch, {x})")
    use_async(fetch, x)

    with View(style={"align": "top"}):
        with ButtonView(on_trigger=lambda _: x_setter(lambda old: [f"manual {len(old)}"] + old)):
            Label("Prepend text")
        with View(layout="none", style={"width": 800, "height": 900}):
            for i, text in enumerate(x):
                with ButtonView(style={"left": i * 50, "top": 0}):
                    Label(text)


if __name__ == "__main__":
    my_app = App(MainComp())
    my_app.start()
