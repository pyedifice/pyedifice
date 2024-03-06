import sys, os
# We need this sys.path line for running this example, especially in VSCode debugger.
import asyncio
sys.path.insert(0, os.path.join(sys.path[0], '..'))
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

    with View(layout="column"):
        Label("Hello world: " + text)
        TextInput(text, on_change=text_set)
        with View(layout="row"):
            Label("Bonjour")

if __name__ == "__main__":
    App(Window()(MyApp())).start()
