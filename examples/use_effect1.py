#
# python examples/use_effect1.py
#

from edifice import App, Button, Label, VBoxView, Window, component
from edifice.hooks import use_effect, use_state


@component
def MainComp(self):
    show, set_show = use_state(False)
    with Window(on_close=lambda _ev: print("Window will close")):
        if show:
            with VBoxView():
                Button(title="Hide", on_click=lambda _ev: set_show(False))
                TestComp()
        else:
            with VBoxView():
                Button(title="Show", on_click=lambda _ev: set_show(True))


@component
def TestComp(self):
    print("TestComp instance " + str(id(self)))

    x, x_setter = use_state(0)

    def setup():
        print("effect setup")

        def cleanup():
            print("effect cleanup")
            pass

        return cleanup

    use_effect(setup, x)

    def setup_always():
        print("effect setup always")

        def cleanup():
            print("effect cleanup always")
            pass

        return cleanup

    use_effect(setup_always, None)

    with VBoxView(style={"align": "top"}):
        Label(text="Label text")
        Button(title="State " + str(x), on_click=lambda _ev: x_setter(x + 1))
        Button(title="State Unchanged", on_click=lambda _ev: x_setter(lambda y: y))


if __name__ == "__main__":
    my_app = App(MainComp())
    my_app.start()
