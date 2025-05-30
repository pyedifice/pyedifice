#
# python examples/use_context2.py
#

from edifice import App, Button, HBoxView, Label, VBoxView, Window, component, provide_context, use_context


@component
def Display(self):
    show_a, _ = use_context("show_a", bool)
    show_c, set_show_c = use_context("show_c", bool)
    with VBoxView():
        if show_a:
            TestComp()
            if show_c:
                Button(title="Hide C", on_click=lambda _ev: set_show_c(False))
            else:
                Button(title="Show C", on_click=lambda _ev: set_show_c(True))


@component
def Main(self):
    show_a, set_show_a = provide_context("show_a", False)
    show_b, set_show_b = provide_context("show_b", False)
    show_c, _ = provide_context("show_c", True)
    with Window(_size_open=(400, 300)):
        with VBoxView():
            with HBoxView():
                if show_a:
                    with VBoxView():
                        Button(title="Hide A", on_click=lambda _ev: set_show_a(False))
                        Display()
                else:
                    with VBoxView():
                        Button(title="Show A", on_click=lambda _ev: set_show_a(True))
                if show_b:
                    with VBoxView():
                        Button(title="Hide B ", on_click=lambda _ev: set_show_b(False))
                        Display()
                else:
                    with VBoxView():
                        Button(title="Show B", on_click=lambda _ev: set_show_b(True))
            if show_c:
                Label(text="Showing C")


@component
def TestComp(self):
    with VBoxView(style={"align": "top"}):
        Label(text=str(id(self)))


if __name__ == "__main__":
    App(Main()).start()
