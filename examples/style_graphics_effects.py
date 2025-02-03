import typing as tp

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import QPointF
    from PyQt6.QtGui import QColor
    from PyQt6.QtWidgets import QApplication
else:
    from PySide6.QtCore import QPointF
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import QApplication


@ed.component
def MyComponent(self):
    with ed.VBoxView(style={"align": "center"}):
        with ed.HBoxView(style={"opacity": 0.2, "padding": 10}):
            ed.Label(
                text="Opacity",
                style={"font-size": 48},
            )
        with ed.HBoxView(style={"blur": 8, "padding": 10}):
            ed.Label(
                text="Blur",
                style={"font-size": 48},
            )
        with ed.HBoxView(style={"padding": 10}):
            ed.Label(
                text="Drop Shadow",
                style={
                    "font-size": 48,
                    "drop-shadow": (8, QColor(0, 0, 0, 255), QPointF(5.0, 5.0)),
                },
            )
        with ed.HBoxView(
            style={"colorize": (QColor(255, 0, 0, 255), 10.0), "padding": 10},
        ):
            ed.Label(
                text="Colorize",
                style={
                    "font-size": 48,
                },
            )


@ed.component
def Main(self):
    def initializer():
        palette = ed.palette_edifice_light() if ed.theme_is_light() else ed.palette_edifice_dark()
        tp.cast(QApplication, QApplication.instance()).setPalette(palette)
        return palette

    ed.use_memo(initializer)
    with ed.Window(_size_open=(800, 600)):
        MyComponent()


if __name__ == "__main__":
    ed.App(Main()).start()
