import edifice as ed

from edifice.components import plotting
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class ViewWrapper(ed.Component):

    def render(self):
        return ed.View(layout="row", style={"border": "1px solid black", "min-width": "500px"}) (
            *self.children
        )

class Test2(ed.Component):
    
    def __init__(self, initial_text):
        super().__init__()
        self.text = initial_text
        self.initial_text = initial_text
        self.vm_state = 0
        self.color = "red"

    def on_click(self):
        print("CLCIKED")
        self.set_state(text="Hi", vm_state=1, color="blue")

    def render(self):
        children = [
            ed.Label(self.text, style={"color": self.color}).set_key("hi_text"),
            ed.Button("Toggle", on_click=lambda: self.on_click()).set_key("toggle button"),
        ]
        if self.vm_state == 1:
            children = [
                ed.Label(self.text, style={"color": "red"}).set_key("hi_text"),
                ed.Label("See this", style={"color": self.color}).set_key("vm_state"),
                ed.Button("Toggle", on_click=self.on_click).set_key("toggle button"),
            ]
        return ViewWrapper()(*children)


class Table(ed.Component):

    @ed.register_props
    def __init__(self, rows, columns, style=None, column_headers=None):
        pass



class SmartTable(ed.Component):

    @ed.register_props
    def __init__(self, data, style=None):
        super().__init__()
        self.key = None
        self.filter_text = None

    def on_change(self, i, text):
        with self.render_changes():
            self.key = self.props.data.keys()[i]
            self.filter_text = text

    def render(self):
        displayed_data = self.props.data
        if self.key is not None:
            displayed_data = self.props.data[self.props.data[self.key].astype(str).str.startswith(self.filter_text)]
        default_style = {
            "min-width": "500px",
            "min-height": "300px",
            "border-radius": "10px",
            "border": "1px solid black",
        }
        rows, columns = displayed_data.shape
        return ed.Table(rows=rows + 1, columns=columns, style=self.props.style or default_style, column_headers=list(displayed_data.keys()))(
            ed.List()(
                *[ed.TextInput(on_change=lambda text, i=i: self.on_change(i, text)).set_key("filter_%s" % i) for i in range(columns)]
            ),
            *[ed.List()(*[
                ed.Label(str(displayed_data.iloc[i, j])).set_key("%s_%s" % (i, j))
                for j in range(columns)])
                for i in range(rows)]
        )

class Test(ed.Component):

    @ed.register_props
    def __init__(self):
        super().__init__()
        self.a = 2
        self.t = np.linspace(0, 10)

    def on_change(self, value):
        self.set_state(a=value)

    def plot(self, ax):
        ax.plot(self.t, np.sin(self.t * self.a))

    def render(self):
        return ed.View(layout="column", style={"width": 380, "height": 380, "margin": 10}) (
            ed.Label(style={"width": 320, "height": 320}, text="""
                  The time.sleep() function uses the underlying operating system's sleep() function. Ultimately there are limitations of this function. For example on a standard Windows installation, the smallest interval you may sleep is 10 - 13 milliseconds. The Linux kernels tend to have a higher tick rate, where the intervals are generally closer to 1 millisecond. Note that in Linux, you can install the RT_PREEMPT patch set, which allows you to have a semi-realtime kernel. Using a real-time kernel will further increase the accuracy of the time.sleep() function. Generally however, unless you want to sleep for a very small period, you can generally ignore this information.
                  """)
        )


if __name__ == "__main__":
    ed.App(Test()).start()
