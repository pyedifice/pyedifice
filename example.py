import react

class ViewWrapper(react.Component):

    def render(self):
        return react.View(layout="row") (
            *self.children
        )

class Test2(react.Component):
    
    def __init__(self, initial_text):
        super(Test2, self).__init__(["initial_text"])
        self.text = initial_text
        self.initial_text = initial_text
        self.vm_state = 0
        self.color = "red"

    def on_click(self):
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
                react.Button("Toggle", on_click=lambda: self.on_click()).set_key("toggle button"),
            ]
        return ViewWrapper()(*children)

class Test(react.Component):

    def __init__(self):
        super(Test, self).__init__([])
        self.text = ""

    def on_change(self, text):
        self.set_state(text=text)

    def render(self):
        return react.View() (
            react.Label("Hello world: " + self.text),
            react.TextInput(self.text, on_change=lambda text: self.on_change(text)),
            Test2("Bonjour"),
        )

react.App(Test()).start()
