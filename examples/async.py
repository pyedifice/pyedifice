#
# python examples/async.py
#

import os, sys
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
import asyncio
import edifice as ed


@ed.component
def AsyncElement(self):

    a, set_a = ed.use_state(0.0)
    b, set_b = ed.use_state(0)

    async def _on_change(text):
        set_a(float(text))
        await asyncio.sleep(4)
        set_a(lambda x: x/2)

    with ed.View():
        ed.Label(str(a))
        ed.Label(str(b))
        ed.Slider(a, min_value=0, max_value=1, on_change=_on_change)
        ed.Button("Update b", on_click=lambda e: set_b(lambda x: x+1))

if __name__ == "__main__":
    ed.App(ed.Window()(AsyncElement())).start()
