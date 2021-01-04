import edifice as ed
import pandas as pd


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
        self.text = ""
        self.open = True
        self.hi_text = "Hi"
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
        return ed.WindowManager()(
            ed.View() (
                # SmartTable(self.data),
                ed.Label(self.hi_text),
                ed.Icon("play"),
                ed.IconButton(name="play", title="Change", on_click=lambda: self.set_state(hi_text="Hello")),
                # ed.Button("Add 5", on_click=self.on_click),
                # ed.ScrollView(style={"min-width": 100, "min-height": 100, "max-height": 100, "height": 100})(
                #     *[ed.Label(i) for i in range(20)]
                # )
            ),
        )

class Test(ed.Component):

    @ed.register_props
    def __init__(self):
        super().__init__()
        self.text = ""
        self.open = True
        self.hi_text = "Hi"
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
        return ed.WindowManager()(
            ed.View() (
                # SmartTable(self.data),
                ed.Label(self.hi_text),
                ed.Icon("play"),
                ed.IconButton(name="play", title="Change", on_click=lambda: self.set_state(hi_text="Hello")),
                # ed.Button("Add 5", on_click=self.on_click),
                # ed.ScrollView(style={"min-width": 100, "min-height": 100, "max-height": 100, "height": 100})(
                #     *[ed.Label(i) for i in range(20)]
                # )
            ),
        )


class _TestComponentInner(ed.Component):

    @ed.register_props
    def __init__(self, prop_a):
        self.state_a = "A"

    def render(self):
        return ed.View(layout="row")(
            ed.Label(self.props.prop_a),
            ed.Label(self.state_a),
            ed.Button("MarkState", on_click = (lambda: self.set_state(state_a=self.state_a + self.props.prop_a)))
        )


class _TestComponentOuterList(ed.Component):
    """
    The rendered tree should be (with index address):
        View(               # []
            View(           # [0]
                Label,      # [0, 0]
                Label)      # [0, 1]
            View(           # [1]
                Label,      # [1, 0]
                Label)      # [1, 1]
            ...
        )
    """

    @ed.register_props
    def __init__(self):
        self.state = ["A", "B", "C"]

    def render(self):
        return ed.WindowManager()(ed.View()(
            ed.Button("Reshuffle", on_click=(lambda: self.set_state(state=["C", "D", "B", "A"]))),
            *[_TestComponentInner(text).set_key(text) for text in self.state]
        ))

if __name__ == "__main__":
    ed.App(Test()).start()
