#
# python examples/calculator.py
#

import logging
import edifice as ed

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6":
    from PyQt6 import QtCore, QtGui
else:
    from PySide6 import QtCore, QtGui

logging.getLogger("Edifice").setLevel(logging.INFO)

OPERATORS = {
    "+": lambda stored, display: stored + display,
    "-": lambda stored, display: stored - display,
    "×": lambda stored, display: stored * display,
    "÷": lambda stored, display: stored / display,
    "+/-": lambda display: -display,
    "%": lambda display: display / 100,
    "AC": lambda display: 0,
}


window_style = {"background-color": "#404040", "height": 300, "width": 242}
button_style = {"font-size": 20, "color": "white", "height": 46, "width": 60, "border": "1px solid #333333"}
digits_style = button_style | {"background-color": "#777777"}
binary_style = button_style | {"background-color": "#ff9e00", "font-size": 30}
unary_style = button_style | {"background-color": "#595959"}
display_style = {"font-size": 50, "height": 70, "color": "white", "width": 240, "align": "right", "padding-right": 10}


@ed.component
def Calculator(self):
    # Simple calculator that doesn't reflect order of operations

    display, display_set = ed.use_state("0")
    stored_value, stored_value_set = ed.use_state(0.0)
    previous_operator, previous_operator_set = ed.use_state("")
    clear_display, clear_display_set = ed.use_state(True)

    def make_add_digit(digit):
        def add_digit(e: QtGui.QKeyEvent | None):
            if clear_display:
                display_ = "0"
                clear_display_set(False)
            else:
                display_ = display
            if digit == ".":
                try:
                    # See if adding a decimal is allowed at this point
                    _ = float(display_ + ".")
                    display_set(display_ + ".")
                except ValueError:
                    pass
            else:
                if display_ == "0":
                    display_set(str(digit))
                else:
                    display_set(display_ + str(digit))

        return add_digit

    def digit_button(digit, double_width=False):
        # Create digits buttons, include the decimal point
        button_style = digits_style.copy()
        if double_width:
            button_style["width"] = 2 * button_style["width"]
        return ed.Button(str(digit), style=button_style, on_click=make_add_digit(digit))

    def apply_binary_operand(operator):
        clear_display_set(True)
        display_set("0")
        if previous_operator == "" or previous_operator == "=":
            stored_value_set(float(display))
        else:
            val = OPERATORS[previous_operator](stored_value, float(display))
            stored_value_set(val)
            display_set("%.4f" % val)
        previous_operator_set(operator)

    def binary_button(symbol):
        # Qt layout is sometimes unintuitive, but you can definitely hack around it!
        button_style = binary_style.copy()
        return ed.Button(symbol, style=button_style, on_click=lambda e: apply_binary_operand(symbol))

    def unary_button(symbol):
        def apply_unary_operand(operator):
            clear_display_set(True)
            display_set("%.4f" % OPERATORS[operator](float(display)))

        return ed.Button(symbol, style=unary_style, on_click=lambda e: apply_unary_operand(symbol))

    def key_press(e: QtGui.QKeyEvent):
        if ord("0") <= e.key() <= ord("9"):
            make_add_digit(e.key() - ord("0"))(None)
        elif e.text() in ["+", "-", "*", "/"]:
            apply_binary_operand(e.text())
        elif e.key() == QtCore.Qt.Key.Key_Return:
            apply_binary_operand("=")

    return ed.View(layout="column", style=window_style, on_key_down=key_press)(
        ed.Label(display, style=display_style),
        ed.GridView(
            layout="""cs%/
                            789*
                            456-
                            123+
                            00.="""
        )(
            unary_button("AC").set_key("c"),
            unary_button("+/-").set_key("s"),
            unary_button("%").set_key("%"),
            binary_button("÷").set_key("/"),
            #
            digit_button(7).set_key("7"),
            digit_button(8).set_key("8"),
            digit_button(9).set_key("9"),
            binary_button("×").set_key("*"),
            #
            digit_button(4).set_key("4"),
            digit_button(5).set_key("5"),
            digit_button(6).set_key("6"),
            binary_button("-").set_key("-"),
            #
            digit_button(1).set_key("1"),
            digit_button(2).set_key("2"),
            digit_button(3).set_key("3"),
            binary_button("+").set_key("+"),
            #
            digit_button(0, double_width=True).set_key("0"),
            digit_button(".").set_key("."),
            binary_button("=").set_key("="),
        ),
    )


@ed.component
def Main(self):
    return ed.Window(title="Calculator")(
        Calculator(),
    )


if __name__ == "__main__":
    ed.App(Main()).start()
