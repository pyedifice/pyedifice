#
# python examples/use_context1.py
#

from edifice import App, Button, Label, VBoxView, Window, component, provide_context, use_context


@component
def Display(self):
    show, _ = use_context("show", bool)
    with VBoxView():
        if show:
            TestComp()


@component
def UseContext1(self):
    show, set_show = provide_context("show", False)
    with Window():
        if show:
            with VBoxView():
                Button(title="Hide", on_click=lambda _ev: set_show(False))
                Display()
        else:
            with VBoxView():
                Button(title="Show", on_click=lambda _ev: set_show(True))


@component
def TestComp(self):
    with VBoxView(style={"align": "top"}):
        Label(text=str(id(self)))


if __name__ == "__main__":
    App(UseContext1()).start()
