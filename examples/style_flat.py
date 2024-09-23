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

def global_style(p:QPalette):
    return """

/* Base Styles */
QWidget {
    background-color: #FAFAFA;  /* Light background for the application */
    color: #212121;
    font-family: Roboto, sans-serif;
    font-size: 14px;
}

/* Push Buttons */
QPushButton {
    background-color: #6200EE;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 500;
    box-shadow: 0px 2px 2px rgba(0, 0, 0, 0.2); /* Elevation */
}

QPushButton:hover {
    background-color: #3700B3;
}

QPushButton:pressed {
    background-color: #03DAC5;
}

QPushButton:disabled {
    background-color: #BDBDBD;
    color: white;
}

/* Flat (Text) Buttons */
QPushButton#flatButton {
    background-color: transparent;
    color: #6200EE;
    padding: 8px;
}

QPushButton#flatButton:hover {
    background-color: rgba(98, 0, 238, 0.1);
}

/* ComboBox */
QComboBox {
    border: none;
    border-bottom: 2px solid #6200EE;
    background-color: transparent;
    padding: 8px;
    font-size: 16px;
}

QComboBox::drop-down {
    width: 30px;
    border: none;
    background: #6200EE;
}

QComboBox::down-arrow {
    image: url(":/icons/arrow_down.svg");  /* Add a custom down arrow */
}

QComboBox QAbstractItemView {
    background-color: white;
    border: 1px solid #BDBDBD;
    selection-background-color: #6200EE;
}

/* SpinBox */
QSpinBox {
    border: none;
    border-bottom: 2px solid #6200EE;
    background-color: transparent;
    padding: 8px;
    font-size: 16px;
}

QSpinBox::up-button, QSpinBox::down-button {
    background-color: transparent;
    border: none;
    width: 14px;
    height: 14px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: rgba(98, 0, 238, 0.1);
}

QSpinBox::up-arrow {
    image: url(":/icons/arrow_up.svg");
}

QSpinBox::down-arrow {
    image: url(":/icons/arrow_down.svg");
}

/* ProgressBar */
QProgressBar {
    border: 1px solid #BDBDBD;
    border-radius: 5px;
    text-align: center;
    background-color: #E0E0E0;
    height: 20px;
}

QProgressBar::chunk {
    background-color: #6200EE;
    border-radius: 5px;
}

/* Slider */
QSlider::groove:horizontal {
    height: 6px;
    background: #BDBDBD;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #6200EE;
    border: none;
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -6px 0;
}

QSlider::handle:horizontal:hover {
    background-color: #03DAC5;
}

/* CheckBox */
QCheckBox {
    spacing: 8px;
    color: #212121;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
}

QCheckBox::indicator:unchecked {
    border: 2px solid #6200EE;
    border-radius: 2px;
    background-color: white;
}

QCheckBox::indicator:checked {
    background-color: #6200EE;
    image: url(':/icons/checkmark.svg'); /* Custom checkmark */
}

/* RadioButton */
QRadioButton {
    spacing: 8px;
    color: #212121;
}

QRadioButton::indicator {
    width: 20px;
    height: 20px;
    border-radius: 10px;
}

QRadioButton::indicator:unchecked {
    border: 2px solid #6200EE;
    background-color: transparent;
}

QRadioButton::indicator:checked {
    background-color: #6200EE;
}

/* Line Edit */
QLineEdit {
    border: none;
    border-bottom: 2px solid #6200EE;
    padding: 8px;
    background-color: transparent;
    font-size: 16px;
}

QLineEdit:focus {
    border-bottom: 2px solid #03DAC5;
}

QLineEdit:disabled {
    border-bottom: 2px solid #BDBDBD;
    color: #BDBDBD;
}

/* Group Box */
QGroupBox {
    border: 2px solid #6200EE;
    border-radius: 8px;
    margin-top: 20px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 3px;
    color: #6200EE;
}

/* ScrollBar */
QScrollBar:vertical {
    border: none;
    background: #E0E0E0;
    width: 12px;
    margin: 0px 0px 0px 0px;
}

QScrollBar::handle:vertical {
    background: #6200EE;
    min-height: 20px;
    border-radius: 6px;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background: none;
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* ScrollArea */
QScrollArea {
    border: none;
    background: #FAFAFA;
}

/* ToolTip */
QToolTip {
    background-color: #6200EE;
    color: white;
    border-radius: 4px;
    padding: 4px;
    opacity: 220;
}

/* TabWidget */
QTabWidget::pane {
    border: 1px solid #6200EE;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #E0E0E0;
    padding: 10px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #6200EE;
    color: white;
}

QTabBar::tab:hover {
    background-color: #3700B3;
}

/* Dialog */
QDialog {
    background-color: white;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.2); /* Elevation */
}

/* MenuBar */
QMenuBar {
    background-color: #6200EE;
    color: white;
    padding: 5px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 4px 20px;
}

QMenuBar::item:selected {
    background-color: #3700B3;
}

/* ToolButton */
QToolButton {
    background-color: transparent;
    color: #6200EE;
    padding: 8px;
}

QToolButton:hover {
    background-color: rgba(98, 0, 238, 0.1);
}

/* Message Box */
QMessageBox {
    background-color: white;
    border-radius: 8px;
}

QMessageBox QLabel {
    font-size: 16px;
    padding: 20px;
}

QMessageBox QPushButton {
    background-color: #6200EE;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
}

"""


# def global_style(p:QPalette):
#     return f"""
# QPushButton {{
#     border-style: none;
#     border-radius: 8px;
# }}
# QPushButton:hover {{
#     background-color: {p.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Mid).name()};
# }}
# QPushButton:pressed {{
#     background-color: {p.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Dark).name()};
# }}
# QComboBox {{
#     border-style: none;
#     border-radius: 0px;
# }}
# QComboBox:hover {{
#     background-color: {p.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Mid).name()};
# }}
# QComboBox:pressed {{
#     background-color: {p.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Dark).name()};
# }}
# /*
# QSlider::handle:horizontal {{
#     width: 50px;
#     height: 50px;
#     margin: -24px -12px;
#     height: -30px;
# }}
# QSlider::handle:vertical {{
#     width: 50px;
#     height: 50px;
#     margin: -24px -12px;
#     height: -30px;
# }}
# QSlider::groove:vertical {{
#     border: 1px solid #111;
#     background-color: #333;
#     width: 6px;
#     margin: 24px 12px;
# }}
# QSlider::handle:vertical {{
#     margin: -24px -12px;
#     height: -30px;
# }}
# QSlider:horizontal {{
# height: 30px;
# }}
# */
#
#
# QSlider::groove:horizontal {{
# border: 1px solid #000;
# height: 6px;
# border-radius: 4px;
# }}
# QSlider::sub-page:horizontal {{
# background: qlineargradient(x1: 0, y1: 0,   x2: 0, y2: 1,
#     stop: 0 #666666, stop: 1 #888888);
# background: qlineargradient(x1: 0, y1: 0.2, x2: 1, y2: 1,
#     stop: 0 #888888, stop: 1 #666666);
# border: 1px solid #777;
# height: 10px;
# border-radius: 4px;
# }}
# QSlider::add-page:horizontal {{
# background: rgba(127,127,127,127);
# border: 1px solid #777;
# height: 10px;
# border-radius: 4px;
# }}
# QSlider::handle:horizontal {{
# background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
#     stop:0 #eee, stop:1 #ccc);
# border: 1px solid #777;
# width: 13px;
# margin-top: -10px;
# margin-bottom: -10px;
# border-radius: 4px;
# }}
# QSlider::handle:horizontal:hover {{
# background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
#     stop:0 #fff, stop:1 #ddd);
# border: 1px solid #444;
# border-radius: 4px;
# }}
# QSlider::sub-page:horizontal:disabled {{
# background: #bbb;
# border-color: #999;
# }}
# QSlider::add-page:horizontal:disabled {{
# background: #eee;
# border-color: #999;
# }}
# QSlider::handle:horizontal:disabled {{
# background: #eee;
# border: 1px solid #aaa;
# border-radius: 4px;
# }}
#
#
# """



@ed.component
def Main(self):
    def initializer():
        palette = (
            ed.utilities.palette_edifice_light()
            if ed.utilities.theme_is_light()
            else ed.utilities.palette_edifice_dark()
        )
        qapp = tp.cast(QtWidgets.QApplication, QtWidgets.QApplication.instance())
        qapp.setPalette(palette)
        qapp.setStyleSheet(global_style(palette))

        return palette

    palette, _ = ed.use_state(initializer)

    somestate, somestate_set = ed.use_state(0)

    with ed.Window(title="Style Matrix"):
        with ed.TableGridView(style={"padding": 10}):
            with ed.TableGridRow():
                ed.Label("Label")
                ed.Label(
                    text="""<h1>Heading 1</h1>
                        <h2>Heading 2</h2>
                        <h3>Heading 3</h3>
                        <p>Normal<p>
                        <a href='https://pyedifice.github.io'>https://pyedifice.github.io</a>
                        """,
                    link_open=True,
                    word_wrap=False,
                )
                ed.Label(
                    text="""<h1>Heading 1</h1>
                        <h2>Heading 2</h2>
                        <h3>Heading 3</h3>
                        <p>Normal<p>
                        <a href='https://pyedifice.github.io'>https://pyedifice.github.io</a>
                        """,
                    link_open=True,
                    word_wrap=False,
                    enabled=False,
                )
            with ed.TableGridRow():
                ed.Label("Icon")
                ed.Icon("home", size=20)
                ed.Icon("home", size=20, enabled=False)
            with ed.TableGridRow():
                ed.Label("TextInput")
                ed.TextInput("TextInput")
                ed.TextInput("TextInput", enabled=False)
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
                ed.Button("Button", on_click=lambda _: somestate_set(somestate + 1))
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
                    ed.Icon("home", size=20)
                    ed.Label("ButtonView")
                with ed.ButtonView(enabled=False):
                    ed.Icon("home", size=20)
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
