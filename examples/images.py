import typing as tp
from edifice import App, Window, View, component, Image

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import Qt
else:
    from PySide6.QtCore import Qt

imgpath = os.path.join(os.path.dirname(__file__), "example_calculator.png")

imgstyle = {"width": "200px", "height": "200px"}


@component
def MyComponent(self):
    with View(layout="column"):
        with View(layout="row"):
            Image(src=imgpath, style=imgstyle)
            Image(src=imgpath, aspect_ratio_mode=Qt.AspectRatioMode.IgnoreAspectRatio, style=imgstyle)
        with View(layout="row"):
            Image(src=imgpath, aspect_ratio_mode=Qt.AspectRatioMode.KeepAspectRatio, style=imgstyle)
            Image(src=imgpath, aspect_ratio_mode=Qt.AspectRatioMode.KeepAspectRatioByExpanding, style=imgstyle)


@component
def Main(self):
    with Window():
        MyComponent()


if __name__ == "__main__":
    App(Main()).start()
