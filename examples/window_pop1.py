#
# python examples/window_pop1.py
#

import asyncio

import edifice as ed


def use_clocktick() -> int:
    tick, tick_set = ed.use_state(0)

    async def increment():
        await asyncio.sleep(1)
        tick_set(tick + 1)

    ed.use_async(increment, tick)

    return tick

@ed.component
def Clock(self):
    tick = use_clocktick()
    ed.Label(text=f"Tick: {tick}")

@ed.component
def Main(self):

    popshow, popshow_set = ed.use_state(False)

    popshow2, popshow2_set = ed.use_state(False)

    with ed.Window(
        title="Main Window",
        style={
            "background-color": "black",
            "padding": 20,
        },
    ):
        ed.CheckBox(
            checked=popshow,
            text="Show Pop-up Window",
            on_change=popshow_set,
        )
        if popshow:
            with ed.WindowPopView(
                title="Pop-up Window",
                on_close=lambda _: popshow_set(False),
                style={
                    "background-color": "green",
                    "padding": 20,
                },
            ):
                ed.Label(
                    text="This is a Pop-up Window",
                    word_wrap=False,
                )
                Clock()
                ed.CheckBox(
                    checked=popshow2,
                    text="Show Pop-up Window 2",
                    on_change=popshow2_set,
                )
                if popshow2:
                    with ed.WindowPopView(
                        title="Pop-up Window 2",
                        on_close=lambda _: popshow2_set(False),
                        style={
                            "background-color": "blue",
                            "padding": 20,
                        },
                    ):
                        ed.Label(
                            text="This is a Pop-up Window 2",
                            word_wrap=False,
                        )
                        Clock()
                    with ed.WindowPopView(
                        title="Pop-up Window 2 Second",
                        on_close=lambda _: popshow2_set(False),
                        style={
                            "background-color": "blue",
                            "padding": 20,
                        },
                    ):
                        ed.Label(
                            text="This is the second Pop-up Window 2",
                            word_wrap=False,
                        )
                        Clock()

if __name__ == "__main__":
    ed.App(Main()).start()
