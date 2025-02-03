#
#     python -m edifice examples/text_style.py Main
#

from __future__ import annotations

import typing as tp

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtWidgets
    from PyQt6.QtCore import QByteArray, Qt
    from PyQt6.QtWidgets import QSizePolicy
else:
    from PySide6 import QtWidgets
    from PySide6.QtCore import QByteArray, Qt
    from PySide6.QtWidgets import QSizePolicy


ff_svg_text = QByteArray.fromStdString('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2024 Fonticons, Inc.--><path d="M18.4 445c11.2 5.3 24.5 3.6 34.1-4.4L224 297.7 224 416c0 12.4 7.2 23.7 18.4 29s24.5 3.6 34.1-4.4L448 297.7 448 416c0 17.7 14.3 32 32 32s32-14.3 32-32l0-320c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 118.3L276.5 71.4c-9.5-7.9-22.8-9.7-34.1-4.4S224 83.6 224 96l0 118.3L52.5 71.4c-9.5-7.9-22.8-9.7-34.1-4.4S0 83.6 0 96L0 416c0 12.4 7.2 23.7 18.4 29z"/></svg>')
ff_svg_text_white = QByteArray.fromStdString('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2024 Fonticons, Inc.--><path style="fill:#ffffff;" d="M18.4 445c11.2 5.3 24.5 3.6 34.1-4.4L224 297.7 224 416c0 12.4 7.2 23.7 18.4 29s24.5 3.6 34.1-4.4L448 297.7 448 416c0 17.7 14.3 32 32 32s32-14.3 32-32l0-320c0-17.7-14.3-32-32-32s-32 14.3-32 32l0 118.3L276.5 71.4c-9.5-7.9-22.8-9.7-34.1-4.4S224 83.6 224 96l0 118.3L52.5 71.4c-9.5-7.9-22.8-9.7-34.1-4.4S0 83.6 0 96L0 416c0 12.4 7.2 23.7 18.4 29z"/></svg>')

@ed.component
def TextStyle(self):
    with ed.VBoxView(style={"align": Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop}):

        ed.Label(
            text="⏭ Fast Forward",
            style={
                "font-size": 20,
            },
        )

        ed.Label(
            text="<span style='font-size:25pt;'>⏭</span> <span>Fast Forward</span>",
            style={
                "font-size": 20,
                "align": Qt.AlignmentFlag.AlignBaseline, # has no effect
            },
        )

        with ed.HBoxView():
            ed.Label(
                text="⏭",
                style={
                    "font-size": 32,
                },
              )
            ed.Label(
                text=" Fast Forward",
                style={
                    "font-size": 20,
                },
            )

        with ed.HBoxView():
            ed.Label(
                text="⏭",
                style={
                    "font-size": 32,
                    "font-family": "Segoe UI Emoji",
                },
              )
            ed.Label(
                text=" Fast Forward",
                style={
                    "font-size": 20,
                },
            )

        with ed.HBoxView():
            ed.Label(
                text="⏭",
                style={
                    "font-size": 32,
                    "font-family": "Noto Emoji",
                },
              )
            ed.Label(
                text=" Fast Forward",
                style={
                    "font-size": 20,
                },
            )

        with ed.HBoxView():
            ed.ImageSvg(
                src=ff_svg_text,
                style={
                    "width": 30,
                    "height": 30,
                },
            )
            ed.Label(
                text=" Fast Forward",
                style={
                    "font-size": 20,
                },
            )

        with ed.HBoxView():
            ed.ImageSvg(
                src=ff_svg_text_white,
                style={
                    "width": 30,
                    "height": 30,
                },
            )
            ed.Label(
                text=" Fast Forward",
                style={
                    "font-size": 20,
                },
            )


@ed.component
def Main(self):
    def initializer():
        palette = ed.palette_edifice_light() if ed.theme_is_light() else ed.palette_edifice_dark()
        tp.cast(QtWidgets.QApplication, QtWidgets.QApplication.instance()).setPalette(palette)
        return palette

    ed.use_memo(initializer)

    with ed.Window(title="Text Style", _size_open=(800, 400)):
        TextStyle()

if __name__ == "__main__":
    ed.App(Main()).start()
