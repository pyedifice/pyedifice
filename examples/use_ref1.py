#
# python examples/use_ref1.py
#

import asyncio as asyncio
import sys, os
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
from edifice import App, View, Label, Button, component, use_ref, use_effect

@component
def MyComp(self):
    ref = use_ref()

    def did_render():
        element = ref()
        assert isinstance(element, Label)
        element.underlying.setText("After")
        return lambda:None

    use_effect(did_render, ref)

    with View():
        Label("Before").register_ref(ref)

if __name__ == "__main__":
    my_app = App(MyComp())
    with my_app.start_loop() as loop:
        loop.run_forever()
