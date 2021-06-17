import edifice as ed

class KeyboardEvents(ed.Component):

    @ed.register_props
    def __init__(self):
        self.text = ""

    def key_down(self, e):
        with self.render_changes():
            self.text += chr(e.key())

    def render(self):
        return ed.View(on_key_down=self.key_down)(
            ed.Label(self.text)
        )

