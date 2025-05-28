"""
Display a matrix of most of the available widgets with the Edifice palette.

Run with default theme.

    python examples/style_matrix.py

Run with light theme.

    GTK_THEME=Adwaita:light python examples/style_matrix.py

Run with dark theme.

    GTK_THEME=Adwaita:dark python examples/style_matrix.py

"""
from __future__ import annotations

import typing as tp

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtWidgets
    from PyQt6.QtCore import QByteArray
    from PyQt6.QtGui import QColor, QPalette
else:
    from PySide6 import QtWidgets
    from PySide6.QtCore import QByteArray
    from PySide6.QtGui import QColor, QPalette

def pen_to_square(color:QColor) -> QByteArray:
    # https://fontawesome.com/icons/pen-to-square?f=classic&s=regular
    return QByteArray.fromStdString(f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
    <!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.-->
    <path fill="{color.name(format=QColor.NameFormat.HexRgb)}" d="M441 58.9L453.1 71c9.4 9.4 9.4 24.6 0 33.9L424 134.1 377.9 88 407 58.9c9.4-9.4 24.6-9.4 33.9 0zM209.8 256.2L344 121.9 390.1 168 255.8 302.2c-2.9 2.9-6.5 5-10.4 6.1l-58.5 16.7 16.7-58.5c1.1-3.9 3.2-7.5 6.1-10.4zM373.1 25L175.8 222.2c-8.7 8.7-15 19.4-18.3 31.1l-28.6 100c-2.4 8.4-.1 17.4 6.1 23.6s15.2 8.5 23.6 6.1l100-28.6c11.8-3.4 22.5-9.7 31.1-18.3L487 138.9c28.1-28.1 28.1-73.7 0-101.8L474.9 25C446.8-3.1 401.2-3.1 373.1 25zM88 64C39.4 64 0 103.4 0 152L0 424c0 48.6 39.4 88 88 88l272 0c48.6 0 88-39.4 88-88l0-112c0-13.3-10.7-24-24-24s-24 10.7-24 24l0 112c0 22.1-17.9 40-40 40L88 464c-22.1 0-40-17.9-40-40l0-272c0-22.1 17.9-40 40-40l112 0c13.3 0 24-10.7 24-24s-10.7-24-24-24L88 64z"/>
    </svg>
    """)

@ed.component
def Main(self):
    def initializer():
        # Uncomment this line to see the Qt default palette.
        # return tp.cast(QtWidgets.QApplication, QtWidgets.QApplication.instance()).palette()
        palette = ed.palette_edifice_light() if ed.theme_is_light() else ed.palette_edifice_dark()
        tp.cast(QtWidgets.QApplication, QtWidgets.QApplication.instance()).setPalette(palette)
        return palette

    palette, _ = ed.use_state(initializer)

    with ed.Window(
        title="Style Matrix",
        menu=(
            ("Action 1", lambda: None),
            ("Action 2", lambda: None),
            ("Submenu", (("Action 3", lambda: None), ("Action 4", lambda: None))),
        ),
    ):
        with ed.TableGridView(style={"padding": 10}):
            with ed.TableGridRow():
                ed.Label("Label")
                with ed.VBoxView():
                    ed.Label(
                        text="""<h1>Enabled</h1>
                            <h2>Heading 2</h2>
                            <h3>Heading 3</h3>
                            <p>Enabled widgets.</p>""",
                        selectable=True,
                    )
                    ed.Label(
                        text="""<a href='https://pyedifice.github.io'>https://pyedifice.github.io</a>""",
                        link_open=True,
                    )
                with ed.VBoxView():
                    ed.Label(
                        text="""<h1>Disabled</h1>
                            <h2>Heading 2</h2>
                            <h3>Heading 3</h3>
                            <p>Disabled widgets.</p>""",
                        selectable=True,
                        enabled=False,
                    )
                    ed.Label(
                        text="""<a href='https://pyedifice.github.io'>https://pyedifice.github.io</a>""",
                        link_open=True,
                        enabled=False,
                    )
            with ed.TableGridRow():
                ed.Label("TextInput")
                ed.TextInput(
                    text="TextInput",
                    completer=(
                        QtWidgets.QCompleter.CompletionMode.UnfilteredPopupCompletion,
                        ("TextInput 1", "TextInput 2", "TextInput 3"),
                    ),
                    _focus_open=True,
                )
                ed.TextInput(
                    text="TextInput",
                    completer=(
                        QtWidgets.QCompleter.CompletionMode.UnfilteredPopupCompletion,
                        ("TextInput 1", "TextInput 2", "TextInput 3"),
                    ),
                    enabled=False,
                )
            with ed.TableGridRow():
                ed.Label("Placeholder")
                ed.TextInput(placeholder_text="Placeholder")
                ed.TextInput(placeholder_text="Placeholder", enabled=False)
            with ed.TableGridRow():
                ed.Label("TextInputMultiline")
                ed.TextInputMultiline("TextInputMultiline")
                ed.TextInputMultiline("TextInputMultiline", enabled=False)
            with ed.TableGridRow():
                ed.Label("Button")
                ed.Button("Button")
                ed.Button("Button", enabled=False)
            with ed.TableGridRow():
                ed.Label("CheckBox")
                with ed.HBoxView():
                    ed.CheckBox(checked=True, text="CheckBox")
                    ed.CheckBox(checked=False, text="CheckBox")
                with ed.HBoxView():
                    ed.CheckBox(checked=True, text="CheckBox", enabled=False)
                    ed.CheckBox(checked=False, text="CheckBox", enabled=False)
            with ed.TableGridRow():
                ed.Label("RadioButton")
                with ed.HBoxView():
                    ed.RadioButton(text="RadioButton", checked=True)
                    ed.RadioButton(text="RadioButton", checked=False)
                with ed.HBoxView():
                    ed.RadioButton(text="RadioButton", checked=True, enabled=False)
                    ed.RadioButton(text="RadioButton", checked=False, enabled=False)
            with ed.TableGridRow():
                ed.Label("Dropdown")
                ed.Dropdown(options=["Option 1", "Option 2", "Option 3"])
                ed.Dropdown(options=["Option 1", "Option 2", "Option 3"], enabled=False)
            with ed.TableGridRow():
                ed.Label("SpinInput")
                ed.SpinInput()
                ed.SpinInput(enabled=False)
            with ed.TableGridRow():
                ed.Label("ButtonView")
                with ed.ButtonView():
                    ed.ImageSvg(
                        src=pen_to_square(palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Text)),
                        style={"width": 20, "height": 20},
                    )
                    ed.Label("ButtonView")
                with ed.ButtonView(enabled=False):
                    ed.ImageSvg(
                        src=pen_to_square(palette.color(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text)),
                        style={"width": 20, "height": 20},
                        enabled=False,
                    )
                    ed.Label("ButtonView")
            with ed.TableGridRow():
                ed.Label("ProgressBar")
                with ed.HBoxView():
                    ed.ProgressBar(value=50, format="%p%")
                    ed.ProgressBar(value=0, min_value=0, max_value=0)
                with ed.HBoxView():
                    ed.ProgressBar(value=50, format="%p%", enabled=False)
                    ed.ProgressBar(value=0, min_value=0, max_value=0, enabled=False)
            with ed.TableGridRow():
                ed.Label("Slider")
                ed.Slider(value=50)
                ed.Slider(value=50, enabled=False)
            with ed.TableGridRow():
                ed.Label("ScrollBar")
                with ed.VScrollView():
                    ed.Label("ScrollBar")
                    ed.Label("ScrollBar")
                    ed.Label("ScrollBar")
                    ed.Label("ScrollBar")
                    ed.Label("ScrollBar")
                    ed.Label("ScrollBar")
                with ed.VScrollView(enabled=False):
                    ed.Label("ScrollBar")
                    ed.Label("ScrollBar")
                    ed.Label("ScrollBar")
                    ed.Label("ScrollBar")
                    ed.Label("ScrollBar")
                    ed.Label("ScrollBar")
            with ed.TableGridRow():
                ed.Label("Tooltip")
                ed.Label(
                    text="Hover for tooltip",
                    tool_tip="This is a tooltip",
                )
                ed.Label(
                    text="Hover for tooltip",
                    tool_tip="This is a tooltip",
                    enabled=False,
                )
            with ed.TableGridRow():
                ed.Label("Context Menu")
                ed.Label(
                    text="Right-click for menu",
                    context_menu=(
                        ("Action 1", lambda: None),
                        ("Action 2", lambda: None),
                        ("Submenu", (("Action 3", lambda: None), ("Action 4", lambda: None))),
                    ),
                )
                ed.Label(
                    text="Right-click for menu",
                    context_menu=(
                        ("Action 1", lambda: None),
                        ("Action 2", lambda: None),
                        ("Submenu", (("Action 3", lambda: None), ("Action 4", lambda: None))),
                    ),
                    enabled=False,
                )
            with ed.TableGridRow():
                ed.Label("BrightText")
                ed.Label(
                    text="BrightText",
                    style={"color": palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.BrightText).name()},
                )
            with ed.TableGridRow():
                ed.Label("Light")
                with ed.VBoxView(
                    style={
                        "background-color": palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Light).name(),
                    },
                ):
                    ed.Label("Lighter than Button color.")
            with ed.TableGridRow():
                ed.Label("Midlight")
                with ed.VBoxView(
                    style={
                        "background-color": palette.color(
                            QPalette.ColorGroup.Active,
                            QPalette.ColorRole.Midlight,
                        ).name(),
                    },
                ):
                    ed.Label("Between Button and Light.")
            with ed.TableGridRow():
                ed.Label("Button")
                with ed.VBoxView(
                    style={
                        "background-color": palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Button).name(),
                    },
                ):
                    pass
            with ed.TableGridRow():
                ed.Label("Mid")
                with ed.VBoxView(
                    style={
                        "background-color": palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Mid).name(),
                    },
                ):
                    ed.Label("Between Button and Dark.")
            with ed.TableGridRow():
                ed.Label("Dark")
                with ed.VBoxView(
                    style={
                        "background-color": palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Dark).name(),
                    },
                ):
                    ed.Label("Darker than Button.")
            with ed.TableGridRow():
                ed.Label("Shadow")
                with ed.VBoxView(
                    style={
                        "background-color": palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Shadow).name(),
                    },
                ):
                    ed.Label("Very Dark.")
            with ed.TableGridRow():
                ed.Label("solid")
                ed.Label(
                    text="solid",
                    style={"border": "5px solid"},
                )
                ed.Label(
                    text="solid",
                    style={"border": "5px solid"},
                    enabled=False,
                )
            with ed.TableGridRow():
                ed.Label("dashed")
                ed.Label(
                    text="dashed",
                    style={"border": "5px dashed"},
                )
            with ed.TableGridRow():
                ed.Label("dot-dash")
                ed.Label(
                    text="dot-dash",
                    style={"border": "5px dot-dash"},
                )
            with ed.TableGridRow():
                ed.Label("dotted")
                ed.Label(
                    text="dottted",
                    style={"border": "5px dotted"},
                )
            with ed.TableGridRow():
                ed.Label("double")
                ed.Label(
                    text="double",
                    style={"border": "5px double"},
                )
            with ed.TableGridRow():
                ed.Label("groove")
                ed.Label(
                    text="groove",
                    style={"border": "5px groove"},
                )
            with ed.TableGridRow():
                ed.Label("inset")
                ed.Label(
                    text="inset",
                    style={"border": "5px inset"},
                )
            with ed.TableGridRow():
                ed.Label("outset")
                ed.Label(
                    text="outset",
                    style={"border": "5px outset"},
                )
            with ed.TableGridRow():
                ed.Label("ridge")
                ed.Label(
                    text="ridge",
                    style={"border": "5px ridge"},
                )


if __name__ == "__main__":
    ed.App(Main()).start()
