import sys, os
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
import edifice
from edifice import View, Label, TextInput

class MyApp(edifice.Element):
    def __init__(self):
        super(MyApp, self).__init__()
        self.text = ""

    def _render_element(self):
        return View(layout="column")(
            Label("Hello world: " + self.text),
            TextInput(self.text, on_change=lambda text: self._set_state(text=text)),
            View(layout="row")(
                Label("Bonjour")
            )
        )

if __name__ == "__main__":
    edifice.App(edifice.Window()(MyApp())).start()
