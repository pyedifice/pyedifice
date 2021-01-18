import edifice as ed

from edifice.components import plotting
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class Test(ed.Component):

    @ed.register_props
    def __init__(self):
        super().__init__()
        self.a = 5
        self.t = np.linspace(0, 10)

    def on_change(self, value):
        self.set_state(a=value)

    def plot(self, ax):
        ax.plot(self.t, np.sin(self.t * self.a))

    def render(self):
        print("render", self.a)
        return ed.View(layout="column", style={}) (
            plotting.Figure(lambda figure: self.plot(figure)).set_key("plot"),
            ed.Slider(value=self.a, min_value=1, max_value=10, on_change=self.on_change).set_key("slider")
        )


if __name__ == "__main__":
    ed.App(Test()).start()
