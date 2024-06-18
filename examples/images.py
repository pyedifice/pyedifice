import typing as tp
from edifice import App, Window, View, component, Image
import os

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import Qt
else:
    from PySide6.QtCore import Qt

imgpath = os.path.join(os.path.dirname(__file__), "example_calculator.png")

imgstyle = {"width": "200px", "height": "200px"}


@component
def MyComponent(self):
    with View(layout="column").render():
        with View(layout="row").render():
            Image(src=imgpath, style=imgstyle).render()
            Image(src=imgpath, aspect_ratio_mode=Qt.AspectRatioMode.IgnoreAspectRatio, style=imgstyle).render()
        with View(layout="row").render():
            Image(src=imgpath, aspect_ratio_mode=Qt.AspectRatioMode.KeepAspectRatio, style=imgstyle).render()
            Image(src=imgpath, aspect_ratio_mode=Qt.AspectRatioMode.KeepAspectRatioByExpanding, style=imgstyle).render()


@component
def Main(self):
    with Window().render():
        MyComponent().render()


if __name__ == "__main__":
    App(Main()).start()
