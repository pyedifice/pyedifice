import edifice as ed
from edifice import Label, TextInput, View

METERS_TO_FEET = 3.28084


def str_to_float(s):
    try:
        return float(s)
    except ValueError:
        return 0.0

class ConversionWidget(ed.Component):

    @ed.register_props
    def __init__(self, from_unit, to_unit, factor):
        super().__init__()
        self.current_text = "0.0"

    def render(self):
        from_text = self.current_text
        to_text = "%.3f" % (str_to_float(from_text) * self.props.factor)

        from_label_style = {"width": 170}
        to_label_style = {"margin-left": 20, "width": 200}
        input_style = {"padding": 2, "width": 120}
        return ed.View(layout="row", style={"margin": 10, "width": 560})(
            Label(f"Measurement in {self.props.from_unit}:", style=from_label_style),
            TextInput(from_text, style=input_style,
                      on_change=lambda text: self.set_state(current_text=text)),
            Label(f"Measurement in {self.props.to_unit}: {to_text}", style=to_label_style),
        )

class MyApp(ed.Component):

    def render(self):
        return ed.View(layout="column", style={})(
            ConversionWidget("meters", "feet", METERS_TO_FEET),
            ConversionWidget("feet", "meters", 1 / METERS_TO_FEET),
        )

if __name__ == "__main__":
    ed.App(MyApp()).start()
