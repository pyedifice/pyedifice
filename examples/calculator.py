import edifice as ed

OPERATORS = {
    "+": lambda stored, display: stored + display,
    "-": lambda stored, display: stored - display,
    "×": lambda stored, display: stored * display,
    "÷": lambda stored, display: stored / display,
    "+/-": lambda display: -display,
    "%": lambda display: display / 100,
    "AC": lambda display: 0,
}


class Calculator(ed.Component):
    # Simple calculator that doesn't reflect order of operations

    def __init__(self):
        super().__init__()
        # Currently displayed value
        self.display = "0"
        # Results of computations
        self.stored_value = 0
        # The previously pressed operator. After pressing an operator button,
        # calculators display the result of the *previous* calculation
        self.previous_operator = None
        # After pressing an operation, the next digit press should clear the display
        self.clear_display = True

    def render(self):
        window_style = {"background-color": "#404040", "height": 300, "width": 242}
        button_style = {"font-size": 20, "color": "white", "height": 60, "width": 60, "border": "1px solid #333333"}
        digits_style = button_style | {"background-color": "#777777"}
        binary_style = button_style | {"background-color": "#ff9e00", "font-size": 30}
        unary_style = button_style | {"background-color": "#595959"}
        display_style = {"font-size": 50, "height": 70, "color": "white", "width": 240, "align": "right", "padding-right": 10}

        def make_add_digit(digit):
            def add_digit(e):
                with self.render_changes():
                    if self.clear_display:
                        self.display = "0"
                        self.clear_display = False
                    if digit == ".":
                        try:
                            # See if adding a decimal is allowed at this point
                            _ = float(self.display + ".")
                            self.display += "."
                        except ValueError:
                            pass
                    else:
                        if self.display == "0":
                            self.display = str(digit)
                        else:
                            self.display += str(digit)
            return add_digit

        def digit_button(digit, double_width=False):
            # Create digits buttons, include the decimal point
            button_style = digits_style.copy()
            if double_width:
                button_style["width"] = 2 * button_style["width"]
            return ed.Button(str(digit), style=button_style, on_click=make_add_digit(digit))

        def apply_binary_operand(operator):
            with self.render_changes():
                self.clear_display = True
                if self.previous_operator is None or self.previous_operator == "=":
                    self.stored_value = float(self.display)
                else:
                    self.stored_value = OPERATORS[self.previous_operator](self.stored_value, float(self.display))
                    self.display = "%.4f" % self.stored_value
                self.previous_operator = operator

        def binary_button(symbol):
            # Qt layout is sometimes unintuitive, but you can definitely hack around it!
            button_style = binary_style.copy()
            return ed.Button(symbol, style=button_style, on_click=lambda e: apply_binary_operand(symbol))

        def unary_button(symbol):
            def apply_unary_operand(operator):
                with self.render_changes():
                    self.clear_display = True
                    self.display = "%.4f" % OPERATORS[operator](float(self.display))
            return ed.Button(symbol, style=unary_style, on_click=lambda e: apply_unary_operand(symbol))

        def key_press(e):
            if ord('0') <= e.key() <= ord('9'):
                make_add_digit(e.key() - ord('0'))(None)
            elif e.text() in ['+', '-', '*', '/']:
                apply_binary_operand(e.text())
            elif e.key() == ed.Key.Key_Return:
                apply_binary_operand("=")

        return ed.Window(title="Calculator")(
            ed.View(layout="column", style=window_style, on_key_down=key_press)(
                ed.Label(self.display, style=display_style),
                ed.GridView(layout="""cs%/
                                      789*
                                      456-
                                      123+
                                      00.=""")(
                    unary_button("AC").set_key("c"), unary_button("+/-").set_key("s"), unary_button("%").set_key("%"), binary_button("÷").set_key("/"),
                    digit_button(7).set_key("7"), digit_button(8).set_key("8"), digit_button(9).set_key("9"), binary_button("×").set_key("*"),
                    digit_button(4).set_key("4"), digit_button(5).set_key("5"), digit_button(6).set_key("6"), binary_button("-").set_key("-"),
                    digit_button(1).set_key("1"), digit_button(2).set_key("2"), digit_button(3).set_key("3"), binary_button("+").set_key("+"),
                    digit_button(0, double_width=True).set_key("0"), digit_button(".").set_key("."), binary_button("=").set_key("="),
                )
            )
        )

if __name__ == "__main__":
    ed.App(Calculator()).start()
