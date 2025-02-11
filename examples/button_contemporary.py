# python examples/todomvc.py
#

from __future__ import annotations

import asyncio
import typing as tp
from collections import OrderedDict
from dataclasses import dataclass
from typing import cast

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtCore, QtGui, QtWidgets
    from PyQt6.QtGui import QKeyEvent, QMouseEvent
    from PyQt6.QtWidgets import QSizePolicy
else:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtGui import QKeyEvent, QMouseEvent
    from PySide6.QtWidgets import QSizePolicy

import edifice as ed


@ed.component
def ButtonContemporary(
    self,
    style: ed.PropsDict | None = None,
    on_trigger: tp.Callable[[QKeyEvent], None] | tp.Callable[[QMouseEvent], None] | None = None,
    children: tuple[ed.Element, ...] = (),
    **kwargs,
):
    # palette = tp.cast(QtWidgets.QApplication, QtWidgets.QApplication.instance()).palette()

    step, step_set = ed.use_state(0)
    # step = 0: normal
    # step = 5: hover
    # step = 10: mouse down

    async def step_to(target: int):
        print(f"step_to({target})")
        try:
            while step != target:
                await asyncio.sleep(0.05)
                step_set(lambda step_old: step_old + 1 if step_old < target else step_old - 1)
        except asyncio.CancelledError:
            step_set(target)
            raise

    step_to_call, step_to_call_cancel = ed.use_async_call(step_to)

    hover, hover_set = ed.use_state(False)
    mouse_down, mouse_down_set = ed.use_state(False)
    is_light = ed.theme_is_light()

    def on_mouse_enter(_ev: QtGui.QMouseEvent):
        print("on_mouse_enter")
        hover_set(True)
        step_to_call(5)

    def on_mouse_leave(_ev: QtGui.QMouseEvent):
        print("on_mouse_leave")
        hover_set(False)
        mouse_down_set(False)
        step_to_call(0)

    def on_mouse_down(_ev: QtGui.QMouseEvent):
        print("on_mouse_down")
        mouse_down_set(True)
        # step_to_call(10)
        step_to_call_cancel()
        step_set(10)

    def on_mouse_up(_ev: QtGui.QMouseEvent):
        print("on_mouse_up")
        mouse_down_set(False)
        step_to_call(5)

    if is_light:
        backcolor = QtGui.QColor(0, 0, 0, step * 2)
    else:
        backcolor = QtGui.QColor(255, 255, 255, step * 2)
    # match is_light, hover, mouse_down:
    #     case False, False, False:
    #         backcolor = QtGui.QColor(255, 255, 255, 0)
    #     case False, True, False:
    #         backcolor = QtGui.QColor(255, 255, 255, 10)
    #     case False, True, True:
    #         backcolor = QtGui.QColor(255, 255, 255, 20)
    #     case False, False, True:
    #         raise ValueError("unreachable")
    #     case True, False, False:
    #         backcolor = QtGui.QColor(0, 0, 0, 0)
    #     case True, True, False:
    #         backcolor = QtGui.QColor(0, 0, 0, 10)
    #     case True, True, True:
    #         backcolor = QtGui.QColor(0, 0, 0, 20)
    #     case True, False, True:
    #         raise ValueError("unreachable")

    with ed.ButtonView(
        # style={
        #     "border-width": 0,
        #     "border-radius": 6,
        #     "padding": 6,
        #     "background-color": backcolor,
        # } | (style or {}),
        # on_mouse_enter=on_mouse_enter,
        # on_mouse_leave=on_mouse_leave,
        # on_mouse_down=on_mouse_down,
        # on_mouse_up=on_mouse_up,
        # on_trigger=on_trigger,
        # size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
        **(
            {
                # Props which can be overridden
                "on_trigger": on_trigger,
                "size_policy": QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
            }
            | kwargs
            | {
                # Style, which can be overridden
                "style": {
                    "border-width": 0,
                    "border-radius": 6,
                    "padding": 6,
                    "background-color": backcolor,
                }
                | (style or {}),
                # Props which cannot be overridden
                "on_mouse_enter": on_mouse_enter,
                "on_mouse_leave": on_mouse_leave,
                "on_mouse_down": on_mouse_down,
                "on_mouse_up": on_mouse_up,
            }
        ),
    ):
        for child in children:
            ed.child_place(child)


@ed.component
def Application(self):
    with ed.Window(title="Button Contemporary Demo"):
        with ed.VBoxView():
            with ed.HBoxView():
                with ed.VBoxView(style={"padding": 20}):
                    with ButtonContemporary():
                        ed.Label(text="Muted")
                with ed.VBoxView(style={"padding": 20}):
                    with ButtonContemporary():
                        ed.Label(text="Post")
                with ed.VBoxView(style={"padding": 20}):
                    with ButtonContemporary():
                        ed.Label(text="Horn")


@ed.component
def Main(self):
    def initializer():
        qapp = tp.cast(QtWidgets.QApplication, QtWidgets.QApplication.instance())
        qapp.setApplicationName("Button Contemporary Demo")
        if ed.theme_is_light():
            qapp.setPalette(ed.palette_edifice_light())
        else:
            qapp.setPalette(ed.palette_edifice_dark())

    _, _ = ed.use_state(initializer)

    with ed.Window(title="todos", _size_open=(520, 200)):
        Application()


if __name__ == "__main__":
    ed.App(Main()).start()
