#
# python examples/use_effect_async1.py
#

import asyncio as asyncio
import sys, os
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
from edifice import App, Element, View, Label, Button
from edifice.hooks import use_state, use_async

class MainComp(Element):
    def __init__(self):
        super().__init__()

    def render(self):
        show, set_show = use_state(False)
        if show:
            return View(
                style={
                    "align":"top"
                }
            )(
                Button(
                    title="Hide",
                    on_click=lambda ev: set_show(False)
                ),
                TestComp()
            )
        else:
            return View(
                style={
                    "align":"top"
                }
            )(
                Button(
                    title="Show",
                    on_click=lambda ev: set_show(True)
                )
            )
class TestComp(Element):
    def __init__(self):
        super().__init__()
        self.count = 0


    def render(self):

        print("TestComp instance " + str(id(self)))

        x, x_setter = use_state(0)

        result, result_set = use_state("")

        async def fetch():
            print("async effect")
            # https://docs.python.org/3/library/asyncio-stream.html#get-http-headers
            reader,writer = await asyncio.open_connection("www.google.com", 443, ssl=True)
            query_incomplete = (
                f"HEAD / HTTP/1.0\r\n"
            )
            query = (
                f"HEAD / HTTP/1.0\r\n"
                f"Host: www.google.com\r\n"
                f"\r\n"
            )
            writer.write(query.encode('latin-1'))
            line = await reader.readline()
            writer.close()
            await writer.wait_closed()
            result_line = line.decode('latin-1').rstrip()
            print(result)
            result_set(result_line)

        use_async(fetch, x)

        def fetch10(event):
            for i in range(x, x+10):
                x_setter(i+1)

        return View(
            style={
                "align":"top"
            }
        )(
            Label(text=result),
            Button(
                title="State " + str(x),
                on_click=lambda ev: x_setter(x+1)
            ),
            Button(
                title="State + 10",
                on_click=fetch10,
            )
        )

if __name__ == "__main__":
    my_app = App(MainComp())
    with my_app.start_loop() as loop:
        loop.run_forever()
