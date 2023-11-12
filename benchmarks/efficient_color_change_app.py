import edifice as ed
from edifice.state import StateValue


class RecurseTree(ed.Element):

    def __init__(self, level, t):
        self._register_props({
            "level": level,
            "t": t,
        })
        super().__init__()

    def did_mount(self):
        if self.props.level == 0:
            self.props.t.subscribe(self)

    def render(self):
        if self.props.level > 0:
            layout = "row" if self.props.level % 2 == 0 else "column"
            return ed.View(layout=layout)(
               RecurseTree(level=self.props.level-1, t=self.props.t).set_key("0"),
               RecurseTree(level=self.props.level-1, t=self.props.t).set_key("1"),
            )
        else:
            t = self.props.t.value
            return ed.View(layout="row")(
                ed.View(style={"background-color": "rgba(255, 255, 0, 1)", "width": "25px", "height": "25px", "min-height": "25px", "min-width": "25px", "max-width": "25px"}).set_key("0"),
                ed.Label("%.02f" % t).set_key("1"),
            )



class MainElement(ed.Element):

    def __init__(self, level=2):
        self._register_props({
            "level": level,
        })
        super().__init__()
        self.t = StateValue(5)

    def did_mount(self):
        self.timer = ed.utilities.Timer(self.increment_time)
        self.timer.start(16)

    def will_unmount(self):
        self.timer.stop()

    def increment_time(self):
        self.t.set(self.t.value + 0.016)
        # self.set_state(t=self.t + 0.016)

    def render(self):
        return RecurseTree(level=7, t=self.t)

if __name__ == "__main__":
    ed.App(MainElement()).start()
