from __future__ import annotations

import typing as tp

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtWidgets
    from PyQt6.QtGui import QPalette
else:
    from PySide6 import QtWidgets
    from PySide6.QtGui import QPalette


@ed.component
def Main(self):
    def initializer():
        palette = (
            ed.utilities.palette_edifice_light()
            if ed.utilities.theme_is_light()
            else ed.utilities.palette_edifice_dark()
        )
        tp.cast(QtWidgets.QApplication, QtWidgets.QApplication.instance()).setPalette(palette)
        return palette

    palette, _ = ed.use_state(initializer)

    with ed.Window(title="Style Matrix"):
        with ed.TableGridView(style={"padding": 10}) as tgv:
            with tgv.row():
                ed.Label("Label")
                with ed.VBoxView():
                    ed.Label(
                        text="""<h1>Heading 1</h1>
                            <h2>Heading 2</h2>
                            <h3>Heading 3</h3>
                            <p>Normal</p>""",
                        word_wrap=False,
                        selectable=True,
                    )
                    ed.Label(
                        text="""<a href='https://pyedifice.github.io'>https://pyedifice.github.io</a>""",
                        link_open=True,
                        word_wrap=False,
                    )
                with ed.VBoxView():
                    ed.Label(
                        text="""<h1>Heading 1</h1>
                            <h2>Heading 2</h2>
                            <h3>Heading 3</h3>
                            <p>Normal</p>""",
                        word_wrap=False,
                        selectable=True,
                        enabled=False,
                    )
                    ed.Label(
                        text="""<a href='https://pyedifice.github.io'>https://pyedifice.github.io</a>""",
                        link_open=True,
                        word_wrap=False,
                        enabled=False,
                    )
            with tgv.row():
                ed.Label("Icon")
                ed.Icon("home", size=20)
                ed.Icon("home", size=20, enabled=False)
            with tgv.row():
                ed.Label("TextInput")
                ed.TextInput("TextInput")
                ed.TextInput("TextInput", enabled=False)
            with tgv.row():
                ed.Label("Placeholder")
                ed.TextInput(placeholder_text="Placeholder")
                ed.TextInput(placeholder_text="Placeholder", enabled=False)
            with tgv.row():
                ed.Label("TextInputMultiline")
                ed.TextInputMultiline("TextInputMultiline")
                ed.TextInputMultiline("TextInputMultiline", enabled=False)
            with tgv.row():
                ed.Label("Button")
                ed.Button("Button")
                ed.Button("Button", enabled=False)
            with tgv.row():
                ed.Label("CheckBox")
                with ed.HBoxView():
                    ed.CheckBox(checked=True, text="CheckBox")
                    ed.CheckBox(checked=False, text="CheckBox")
                with ed.HBoxView():
                    ed.CheckBox(checked=True, text="CheckBox", enabled=False)
                    ed.CheckBox(checked=False, text="CheckBox", enabled=False)
            with tgv.row():
                ed.Label("RadioButton")
                with ed.HBoxView():
                    ed.RadioButton(text="RadioButton", checked=True)
                    ed.RadioButton(text="RadioButton", checked=False)
                with ed.HBoxView():
                    ed.RadioButton(text="RadioButton", checked=True, enabled=False)
                    ed.RadioButton(text="RadioButton", checked=False, enabled=False)
            with tgv.row():
                ed.Label("Dropdown")
                ed.Dropdown(options=["Option 1", "Option 2", "Option 3"])
                ed.Dropdown(options=["Option 1", "Option 2", "Option 3"], enabled=False)
            with tgv.row():
                ed.Label("SpinInput")
                ed.SpinInput()
                ed.SpinInput(enabled=False)
            with tgv.row():
                ed.Label("ButtonView")
                with ed.ButtonView():
                    ed.Icon("home", size=20)
                    ed.Label("ButtonView")
                with ed.ButtonView(enabled=False):
                    ed.Icon("home", size=20)
                    ed.Label("ButtonView")
            with tgv.row():
                ed.Label("ProgressBar")
                with ed.HBoxView():
                    ed.ProgressBar(value=50, format="%p%")
                    ed.ProgressBar(value=0, min_value=0, max_value=0)
                with ed.HBoxView():
                    ed.ProgressBar(value=50, format="%p%", enabled=False)
                    ed.ProgressBar(value=0, min_value=0, max_value=0, enabled=False)
            with tgv.row():
                ed.Label("Slider")
                ed.Slider(value=50)
                ed.Slider(value=50, enabled=False)
            with tgv.row():
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
            with tgv.row():
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
            with tgv.row():
                ed.Label("BrightText")
                ed.Label(
                    text="BrightText",
                    style={"color": palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.BrightText).name()},
                )
            with tgv.row():
                ed.Label("Light")
                with ed.VBoxView(
                    style={
                        "background-color": palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Light).name(),
                    },
                ):
                    ed.Label("Lighter than Button color.")
            with tgv.row():
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
            with tgv.row():
                ed.Label("Button")
                with ed.VBoxView(
                    style={
                        "background-color": palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Button).name(),
                    },
                ):
                    pass
            with tgv.row():
                ed.Label("Mid")
                with ed.VBoxView(
                    style={
                        "background-color": palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Mid).name(),
                    },
                ):
                    ed.Label("Between Button and Dark.")
            with tgv.row():
                ed.Label("Dark")
                with ed.VBoxView(
                    style={
                        "background-color": palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Dark).name(),
                    },
                ):
                    ed.Label("Darker than Button.")
            with tgv.row():
                ed.Label("Shadow")
                with ed.VBoxView(
                    style={
                        "background-color": palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Shadow).name(),
                    },
                ):
                    ed.Label("Very Dark.")
            with tgv.row():
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
            with tgv.row():
                ed.Label("dashed")
                ed.Label(
                    text="dashed",
                    style={"border": "5px dashed"},
                )
            with tgv.row():
                ed.Label("dot-dash")
                ed.Label(
                    text="dot-dash",
                    style={"border": "5px dot-dash"},
                )
            with tgv.row():
                ed.Label("dotted")
                ed.Label(
                    text="dottted",
                    style={"border": "5px dotted"},
                )
            with tgv.row():
                ed.Label("double")
                ed.Label(
                    text="double",
                    style={"border": "5px double"},
                )
            with tgv.row():
                ed.Label("groove")
                ed.Label(
                    text="groove",
                    style={"border": "5px groove"},
                )
            with tgv.row():
                ed.Label("inset")
                ed.Label(
                    text="inset",
                    style={"border": "5px inset"},
                )
            with tgv.row():
                ed.Label("outset")
                ed.Label(
                    text="outset",
                    style={"border": "5px outset"},
                )
            with tgv.row():
                ed.Label("ridge")
                ed.Label(
                    text="ridge",
                    style={"border": "5px ridge"},
                )


if __name__ == "__main__":
    ed.App(Main()).start()
