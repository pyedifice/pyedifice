from edifice import App, Button, ButtonView, Icon, Label, VBoxView, Window, component
from edifice.hooks import use_effect, use_state


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
        with VBoxView():
            with VBoxView(style={"padding": 30}):
                with ButtonView(
                    on_click=lambda _event: None,
                    style={"padding": 10},
                ):
                    Icon(name="share", style={"margin": 10})
                    Label(text="<i>Share the Content<i>")
            Button(
                title="asd + 1",
                on_click=lambda _ev: x_set(x + 1),
            )
            Label("asd " + str(x))
            for i in range(x):
                Label(text=str(i))


if __name__ == "__main__":
    my_app = App(Main())
    my_app.start()
