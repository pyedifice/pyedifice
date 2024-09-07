#
# python examples/tutorial.py
#

import logging

from edifice import App, HBoxView, Label, TextInput, Window, component, use_state

logging.getLogger("Edifice").setLevel(logging.INFO)

METERS_TO_FEET = 3.28084


@component
def ConversionWidget(self, from_unit, to_unit, factor):
    current_text, current_text_set = use_state("0.0")

    from_label_style = {"width": 170}
    to_label_style = {"margin-left": 10, "width": 220}
    input_style = {"padding": 2, "width": 120}
    with HBoxView(style={"padding": 10, "align": "left"}):
        Label(f"Measurement in {from_unit}:", style=from_label_style)
        TextInput(current_text, style=input_style, on_change=current_text_set)
        try:
            to_text = "%.3f" % (float(current_text) * factor)
            Label(f"Measurement in {to_unit}: {to_text}", style=to_label_style)
        except ValueError:  # Could not convert string to float
            pass  # So don't render the Label


@component
def MyApp(self):
    with Window(title="Measurement Conversion"):
        ConversionWidget("meters", "feet", METERS_TO_FEET)
        ConversionWidget("feet", "meters", 1 / METERS_TO_FEET)


if __name__ == "__main__":
    App(MyApp()).start()
