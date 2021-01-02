import react
import pandas as pd


class ViewWrapper(react.Component):

    def render(self):
        return react.View(layout="row", style={"border": "1px solid black"}) (
            *self.children
        )

class Test2(react.Component):
    
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
            react.Label(self.text, style={"color": self.color}).set_key("hi_text"),
            react.Button("Toggle", on_click=lambda: self.on_click()).set_key("toggle button"),
        ]
        if self.vm_state == 1:
            children = [
                react.Label(self.text, style={"color": "red"}).set_key("hi_text"),
                react.Label("See this", style={"color": self.color}).set_key("vm_state"),
                react.Button("Toggle", on_click=self.on_click).set_key("toggle button"),
            ]
        return ViewWrapper()(*children)


class Table(react.Component):

    def __init__(self, rows, columns, style=None, column_headers=None):
        super().__init__(["rows", "columns", "style", "column_headers"])



class SmartTable(react.Component):

    @react.register_props
    def __init__(self, data, style=None):
        super().__init__()
        self.data = data
        self.displayed_data = data
        self.style = style or {
            "width": "500px",
            "height": "300px",
            "border-radius": "10px",
            "border": "1px solid black",
        }

    def on_change(self, i, text):
        key = self.data.keys()[i]
        with self.render_changes():
            self.displayed_data = self.data[self.data[key].astype(str).str.startswith(text)]

    def render(self):
        rows, columns = self.displayed_data.shape
        return react.Table(rows=rows + 1, columns=columns, style=self.style, column_headers=list(self.displayed_data.keys()))(
            react.List()(
                *[react.TextInput(on_change=lambda text, i=i: self.on_change(i, text)).set_key("filter_%s" % i) for i in range(columns)]
            ),
            *[react.List()(*[
                react.Label(str(self.displayed_data.iloc[i, j])).set_key("%s_%s" % (i, j))
                for j in range(columns)])
                for i in range(rows)]
        )

class Test(react.Component):

    def __init__(self):
        super().__init__()
        self.text = ""
        self.open = True
        self.dimensions = (1, 3)
        self.data = pd.DataFrame({
            "a": [2, 5, 6, 3, 21],
            "b": [3, 3, 1, 8, 11],
            "c": [4, 7, 1, 0, 10],
        })

    def on_change(self, text):
        self.set_state(text=text)

    def on_click(self):
        with self.render_changes():
            self.data = self.data + 5

    def render(self):
        return react.WindowManager()(
            react.View() (
                react.Label("Hello world: " + self.text),
                react.TextInput(self.text, on_change=self.on_change),
                Test2("Bonjour"),
                SmartTable(self.data),
                react.Button("Add 5", on_click=self.on_click)
            ),
        )

react.App(Test()).start()
