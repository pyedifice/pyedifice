import edifice
from edifice import View, Label, TextInput

class App(edifice.Component):
    def __init__(self):
        super(App, self).__init__()
        self.text = ""

    def render(self):
        return View(layout="column")(
            Label("Hello world: " + self.text),
            TextInput(self.text, on_change=lambda text: self.set_state(text=text)),
            View(layout="row")(
                Label("Bonjour")
            )
        )

if __name__ == "__main__":
    edifice.App(App()).start()
