import asyncio as asyncio
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

    with Window().render():
        with View().render():
            with View(style={"margin": 30}).render():
                with ButtonView(
                    layout="row",
                    on_click=lambda event: None,
                    style={"margin": 10},
                ).render():
                    Icon(name="share", style={"margin": 10}).render()
                    Label(text="<i>Share the Content<i>").render()
            Button(
                title="asd + 1",
                on_click=lambda ev: x_set(x + 1),
            ).render()
            Label("asd " + str(x)).render()
            for i in range(x):
                Label(text=str(i)).render()


if __name__ == "__main__":
    my_app = App(Main())
    my_app.start()
