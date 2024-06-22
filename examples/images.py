import typing as tp
from edifice import App, Window, View, component, Image
import os
from edifice.engine import TreeBuilder

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import Qt
else:
    from PySide6.QtCore import Qt

imgpath = os.path.join(os.path.dirname(__file__), "example_calculator.png")

imgstyle = {"width": "200px", "height": "200px"}


@component
def MyComponent(self):
    put = TreeBuilder()
    with put(View(layout="column")) as root:
        with put(View(layout="row")):
            put(Image(src=imgpath, style=imgstyle))
            put(Image(src=imgpath, aspect_ratio_mode=Qt.AspectRatioMode.IgnoreAspectRatio, style=imgstyle))
        with put(View(layout="row")):
            put(Image(src=imgpath, aspect_ratio_mode=Qt.AspectRatioMode.KeepAspectRatio, style=imgstyle))
            put(Image(src=imgpath, aspect_ratio_mode=Qt.AspectRatioMode.KeepAspectRatioByExpanding, style=imgstyle))
        return root


@component
def Main(self):
    return Window()(MyComponent())


if __name__ == "__main__":
    App(Main()).start()
