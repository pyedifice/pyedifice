import asyncio
import typing as tp

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtWidgets import QSizePolicy
else:
    from PySide6.QtWidgets import QSizePolicy


@ed.component
def FadeIn(self, children: tuple[ed.Element, ...] = ()):
    """
    Component that fades in its children.
    Adds an extra 10px of padding-bottom to make room for the fade-in effect.
    """
    tick, tick_set = ed.use_state(20)
    # tick runs from 20 to 0 for 420ms

    async def fade_in():
        for t in range(19, 0, -1):
            await asyncio.sleep(0.02)
            tick_set(t)

    ed.use_async(fade_in)

    with ed.VBoxView(
        style={"padding-top": (tick // 2), "padding-bottom": 10 - (tick // 2)} | {"opacity": 1.0 - (float(tick) / 20.0)}
        if tick > 0
        else {},
    ):
        with ed.VBoxView(style={"blur": tick / 3} if tick > 0 else {}):
            for child in children:
                ed.child_place(child)


@ed.component
def MyComponent(self):
    show, show_set = ed.use_state(True)
    with ed.VBoxView(style={"align": "center"}):
        ed.CheckBox(checked = show, on_change = show_set, text = "Show")
        with ed.HBoxView(style={"width": 500, "height": 200}):
            if show:
                with FadeIn():
                    ed.Label(
                        text="Hello, World!",
                        style={"font-size": 48},
                    )


@ed.component
def Main(self):
    with ed.Window(_size_open=(800, 600)):
        MyComponent()


if __name__ == "__main__":
    ed.App(Main()).start()
