import asyncio as asyncio
import signal
from edifice import App, Window, Button, ButtonView, View, Label, Icon, component
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

    with Window():
        with View():
            with View(style={"margin": 30}):
                with ButtonView(
                    layout="row",
                    on_click=lambda event: None,
                    style={"margin": 10},
                ):
                    Icon(name="share", style={"margin": 10})
                    Label(text="<i>Share the Content<i>")
            Button(
                title="asd + 1",
                on_click=lambda ev: x_set(x + 1),
            )
            Label("asd " + str(x))
            for i in range(x):
                Label(text=str(i))


if __name__ == "__main__":
    my_app = App(Main())
    my_app.start()
