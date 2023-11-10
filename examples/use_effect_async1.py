#
# python examples/use_effect_async1.py
#

import asyncio as asyncio
import sys, os
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
from edifice import App, Element, View, Label, Button, component
from edifice.hooks import use_state, use_async

@component
def MainComp(self):
    show, set_show = use_state(False)
    if show:
        with View(
            style={
                "align":"top"
            }
        ):
            Button(
                title="Hide",
                on_click=lambda ev: set_show(False)
            )
            TestComp()
    else:
        with View(
            style={
                "align":"top"
            }
        ):
            Button(
                title="Show",
                on_click=lambda ev: set_show(True)
            )

@component
def TestComp(self):

    print("TestComp instance " + str(id(self)))

    x, x_setter = use_state(0)

    result, result_set = use_state("")

    async def fetch():
        print(f"async fetch {x}")
        try:
            # https://docs.python.org/3/library/asyncio-stream.html#get-http-headers
            reader,writer = await asyncio.open_connection("www.google.com", 443, ssl=True)
            query = (
                "HEAD / HTTP/1.0\r\n"
                "Host: www.google.com\r\n"
                "\r\n"
            )
            writer.write(query.encode('latin-1'))
            line = await reader.readline()
            writer.close()
            await writer.wait_closed()
            result_line = line.decode('latin-1').rstrip()
            print(result)
            result_set(result_line)
            print (f"async fetch {x} finished")
        except Exception as ex:
            print (f"async fetch {x} cancelled")
            raise ex

    print(f"use_async(fetch, {x})")
    use_async(fetch, x)

    def fetch10(event):
        for i in range(10):
            asyncio.get_running_loop().call_later(0.1 * i, x_setter, (lambda y: y+1))

    with View(
        style={
            "align":"top"
        }
    ):
        Label(text=result)
        Button(
            title="State " + str(x),
            on_click=lambda ev: x_setter(lambda y: y+1)
        )
        Button(
            title="State + 10",
            on_click=fetch10,
        )

if __name__ == "__main__":
    my_app = App(MainComp())
    with my_app.start_loop() as loop:
        loop.run_forever()
