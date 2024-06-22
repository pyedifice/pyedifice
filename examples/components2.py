import asyncio as asyncio
from edifice import App, Window, Button, ButtonView, View, Label, Icon, component, TreeBuilder
from edifice.hooks import use_state, use_effect


@component
def Main(self):
    x, x_set = use_state(0)

    def setup_print():
        print("print setup")

        def cleanup_print():
            print("print cleanup")

        return cleanup_print

    use_effect(setup_print, x)

    put = TreeBuilder()
    with put(Window()) as root:
        with put(View()):
            with put(View(style={"margin": 30})):
                with put(
                    ButtonView(
                        layout="row",
                        on_click=lambda event: None,
                        style={"margin": 10},
                    )
                ):
                    put(Icon(name="share", style={"margin": 10}))
                    put(Label(text="<i>Share the Content<i>"))
            put(
                Button(
                    title="asd + 1",
                    on_click=lambda ev: x_set(x + 1),
                )
            )
            put(Label("asd " + str(x)))
            for i in range(x):
                put(Label(text=str(i)))
        return root


if __name__ == "__main__":
    my_app = App(Main())
    my_app.start()
