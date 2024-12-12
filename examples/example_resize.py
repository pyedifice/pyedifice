import typing as tp

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
      from PyQt6.QtGui import QResizeEvent
else:
      from PySide6.QtGui import QResizeEvent

def resize_scroll(event: QResizeEvent):
    pass

@ed.component
def MyComponent(self):
    with ed.VScrollView(
        on_resize=resize_scroll,
    ):
        with ed.HBoxView(
            style={"border": "1px solid red"},
        ):
            ed.Label(text="Label1")
            with ed.HBoxView(
                style={"border": "1px solid blue"},
            ):
                ed.Label(text="Label2")

@ed.component
def Main(self):
    with ed.Window(
        style={"padding": 30},
    ):
        MyComponent()


if __name__ == "__main__":
    ed.App(Main()).start()
