import react

class ViewWrapper(react.Component):

    def __init__(self):
        super(ViewWrapper, self).__init__(["children"], [])

    def render(self):
        return react.View(layout="row") (
            *self.children
        )

class Test2(react.Component):
    
    def __init__(self, initial_text):
        super(Test2, self).__init__(["initial_text"], ["text", "vm_state"])
        self.text = initial_text
        self.initial_text = initial_text
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
        return ViewWrapper()(*children)

class Test(react.Component):

    def render(self):
        return react.View() (
            react.Button("Hello world"),
            Test2("Bonjour"),
        )

react.App(Test()).start()
