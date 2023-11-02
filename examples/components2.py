import asyncio as asyncio
import sys
import os
import signal
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
from edifice import App, Button, View, Label, component
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

    with View():
        Button(
            title="asd + 1",
            on_click=lambda ev: x_set(x+1),
        )
        Label("asd " + str(x))
        for i in range(x):
            Label(text=str(i))

if __name__ == "__main__":
    my_app = App(Main())
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    with my_app.start_loop() as loop:
        loop.run_forever()
