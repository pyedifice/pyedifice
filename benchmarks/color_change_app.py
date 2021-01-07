import edifice as ed
import math
import numpy as np


class RecurseTree(ed.Component):

    @ed.register_props
    def __init__(self, level, t):
        pass

    def render(self):
        color = np.array([255, 255, 0])
        color = color * self.props.t
        if self.props.level > 0:
            layout = "row" if self.props.level % 2 == 0 else "column"
            return ed.View(layout=layout)(
               RecurseTree(level=self.props.level-1, t=self.props.t).set_key("0"),
               RecurseTree(level=self.props.level-1, t=self.props.t).set_key("1"),
            )
        else:
            return ed.View(layout="row")(
                ed.View(style={"background-color": "rgba(255, 255, 0, 1)", "width": "25px", "height": "25px", "min-height": "25px", "min-width": "25px", "max-width": "25px"}).set_key("0"),
                ed.Label("%.02f" % self.props.t).set_key("1"),
            )



class MainComponent(ed.Component):

    @ed.register_props
    def __init__(self, level=2):
        self.t = 5

    def did_mount(self):
        print("Mount")
        print("HI")
        self.timer = ed.Timer(self.increment_time)
        print(id(self))
        self.timer.start(16)

    def will_unmount(self):
        print("Unmount")
        self.timer.stop()

    def increment_time(self):
        self.set_state(t=self.t + 0.016)

    def render(self):
        return RecurseTree(level=6, t=self.t)
