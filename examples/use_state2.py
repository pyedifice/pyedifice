#
# python examples/use_state2.py
#
# Test the use_state re-rendering and prop re-rendering logic.

import typing as tp

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QPalette
    from PyQt6.QtWidgets import QApplication, QSizePolicy
else:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QPalette
    from PySide6.QtWidgets import QApplication, QSizePolicy


@ed.component
def Main(self):
    x1, x1_setter = ed.use_state(0)
    x2, x2_setter = ed.use_state(0)
    x3, x3_setter = ed.use_state(0)

    print("render Main")  # noqa: T201
    with ed.Window():
        with ed.HBoxView():
            with ed.VBoxView(
                size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
            ):
                ed.Label(text="1")
                ed.Button(title=f"Prop {x1} + 1", on_click=lambda _: x1_setter(lambda old: old + 1))
                TestComp(1, x1)
            with ed.VBoxView(
                size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
            ):
                ed.Label(text="2")
                ed.Button(title=f"Prop {x2} + 1", on_click=lambda _: x2_setter(lambda old: old + 1))
                TestComp(2, x2)
            with ed.VBoxView(
                size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
            ):
                ed.Label(text="3")
                ed.Button(title=f"Prop {x3} + 1", on_click=lambda _: x3_setter(lambda old: old + 1))
                TestComp(3, x3)

@ed.component
def TestComp(self, prop1: int, prop2: int):
    x, x_setter = ed.use_state(0)

    print(f"render TestComp {prop1} prop {prop2} state {x}")  # noqa: T201

    with ed.VBoxView(
        size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
    ):
        ed.Label(text=f"{x}")
        ed.Button(title="State " + str(x) + " + 1", on_click=lambda _: x_setter(lambda y: y + 1))
        ed.Button(title="No-op", on_click=lambda _: x_setter(lambda y: y))


if __name__ == "__main__":
    ed.App(Main()).start()
