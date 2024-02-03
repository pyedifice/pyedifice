#
# python examples/async.py
#

import os
import sys
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))

import asyncio
from concurrent.futures import ThreadPoolExecutor
import edifice as ed

@ed.component
def ComponentWithAsync(self):
    """
    Component with an async Hook so we can test unmounting.
    """

    x, set_x = ed.use_state("async incomplete")

    async def set_label():
        await asyncio.sleep(1)
        set_x("async complete")

    ed.use_async(set_label, ())

    ed.Label(x)

@ed.component
def Main(self):

    a, set_a = ed.use_state(0)
    b, set_b = ed.use_state(0)

    async def _on_change1(v:int):
        """
        Test regular async event handlers.
        """
        set_a(v)
        await asyncio.sleep(1)
        set_b(v)


    c, set_c = ed.use_state(0)

    async def async_callback1(v:int):
        set_c(v)

    callback1 = ed.use_async_call(async_callback1)

    async def _on_change2(v:int):
        """
        Test async callbacks from another thread.
        """
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            await loop.run_in_executor(pool, lambda: callback1(v))


    d, set_d = ed.use_state(0)
    e, set_e = ed.use_state(0)

    async def _on_change3():
        """
        Test use_async
        """
        set_e(d)
    ed.use_async(_on_change3, d)

    checked, set_checked = ed.use_state(False)

    with ed.View():
        with ed.View(
            style={
                "margin-top": 20,
                "margin-bottom": 20,
                "border-top-width": "1px",
                "border-top-style": "solid",
                "border-top-color": "black",
            },
        ):
            ed.Label(str(a))
            ed.Label(str(b))
            ed.Slider(a, min_value=0, max_value=100, on_change=_on_change1)

        with ed.View(
            style={
                "margin-top": 20,
                "margin-bottom": 20,
                "border-top-width": "1px",
                "border-top-style": "solid",
                "border-top-color": "black",
            },
        ):
            ed.Label(str(c))
            ed.Slider(c, min_value=0, max_value=100, on_change=_on_change2)

        with ed.View(
            style={
                "margin-top": 20,
                "margin-bottom": 20,
                "border-top-width": "1px",
                "border-top-style": "solid",
                "border-top-color": "black",
            },
        ):
            ed.Label(str(e))
            ed.Slider(d, min_value=0, max_value=100, on_change=set_d)

        with ed.View(
            style={
                "margin-top": 20,
                "margin-bottom": 20,
                "border-top-width": "1px",
                "border-top-style": "solid",
                "border-top-color": "black",
            },
        ):
            with ed.View(layout="row"):
                ed.CheckBox(
                    checked=checked,
                    on_change=set_checked,
                )
                if checked:
                    ComponentWithAsync()


if __name__ == "__main__":
    ed.App(ed.Window()(Main())).start()
