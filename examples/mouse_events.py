import edifice as ed

class MouseEvents(ed.Component):

    @ed.register_props
    def __init__(self):
        self.pos = (0, 0)
        self.entered = False
        self.pressed = False

    def render(self):
        return ed.View()(
            ed.View(style={"height": 200, "width": 200, "background-color": "red"},
                    on_mouse_enter=lambda e: self.set_state(entered=True),
                    on_mouse_leave=lambda e: self.set_state(entered=False),
                    on_mouse_down=lambda e: self.set_state(pressed=True),
                    on_mouse_up=lambda e: self.set_state(pressed=False),
                    on_mouse_move=lambda e: self.set_state(pos=(e.x(), e.y()))
                   )(
                       ed.Label("TESTING"),
           ),
            ed.Label("Entered" if self.entered else ""),
            ed.Label("Pressed" if self.pressed else ""),
            ed.Label(self.pos),
        )

