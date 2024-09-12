import os
import typing as tp
from pathlib import Path

from edifice import App, HBoxView, Image, VBoxView, Window, component
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import Qt
else:
    from PySide6.QtCore import Qt

imgpath = str(Path(__file__).parent.parent / "docs/source/image/textinput_button.png")


@component
def MyComponent(self):
    with VBoxView():
        with HBoxView():
            Image(src=imgpath)
            Image(
                src=imgpath,
                style={"padding": "50px", "border": "10px solid black"},
            )
        with HBoxView():
            Image(src=imgpath, style={"width": "200px", "height": "200px"})
            Image(
                src=imgpath,
                aspect_ratio_mode=Qt.AspectRatioMode.IgnoreAspectRatio,
                style={"width": "200px", "height": "200px"},
            )
        with HBoxView():
            Image(
                src=imgpath,
                aspect_ratio_mode=Qt.AspectRatioMode.KeepAspectRatio,
                style={"width": "200px", "height": "200px"},
            )
            Image(
                src=imgpath,
                aspect_ratio_mode=Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                style={"width": "200px", "height": "200px"},
            )


@component
def Main(self):
    with Window():
        MyComponent()


if __name__ == "__main__":
    App(Main()).start()
