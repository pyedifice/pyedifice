#
# python examples/window_pop1.py
#

import asyncio
import typing as tp

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtGui
else:
    from PySide6 import QtGui


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

    full_screen, full_screen_set = ed.use_state(True)

    def handle_key_down(event: QtGui.QKeyEvent):
        if event.key() == QtGui.Qt.Key.Key_F11:
            full_screen_set(not full_screen)

    with ed.Window(
        title="Main Window",
        style={
            "background-color": "black",
            "padding": 20,
        },
        _size_open=(400, 200),
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
                _size_open=(400, 200),
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
                        _size_open=(400, 200),
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
                        on_key_down=handle_key_down,
                        _size_open=(400, 200),
                        # _size_open="Maximized",
                        full_screen=full_screen,
                    ):
                        ed.Label(
                            text="This is the second Pop-up Window 2",
                            word_wrap=False,
                        )
                        Clock()


if __name__ == "__main__":
    ed.App(Main()).start()
