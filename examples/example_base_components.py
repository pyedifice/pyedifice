import typing as tp
import edifice as ed

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    pass
else:
    pass


@ed.component
def Main(self):
    mltext, mltext_set = ed.use_state("Hello World")
    ddoptions, ddoptionss_set = ed.use_state(0)
    ddoptions2, ddoptions2_set = ed.use_state(0)
    ddoptions3, ddoptions3_set = ed.use_state(0)
    sival, sival_set = ed.use_state(0)
    radio_value1, radio_value1_set = ed.use_state(tp.cast(tp.Literal["op1", "op2", "op3"], "op1"))
    radio_value2, radio_value2_set = ed.use_state(tp.cast(tp.Literal["op1", "op2", "op3"], "op1"))
    check_value1, check_value1_set = ed.use_state(True)

    put = ed.TreeBuilder()
    with put(ed.Window()) as root:
        put(ed.Label("Hello"))
        put(
            ed.Label(
                text="World",
                selectable=True,
            )
        )
        with put(ed.View(layout="row")):
            put(
                ed.Dropdown(
                    options=["Option set 1", "Option set 2"],
                    selection=ddoptions,
                    on_select=ddoptionss_set,
                    enable_mouse_scroll=False,
                )
            )
            match ddoptions:
                case 0:
                    put(
                        ed.Dropdown(
                            options=["Option set 1, 1", "Option set 1, 2", "Option set 1, 3"],
                            selection=ddoptions2,
                            on_select=ddoptions2_set,
                            enable_mouse_scroll=False,
                        )
                    )
                case 1:
                    put(
                        ed.Dropdown(
                            options=["Option set 2, 1", "Option set 2, 2", "Option set 2, 3"],
                            selection=ddoptions3,
                            on_select=ddoptions3_set,
                            enable_mouse_scroll=False,
                        )
                    )
        with put(ed.View(layout="row", style={"margin": 10})):
            put(
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
            )
            put(ed.Button("Exclaim text", on_click=lambda _: mltext_set("!" + mltext + "!")))
        with put(ed.View()):
            put(
                ed.SpinInput(
                    value=sival,
                    min_value=10,
                    max_value=20,
                    on_change=lambda v: (sival_set(v)),
                )
            )
        with put(ed.View(layout="row")):
            with put(ed.View()):
                # RadioButtons with the same parent
                put(
                    ed.RadioButton(
                        text="Option 1",
                        checked=radio_value1 == "op1",
                        on_change=lambda checked: radio_value1_set("op1") if checked else None,
                        style={} if radio_value1 == "op1" else {"color": "grey"},
                    )
                )
                put(
                    ed.RadioButton(
                        text="Option 2",
                        checked=radio_value1 == "op2",
                        on_change=lambda checked: radio_value1_set("op2") if checked else None,
                        style={} if radio_value1 == "op2" else {"color": "grey"},
                    )
                )
                put(
                    ed.RadioButton(
                        text="Option 3",
                        checked=radio_value1 == "op3",
                        on_change=lambda checked: radio_value1_set("op3") if checked else None,
                        style={} if radio_value1 == "op3" else {"color": "grey"},
                    )
                )
            with put(ed.View()):
                # RadioButtons with different parents
                with put(ed.View()):
                    put(
                        ed.RadioButton(
                            text="Option 1",
                            checked=radio_value2 == "op1",
                            on_change=lambda checked: radio_value2_set("op1") if checked else None,
                            style={
                                "color": "" if radio_value2 == "op1" else "grey",
                            },
                        )
                    )
                with put(ed.View()):
                    put(
                        ed.RadioButton(
                            text="Option 2",
                            checked=radio_value2 == "op2",
                            on_change=lambda checked: radio_value2_set("op2") if checked else None,
                            style={
                                "color": "" if radio_value2 == "op2" else "grey",
                            },
                        )
                    )
                with put(ed.View()):
                    put(
                        ed.RadioButton(
                            text="Option 3",
                            checked=radio_value2 == "op3",
                            on_change=lambda checked: radio_value2_set("op3") if checked else None,
                            style={
                                "color": "" if radio_value2 == "op3" else "grey",
                            },
                        )
                    )
        with put(ed.View(layout="row")):
            put(
                ed.CheckBox(
                    checked=True,
                    text="Check Const True",
                )
            )
            put(
                ed.CheckBox(
                    checked=False,
                    text="Check Const False",
                    style={"color": "grey"},
                )
            )
            put(
                ed.CheckBox(
                    checked=check_value1,
                    on_change=lambda checked: check_value1_set(checked),
                    text="Check",
                    style={} if check_value1 else {"color": "grey"},
                )
            )
        with put(
            ed.View(
                # https://doc.qt.io/qtforpython-6/overviews/stylesheet-customizing.html#the-box-model
                layout="row",
                style={
                    "border": "3px solid black",
                    "background-color": "white",
                    "color": "blue",
                    "padding": 3,
                },
            )
        ):
            put(
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
            )
            with put(
                ed.View(
                    style={
                        "padding": 20,
                        "border": "10px solid brown",
                    }
                )
            ):
                put(
                    ed.Label(
                        text="CONTENT2",
                        style={
                            "color": "black",
                            "background-color": "pink",
                        },
                    )
                )
    return root


if __name__ == "__main__":
    ed.App(Main()).start()
