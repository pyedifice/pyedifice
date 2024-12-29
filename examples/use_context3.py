#
# python examples/use_context3.py
#

import edifice as ed


@ed.component
def Display(self):
    context_select, context_select_set = ed.use_state(0)
    # This is kind of stupid, no-one should ever dynamically
    # select the context_key, but we do it here to show that it's possible.
    text_a, text_a_set = ed.use_context(str(context_select), str)
    with ed.VBoxView(style={"padding": 10}):
        ed.Dropdown(
            selection=context_select,
            options=("Context A", "Context B"),
            on_select=context_select_set,
        )
        ed.TextInput(text=text_a, on_change=text_a_set)


@ed.component
def Main(self):
    show_all, set_show_all = ed.use_state(False)

    with ed.Window(_size_open=(800, 400)):
        with ed.VBoxView(style={"align": "top"}):
            ed.CheckBox(text="Show provide_context", checked=show_all, on_change=set_show_all)
            if show_all:
                ProviderComponent()


@ed.component
def ProviderComponent(self):
    show_a, set_show_a = ed.use_state(False)
    text_a, set_text_a = ed.provide_context("0", "Hello")
    text_b, set_text_b = ed.provide_context("1", "World")
    display_count, set_display_count = ed.use_state(10)

    with ed.VBoxView(style={"align": "top"}):
        with ed.HBoxView():
            ed.Label(text="Context A")
            ed.TextInput(text=text_a, on_change=set_text_a)
            ed.Label(text="Context B")
            ed.TextInput(text=text_b, on_change=set_text_b)
        with ed.HBoxView():
            ed.CheckBox(text="Show use_context", checked=show_a, on_change=set_show_a)
            ed.SpinInput(value=display_count, on_change=set_display_count)
        if show_a:
            with ed.FlowView():
                for _ in range(display_count):
                    Display()


if __name__ == "__main__":
    ed.App(Main()).start()
