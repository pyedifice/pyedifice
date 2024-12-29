from __future__ import annotations

import typing as tp

from .qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtWidgets
    from PyQt6.QtGui import QColor, QPalette
    from PyQt6.QtWidgets import QApplication
else:
    from PySide6 import QtWidgets
    from PySide6.QtGui import QColor, QPalette
    from PySide6.QtWidgets import QApplication


def palette_dump(palette: QPalette, palette_compare: QPalette | None = None) -> None:
    """
    Dump the palette to the console.

    Args:
        palette: Dump the palette to the console.
        palette_compare: Compare the palette with another palette if palette_compare is not None.
    """
    colorroles = [
        QPalette.ColorRole.Window,
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Base,
        QPalette.ColorRole.AlternateBase,
        QPalette.ColorRole.ToolTipBase,
        QPalette.ColorRole.ToolTipText,
        QPalette.ColorRole.PlaceholderText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.Button,
        QPalette.ColorRole.ButtonText,
        QPalette.ColorRole.BrightText,

        QPalette.ColorRole.Light,
        QPalette.ColorRole.Midlight,
        QPalette.ColorRole.Dark,
        QPalette.ColorRole.Mid,
        QPalette.ColorRole.Shadow,

        QPalette.ColorRole.Highlight,
        QPalette.ColorRole.HighlightedText,
        QPalette.ColorRole.Link,
        QPalette.ColorRole.LinkVisited,
        QPalette.ColorRole.Accent,
    ]
    colorgroups = [
        QPalette.ColorGroup.Active,
        QPalette.ColorGroup.Disabled,
        QPalette.ColorGroup.Inactive,
    ]

    for colorrole in colorroles:
        for colorgroup in colorgroups:
            c = palette.color(colorgroup, colorrole)
            print("palette.setColor(", end="")
            print(f"QPalette.{colorgroup}, QPalette.{colorrole}, ", end="")
            print(f"QColor.fromRgb{c.getRgb()}", end="")
            print(")", end="")
            if palette_compare is not None:
                c_compare = palette_compare.color(colorgroup, colorrole)
                if c != c_compare:
                    print(f" # CHANGED from {c_compare.getRgb()}")
                else:
                    print("")
            else:
                print("")


def theme_is_light() -> bool:
    """
    Detect the operating environment theme.

    True if light theme, false if dark theme.

    Example::

        def initializer():
            palette = palette_edifice_light() if theme_is_light() else palette_edifice_dark()
            cast(QApplication, QApplication.instance()).setPalette(palette)
            return palette

        palette, _ = ed.use_state(initializer)

        with Window():

    """
    return QApplication.palette().windowText().color().lightness() < QApplication.palette().window().color().lightness()
    #
    # The styleHints().colorScheme() doesn't work with environment
    # variable GTK_THEME=Adwaita:light
    #
    # > colorscheme = QtGui.QGuiApplication.styleHints().colorScheme()
    # > match colorscheme:
    # >     case QtCore.Qt.ColorScheme.Dark:
    # >         return False
    # >     case QtCore.Qt.ColorScheme.Light:
    # >         return True
    # >     case QtCore.Qt.ColorScheme.Unknown:
    # >         palette = QApplication.palette()
    # >         return palette.windowText().color().lightness() < palette.window().color().lightness()
    # >     case _:
    # >         return True


def palette_edifice_dark() -> QPalette:
    """
    Edifice dark theme palette. This is the Qt Linux default dark theme palette, with some adjustments.
    """
    # https://doc.qt.io/qtforpython-6/PySide6/QtGui/QPalette.html#PySide6.QtGui.QPalette.ColorGroup
    # https://doc.qt.io/qtforpython-6/PySide6/QtGui/QPalette.html#PySide6.QtGui.QPalette.ColorRole

    palette = QPalette()
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Window, QColor.fromRgb(40, 40, 40, 255)) # CHANGED from (50, 50, 50, 255)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window, QColor.fromRgb(40, 40, 40, 255)) # CHANGED from (50, 50, 50, 255)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, QColor.fromRgb(40, 40, 40, 255)) # CHANGED from (50, 50, 50, 255)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, QColor.fromRgb(200, 200, 200, 255)) # CHANGED from (255, 255, 255, 255)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor.fromRgb(127, 127, 127, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, QColor.fromRgb(200, 200, 200, 255)) # CHANGED from (145, 145, 144, 255)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Base, QColor.fromRgb(50, 50, 50, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor.fromRgb(50, 50, 50, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Base, QColor.fromRgb(50, 50, 50, 255))
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.AlternateBase, QColor.fromRgb(47, 47, 47, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.AlternateBase, QColor.fromRgb(47, 47, 47, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.AlternateBase, QColor.fromRgb(47, 47, 47, 255))
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ToolTipBase, QColor.fromRgb(37, 37, 37, 255)) # CHANGED from (255, 255, 220, 255)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ToolTipBase, QColor.fromRgb(37, 37, 37, 255)) # CHANGED from (255, 255, 220, 255)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ToolTipBase, QColor.fromRgb(37, 37, 37, 255)) # CHANGED from (255, 255, 220, 255)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ToolTipText, QColor.fromRgb(255, 255, 255, 255)) # CHANGED from (0, 0, 0, 255)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ToolTipText, QColor.fromRgb(255, 255, 255, 255)) # CHANGED from (0, 0, 0, 255)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ToolTipText, QColor.fromRgb(255, 255, 255, 255)) # CHANGED from (0, 0, 0, 255)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.PlaceholderText, QColor.fromRgb(100, 100, 100, 255)) # CHANGED from (155, 155, 155, 255)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.PlaceholderText, QColor.fromRgb(70, 70, 70, 255)) # CHANGED FROM (155, 155, 155, 255)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.PlaceholderText, QColor.fromRgb(100, 100, 100, 255)) # CHANGED from (155, 155, 155, 255)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, QColor.fromRgb(200, 200, 200, 255)) # CHANGED from (255, 255, 255, 255)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor.fromRgb(127, 127, 127, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, QColor.fromRgb(200, 200, 200, 255)) # CHANGED from (255, 255, 255, 255)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Button, QColor.fromRgb(37, 37, 37, 255)) # CHANGED from (50, 50, 50, 255)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, QColor.fromRgb(30, 30, 30, 255)) # CHANGED from (50, 50, 50, 255)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Button, QColor.fromRgb(37, 37, 37, 255)) # CHANGED from (50, 50, 50, 255)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText, QColor.fromRgb(200, 200, 200, 255)) # CHANGED from (255, 255, 255, 255)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor.fromRgb(127, 127, 127, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ButtonText, QColor.fromRgb(200, 200, 200, 255)) # CHANGED from (255, 255, 255, 255)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.BrightText, QColor.fromRgb(255, 255, 255, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.BrightText, QColor.fromRgb(255, 255, 255, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.BrightText, QColor.fromRgb(255, 255, 255, 255))

    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Light, QColor.fromRgb(50, 50, 50, 255)) # (62, 62, 62, 255))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Midlight, QColor.fromRgb(43, 43, 43, 255)) # (56, 56, 56, 255))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Dark, QColor.fromRgb(25, 25, 25, 255)) # (44, 44, 44, 255))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Mid, QColor.fromRgb(32, 32, 32, 255)) # (56, 56, 56, 255))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Shadow, QColor.fromRgb(10, 10, 10, 255)) # (2, 2, 2, 255))

    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight, QColor.fromRgb(21, 73, 108, 255)) # CHANGED from (21, 83, 158, 255)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor.fromRgb(21, 73, 108, 255)) # CHANGED from (21, 83, 158, 255)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Highlight, QColor.fromRgb(21, 73, 108, 255)) # CHANGED from (21, 83, 158, 255)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText, QColor.fromRgb(255, 255, 255, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor.fromRgb(255, 255, 255, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.HighlightedText, QColor.fromRgb(255, 255, 255, 255))
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Link, QColor.fromRgb(80, 180, 255, 255)) # CHANGED from (48, 140, 198, 255)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Link, QColor.fromRgb(48, 140, 198, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Link, QColor.fromRgb(80, 180, 255, 255)) # CHANGED from (48, 140, 198, 255)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.LinkVisited, QColor.fromRgb(80, 180, 255, 255)) # CHANGED from (255, 0, 255, 255)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.LinkVisited, QColor.fromRgb(48, 140, 198, 255)) # CHANGED from (255, 0, 255, 255)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.LinkVisited, QColor.fromRgb(80, 180, 255, 255)) # CHANGED from (255, 0, 255, 255)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Accent, QColor.fromRgb(48, 140, 198, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Accent, QColor.fromRgb(145, 145, 145, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Accent, QColor.fromRgb(48, 140, 198, 255))

    return palette


def palette_edifice_light() -> QPalette:
    """
    Edifice light theme palette. This is the Qt Linux default light theme palette, with some adjustments.
    """
    palette = QPalette()
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Window, QColor.fromRgb(230, 230, 230, 255)) # CHANGED from (250, 249, 248, 255)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window, QColor.fromRgb(230, 230, 230, 255)) # CHANGED from (250, 249, 248, 255)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Window, QColor.fromRgb(230, 230, 230, 255)) # CHANGED from (250, 249, 248, 255)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText, QColor.fromRgb(60, 60, 60, 255)) # CHANGED from (0, 0, 0, 255)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor.fromRgb(127, 127, 127, 255))# CHANGED from (0, 0, 0, 255)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.WindowText, QColor.fromRgb(60, 60, 60, 255)) # CHANGED from (146, 149, 149, 255)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Base, QColor.fromRgb(242, 242, 242, 255)) # (250, 249, 248, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor.fromRgb(235, 235, 235, 255)) # (250, 249, 248, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Base, QColor.fromRgb(242, 242, 242, 255)) # (250, 249, 248, 255))
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.AlternateBase, QColor.fromRgb(234, 233, 232, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.AlternateBase, QColor.fromRgb(225, 225, 225, 255)) # (234, 233, 232, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.AlternateBase, QColor.fromRgb(234, 233, 232, 255))
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ToolTipBase, QColor.fromRgb(230, 230, 230, 255)) # (255, 255, 220, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ToolTipBase, QColor.fromRgb(230, 230, 230, 255)) # (255, 255, 220, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ToolTipBase, QColor.fromRgb(230, 230, 230, 255)) # (255, 255, 220, 255))
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ToolTipText, QColor.fromRgb(0, 0, 0, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ToolTipText, QColor.fromRgb(0, 0, 0, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ToolTipText, QColor.fromRgb(0, 0, 0, 255))
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.PlaceholderText, QColor.fromRgb(160, 160, 160, 255)) # (0, 0, 0, 0))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.PlaceholderText, QColor.fromRgb(200, 200, 200)) # (0, 0, 0, 0))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.PlaceholderText, QColor.fromRgb(160, 160, 160, 255)) # (0, 0, 0, 0))
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, QColor.fromRgb(40, 40, 40, 255)) # CHANGED from (0, 0, 0, 255)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor.fromRgb(100, 100, 100, 255))# (0, 0, 0, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, QColor.fromRgb(40, 40, 40, 255)) # (0, 0, 0, 255))
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Button, QColor.fromRgb(225, 225, 225, 255)) # CHANGED from (250, 249, 248, 255)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, QColor.fromRgb(215, 215, 215, 255)) # CHANGED from (250, 249, 248, 255)
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Button, QColor.fromRgb(225, 225, 225, 255)) # CHANGED from (250, 249, 248, 255)
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText, QColor.fromRgb(60, 60, 60, 255)) # (0, 0, 0, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor.fromRgb(127, 127, 127, 255)) # (0, 0, 0, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.ButtonText, QColor.fromRgb(60, 60, 60, 255)) # (0, 0, 0, 255))
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.BrightText, QColor.fromRgb(0, 0, 0, 255)) # (255, 255, 255, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.BrightText, QColor.fromRgb(0, 0, 0, 255)) # (255, 255, 255, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.BrightText, QColor.fromRgb(0, 0, 0, 255)) # (255, 255, 255, 255))

    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Light, QColor.fromRgb(242, 242, 242, 255)) #(255, 255, 255, 255))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Midlight, QColor.fromRgb(235, 235, 235, 255)) # (255, 255, 255, 255))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Dark, QColor.fromRgb(205, 205, 205, 255)) # (219, 218, 218, 255))
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Mid, QColor.fromRgb(218, 218, 218, 255)) # (255, 255, 255, 255))
    palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Shadow, QColor.fromRgb(100, 100, 100, 255)) # (12, 12, 12, 255))

    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight, QColor.fromRgb(120, 190, 255, 255)) # (53, 132, 228, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor.fromRgb(180, 220, 255, 255)) # (53, 132, 228, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Highlight, QColor.fromRgb(120, 190, 255, 255)) # (53, 132, 228, 255))
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText, QColor.fromRgb(0, 0, 0, 255)) # (255, 255, 255, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor.fromRgb(0, 0, 0, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.HighlightedText, QColor.fromRgb(0, 0, 0, 255)) # (255, 255, 255, 255))
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Link, QColor.fromRgb(0, 80, 120, 255)) # (48, 140, 198, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Link, QColor.fromRgb(0, 80, 120, 255)) # (48, 140, 198, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Link, QColor.fromRgb(0, 80, 120, 255)) # (48, 140, 198, 255))
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.LinkVisited, QColor.fromRgb(0, 80, 120, 255)) # (255, 0, 255, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.LinkVisited, QColor.fromRgb(0, 80, 120, 255)) # (255, 0, 255, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.LinkVisited, QColor.fromRgb(0, 80, 120, 255)) # (255, 0, 255, 255))
    palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Accent, QColor.fromRgb(48, 140, 198, 255))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Accent, QColor.fromRgb(145, 145, 145, 255))
    palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Accent, QColor.fromRgb(48, 140, 198, 255))
    return palette


def alert(message: str, choices: tp.Sequence[str] | None = None) -> int | None:
    """Displays a message in an alert box.

    If choices is specified, the alert box contain a list of buttons showing each of the choices,
    and this function will return the user's choice.

    Args:
        message: message to display
        choices: optional list of choice texts, which will be displayed as buttons.
    Returns:
        Index of chosen option.
    """
    msgbox = QtWidgets.QMessageBox()
    msgbox.setText(message)
    buttons = []
    if choices is not None:
        for choice in choices:
            buttons.append(msgbox.addButton(choice, QtWidgets.QMessageBox.ButtonRole.ActionRole))
    msgbox.exec()
    clicked_button = msgbox.clickedButton()
    for i, button in enumerate(buttons):
        if clicked_button == button:
            return i
    return None


def file_dialog(
    caption: str = "",
    directory: str = "",
    file_filter: tp.Sequence[str] | None = None,
) -> str | None:
    """Displays a file choice dialog.

    Args:
        caption: the file dialog's caption
        directory: starting directory for the file dialog
        file_filter:
            Sequence of allowed file extensions. For example::

                "*.cpp *.cc *.C *.c++"
                "C++ files (*.cpp *.cc *.C *.c++)"

            are both valid ways of specifying a file filter.
    Returns:
        Path of chosen file
    """
    dialog = QtWidgets.QFileDialog(None, caption, directory)
    dialog.setFileMode(QtWidgets.QFileDialog.FileMode.AnyFile)
    if file_filter is not None:
        dialog.setNameFilters(file_filter)
    if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
        return dialog.selectedFiles()[0]
    return None


def set_trace():
    """Set a tracepoint in the Python debugger that works with PyQt.

    PDB does not work well with PyQt applications. :code:`edifice.set_trace()` is
    equivalent to :code:`pdb.set_trace()`,
    but it can properly pause the PyQt event loop
    to enable use of the debugger
    (users of PySide need not worry about this)."""

    import pdb

    if QT_VERSION == "PyQt6":
        from PyQt6.QtCore import pyqtRemoveInputHook

        pyqtRemoveInputHook()
    pdb.set_trace()
    # # set up the debugger
    # debugger = pdb.Pdb()
    # debugger.reset()
    # # custom next to get outside of function scope
    # debugger.do_next(None) # run the next command
    # users_frame = sys._getframe().f_back # frame where the user invoked `pyqt_set_trace()`
    # debugger.interaction(users_frame, None)
    # pyqtRestoreInputHook()
