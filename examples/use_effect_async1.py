#
# python examples/use_effect_async1.py
#

import asyncio
from typing import cast

import edifice as ed
from edifice import App, Button, Label, VBoxView, Window, component


@component
def MainComp(self):
    show, set_show = ed.use_state(False)
    with Window():
        if show:
            with VBoxView(style={"align": "top"}):
                Button(title="Hide", on_click=lambda _: set_show(False))
                TestComp()
        else:
            with VBoxView(style={"align": "top"}):
                Button(title="Show", on_click=lambda _: set_show(True))


def result_modify(x: int, new_result: str, old_result: tuple[str, ...]) -> tuple[str, ...]:
    result_ = list(old_result)
    if len(result_) < x + 1:
        result_.extend([""] * (x + 1 - len(result_)))
    result_[x] = new_result
    return tuple(result_)


@component
def TestComp(self):
    result, result_set = ed.use_state(cast(tuple[str, ...], ()))

    async def fetch_async(z: int):
        try:
            # https://docs.python.org/3/library/asyncio-stream.html#get-http-headers
            reader, writer = await asyncio.open_connection("www.google.com", 443, ssl=True)
            query = "HEAD / HTTP/1.0\r\nHost: www.google.com\r\n\r\n"
            result_set(lambda old_result, z=z, query=query: result_modify(z, query.replace("\r\n", " "), old_result))
            writer.write(query.encode("latin-1"))
            line = await reader.readline()
            writer.close()
            await writer.wait_closed()
            result_line = line.decode("latin-1").rstrip()
            result_set(lambda old_result, z=z, result_line=result_line: result_modify(z, result_line, old_result))
        except asyncio.CancelledError:
            result_set(lambda old_result, z=z: result_modify(z, "cancelled", old_result))
            raise
        except Exception as ex:  # noqa: BLE001
            result_set(lambda old_result, z=z, ex=ex: result_modify(z, f"exception: {ex}", old_result))

    fetch, _ = ed.use_async_call(fetch_async, max_concurrent=None)

    async def fetch10_async():
        for i in range(len(result), len(result) + 10):
            await asyncio.sleep(0.1)
            fetch(i)

    fetch10, _ = ed.use_async_call(fetch10_async, max_concurrent=None)

    with VBoxView(style={"align": "top"}):
        Button(title="Fetch 1", on_click=lambda _: fetch(len(result)))
        Button(title="Fetch 10", on_click=lambda _: fetch10())
        with ed.TableGridView():
            for i, r in enumerate(result):
                with ed.TableGridRow():
                    Label(text=str(i), style={"width": "50px"})
                    Label(text=r, style={"align": "left"})


if __name__ == "__main__":
    my_app = App(MainComp())
    my_app.start()
