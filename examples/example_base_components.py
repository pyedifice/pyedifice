from __future__ import annotations

import datetime as dt
import re
import typing as tp

import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QCloseEvent, QFont, QKeyEvent, QValidator
    from PyQt6.QtWidgets import QApplication, QCompleter
else:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QCloseEvent, QFont, QKeyEvent, QValidator
    from PySide6.QtWidgets import QApplication, QCompleter


@ed.component
def Main(self):
    def handle_open(qapp: QApplication):
        print("Opening window")  # noqa: T201

    def handle_close(ev: QCloseEvent):
        print("Closing window")  # noqa: T201

    def initializer():
        qapp = tp.cast(QApplication, QApplication.instance())
        qapp.setApplicationName("Example Base Components")
        QApplication.setStyle("fusion")
        qapp.setFont(QFont("Yu Gothic UI", 20))
        if ed.theme_is_light():
            qapp.setPalette(ed.palette_edifice_light())
        else:
            qapp.setPalette(ed.palette_edifice_dark())

    ed.use_state(initializer)

    text1, text1_set = ed.use_state("")
    mltext, mltext_set = ed.use_state("Hello World")
    ddoptions, ddoptionss_set = ed.use_state(0)
    ddoptions2, ddoptions2_set = ed.use_state(0)
    ddoptions3, ddoptions3_set = ed.use_state(0)
    sival, sival_set = ed.use_state(0)
    smillimeters, smillimeters_set = ed.use_state(0)
    radio_value1, radio_value1_set = ed.use_state(tp.cast(tp.Literal["op1", "op2", "op3"], "op1"))
    radio_value2, radio_value2_set = ed.use_state(tp.cast(tp.Literal["op1", "op2", "op3"], "op1"))
    check_value1, check_value1_set = ed.use_state(True)
    n = dt.datetime.now()  # noqa: DTZ005
    n = dt.datetime(n.year, n.month, n.day, n.hour, n.minute, n.second)  # remove microseconds  # noqa: DTZ001
    date_value, date_value_set = ed.use_state(tp.cast(dt.date | ValueError, n.date()))
    date_text, date_text_set = ed.use_state(n.date().isoformat())
    time_value, time_value_set = ed.use_state(tp.cast(dt.time | ValueError, n.time()))
    time_text, time_text_set = ed.use_state(n.time().isoformat())

    float1, float1_set = ed.use_state(0.0)

    upperlower, upperlower_set = ed.use_state("")

    with ed.Window(
        _on_open=handle_open,
        on_close=handle_close,
        title="Example Base Components",
    ):
        with ed.HBoxView():
            with ed.VBoxView():
                ed.Label("Hello")
                ed.Label(
                    text="World",
                    selectable=True,
                )
            with ed.VBoxView():
                ed.Label(
                    text="""<h2>Title</h2>
                    <p><i>Para</i>graph</p>""",
                    text_format=Qt.TextFormat.RichText,
                    selectable=True,
                )
            with ed.VBoxView():
                ed.Label(
                    text="""## Title

*Para*graph""",
                    text_format=Qt.TextFormat.MarkdownText,
                    selectable=True,
                )
        with ed.HBoxView():
            ed.TextInput(
                text=text1,
                placeholder_text="TextInput with repetitive completions suggestions",
                completer=(
                    QCompleter.CompletionMode.UnfilteredPopupCompletion,
                    # > QCompleter.CompletionMode.InlineCompletion,
                    (
                        text1 + text1,
                        text1 + text1 + text1,
                        text1 + text1 + text1 + text1,
                    ),
                )
                if len(text1) > 0
                else None,
                on_change=text1_set,
            )
        with ed.HBoxView():
            ed.Dropdown(
                options=["Option set 1", "Option set 2"],
                selection=ddoptions,
                on_select=ddoptionss_set,
                enable_mouse_scroll=False,
            )
            match ddoptions:
                case 0:
                    ed.Dropdown(
                        options=["Option set 1, 1", "Option set 1, 2", "Option set 1, 3"],
                        selection=ddoptions2,
                        on_select=ddoptions2_set,
                        enable_mouse_scroll=False,
                    )
                case 1:
                    ed.Dropdown(
                        options=["Option set 2, 1", "Option set 2, 2", "Option set 2, 3"],
                        selection=ddoptions3,
                        on_select=ddoptions3_set,
                        enable_mouse_scroll=False,
                    )
        with ed.HBoxView(style={"padding": 10}):
            ed.TextInputMultiline(
                text=mltext,
                on_change=mltext_set,
                placeholder_text="Type here",
                style={
                    "min-height": 100,
                    "border": "1px solid black",
                    "font-size": "20px",
                    "font-family": "Courier New",
                    "font-style": "italic",
                },
            )
            ed.Button("Exclaim text", on_click=lambda _: mltext_set("!" + mltext + "!"))

        with ed.VBoxView():
            ed.SpinInput(
                value=sival,
                min_value=10,
                max_value=20,
                on_change=sival_set,
                enable_mouse_scroll=False,
            )

            def text_to_meters(text: str) -> int | QValidator.State.Intermediate | QValidator.State.Invalid: # type: ignore  # noqa: PGH003
                try:
                    # search for a decimal number in the text
                    matches = re.search(r"(\d*\.?\d*)", text)
                    if matches is not None and len(matches.groups()) > 0:
                        return int(float(matches.groups()[0]) * 1000)
                except ValueError:
                    return QValidator.State.Intermediate

            def meters_to_text(millimeters: int) -> str:
                return f"{(float(millimeters) / 1000):.3f} meters"

            ed.SpinInput(
                value=smillimeters,
                min_value=0,
                max_value=100000,
                on_change=smillimeters_set,
                text_to_value=text_to_meters,
                value_to_text=meters_to_text,
                single_step=1000,
            )

            def float1_to_text(value:int) -> str:
                return f"{float(value)/100.0:.2f}"
            def text_to_float1(text:str) -> int | QValidator.State.Intermediate | QValidator.State.Invalid: # type: ignore  # noqa: PGH003
                try:
                    return int(float(text) * 100.0)
                except ValueError:
                    return QValidator.State.Intermediate

            ed.SpinInput(
                min_value=100,
                max_value=1000000,
                value=int(float1 * 100.0),
                on_change=lambda int1: float1_set(float(int1) / 100.0),
                value_to_text=float1_to_text,
                text_to_value=text_to_float1,
                single_step=100,
            )

        with ed.HBoxView():
            with ed.VBoxView():
                # RadioButtons with the same parent
                ed.RadioButton(
                    text="Option 1",
                    checked=radio_value1 == "op1",
                    on_change=lambda checked: radio_value1_set("op1") if checked else None,
                    style={} if radio_value1 == "op1" else {"color": "grey"},
                )
                ed.RadioButton(
                    text="Option 2",
                    checked=radio_value1 == "op2",
                    on_change=lambda checked: radio_value1_set("op2") if checked else None,
                    style={} if radio_value1 == "op2" else {"color": "grey"},
                )
                ed.RadioButton(
                    text="Option 3",
                    checked=radio_value1 == "op3",
                    on_change=lambda checked: radio_value1_set("op3") if checked else None,
                    style={} if radio_value1 == "op3" else {"color": "grey"},
                )
            with ed.VBoxView():
                # RadioButtons with different parents
                with ed.VBoxView():
                    ed.RadioButton(
                        text="Option 1",
                        checked=radio_value2 == "op1",
                        on_change=lambda checked: radio_value2_set("op1") if checked else None,
                        style={
                            "color": "" if radio_value2 == "op1" else "grey",
                        },
                    )
                with ed.VBoxView():
                    ed.RadioButton(
                        text="Option 2",
                        checked=radio_value2 == "op2",
                        on_change=lambda checked: radio_value2_set("op2") if checked else None,
                        style={
                            "color": "" if radio_value2 == "op2" else "grey",
                        },
                    )
                with ed.VBoxView():
                    ed.RadioButton(
                        text="Option 3",
                        checked=radio_value2 == "op3",
                        on_change=lambda checked: radio_value2_set("op3") if checked else None,
                        style={
                            "color": "" if radio_value2 == "op3" else "grey",
                        },
                    )
        with ed.HBoxView():
            ed.CheckBox(
                checked=True,
                text="Check Const True",
            )
            ed.CheckBox(
                checked=False,
                text="Check Const False",
                style={"color": "grey"},
            )
            ed.CheckBox(
                checked=check_value1,
                on_change=lambda checked: check_value1_set(checked),
                text="Check",
                style={} if check_value1 else {"color": "grey"},
            )
        with ed.HBoxView(
            # https://doc.qt.io/qtforpython-6/overviews/stylesheet-customizing.html#the-box-model
            style={
                "border": "3px solid black",
                "background-color": "white",
                "color": "blue",
                "padding": 3,
            },
        ):
            ed.Label(
                text="CONTENT1",
                style={
                    "color": "black",
                    "margin": "10px",
                    "padding": "20px",
                    "border": "10px solid brown",
                    "background-color": "pink",
                },
            )
            with ed.VBoxView(
                style={
                    "padding": 20,
                    "border": "10px solid brown",
                },
            ):
                ed.Label(
                    text="CONTENT2",
                    style={
                        "color": "black",
                        "background-color": "pink",
                    },
                )
        with ed.TableGridView(style={"padding": 10}):
            with ed.TableGridRow():

                def handle_date(text: str):
                    date_text_set(text)
                    matches = re.findall(r"(\d+)", text)
                    if matches is not None and len(matches) == 3:
                        try:
                            date_value_set(dt.date(int(matches[0]), int(matches[1]), int(matches[2])))
                        except ValueError as ex:
                            date_value_set(ex)
                    else:
                        date_value_set(ValueError("Need year-month-day"))

                ed.Label(text="Date")
                ed.TextInput(
                    text=date_text,
                    on_change=handle_date,
                )
                match date_value:
                    case ValueError():
                        ed.Label(
                            text=str(date_value),
                            style={"background-color": "red"},
                        )
                    case dt.date():
                        ed.Label(
                            text=date_value.strftime("%Y %B %d %A"),
                        )
            with ed.TableGridRow():

                def handle_time(text: str):
                    time_text_set(text)
                    matches = re.findall(r"(\d+)", text)
                    if matches is not None and len(matches) == 3:
                        try:
                            time_value_set(dt.time(int(matches[0]), int(matches[1]), int(matches[2])))
                        except ValueError as ex:
                            time_value_set(ex)
                    else:
                        time_value_set(ValueError("Need hour:minute:second"))

                ed.Label(text="Time")
                ed.TextInput(
                    text=time_text,
                    on_change=handle_time,
                )
                match time_value:
                    case ValueError():
                        ed.Label(
                            text=str(time_value),
                            style={"background-color": "red"},
                        )
                    case dt.time():
                        ed.Label(
                            text=time_value.strftime("%H:%M:%S"),
                        )
        def handle_updown(event: QKeyEvent):
            # if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Up:
            if event.key() == Qt.Key.Key_Up:
               upperlower_set(upperlower.upper())
            elif event.key() == Qt.Key.Key_Down:
               upperlower_set(upperlower.lower())

        with ed.VBoxView():
            ed.TextInput(
                text=upperlower,
                on_change=upperlower_set,
                placeholder_text="Press 🡅 🡇 to change uppercase/lowercase",
                on_key_down=handle_updown,
            )

        tab1, tab1_set = ed.use_state(True)
        tab2, tab2_set = ed.use_state(True)
        tab3, tab3_set = ed.use_state(True)
        with ed.VBoxView():

            with ed.HBoxView():
                ed.CheckBox(checked = tab1, on_change = tab1_set, text = "Tab 1")
                ed.CheckBox(checked = tab2, on_change = tab2_set, text = "Tab 2")
                ed.CheckBox(checked = tab3, on_change = tab3_set, text = "Tab 3")
            with ed.TabView(
                labels=(
                    (("Tab 1",) if tab1 else ())
                    + (("Tab 2",) if tab2 else ())
                    + (("Tab 3",) if tab3 else ())
                ),
            ):
                if tab1:
                    with ed.VBoxView().set_key("tab1"):
                        ed.Label("Tab 1")
                        ed.Label("Content 1")
                if tab2:
                    with ed.VBoxView().set_key("tab2"):
                        ed.Label("Tab 2")
                        ed.Label("Content 2")
                if tab3:
                    with ed.VBoxView().set_key("tab3"):
                        ed.Label("Tab 3")
                        ed.Label("Content 3")


if __name__ == "__main__":
    ed.App(Main()).start()
