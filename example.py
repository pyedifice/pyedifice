import react

class Test2(react.Component):
    
    def __init__(self):
        super(Test2, self).__init__([], ["text", "vm_state"])
        self.text = "Hello"
        self.vm_state = 0

    def on_click(self):
        self.set_state(text="Hi", vm_state=1)

    def render(self):
        children = [
            react.Label(self.text).set_key("hi_text"),
            react.Button("Toggle", on_click=lambda: self.on_click()).set_key("toggle button"),
        ]
        if self.vm_state == 1:
            children = [
                react.Label(self.text).set_key("hi_text"),
                react.Label("See this").set_key("vm_state"),
                react.Button("Toggle", on_click=lambda: self.on_click()).set_key("toggle button"),
            ]
        return react.View(layout="row") (*children)

class Test(react.Component):

    def render(self):
        return react.View() (
            react.Button("Hello world"),
            Test2(),
        )

react.App(Test()).start()
