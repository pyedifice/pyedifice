import asyncio
import edifice as ed


class Component(ed.Component):

    def __init__(self):
        super().__init__()
        self.a = 0
        self.b = 0

    async def _on_change(self, text):
        self.set_state(a=text)
        await asyncio.sleep(4)
        self.set_state(a = self.a/2)

    def render(self):
        return ed.View()(
            ed.Label(self.a),
            ed.Label(self.b),
            ed.Slider(self.a, min_value=0, max_value=1, on_change=self._on_change),
            ed.Button("Update b", on_click=lambda e: self.set_state(b=self.b+1)),
        )
