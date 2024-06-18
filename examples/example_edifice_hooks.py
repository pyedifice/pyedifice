import asyncio
from edifice import App, Window, View, Label, TextInput, component, use_state, use_async


@component
def MyApp(self):
    text, text_set = use_state("")

    # force silent background rerenders for testing the TextInput behavior
    f, f_set = use_state(0)

    async def force():
        await asyncio.sleep(1.0)
        f_set(f + 1)

    use_async(force, f)

    with Window().render(), View(layout="column").render():
        Label("Hello world: " + text).render()
        TextInput(text, on_edit=text_set).render()
        with View(layout="row").render():
            Label("Bonjour").render()


if __name__ == "__main__":
    App(MyApp()).start()
