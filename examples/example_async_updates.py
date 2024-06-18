#
# python examples/use_effect_async1.py
#

import asyncio as asyncio
import time
from typing import cast
from edifice import App, Window, View, Label, Button, ButtonView, component
from edifice.hooks import use_state, use_async
import functools
import queue
import threading
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def spawn_worker(
    target: Callable[P, R],
    poll_result_interval: float = 0.1,
    timeout: float = 5.0,
) -> Callable[P, Awaitable[R]]:
    """
    Spawn a worker thread that runs the `target` function till completion.

    Args:
        target: The target function to run.
        poll_result_interval: How often to check for the result of the target function.

    Returns:
        An awaitable that takes the same parameters as the target function.

    Creating a worker-thread using `asyncio.to_thread` doesn't create the
    thread as a daemon thread blocks the main thread from terminating when
    the application is closed. Thus, we explicitly create a daemon thread
    that won't block the main thread to exit and use a threadsafe queue
    to pass the results back to the main thread.
    """

    async def inner(
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        result: queue.Queue[R] = queue.Queue()
        worker_target = functools.partial(target, *args, **kwargs)

        def runner() -> None:
            result.put(worker_target())

        worker = threading.Thread(target=runner, daemon=True)
        worker.start()
        while worker.is_alive():
            try:
                return result.get_nowait()
            except queue.Empty:  # noqa: PERF203
                await asyncio.sleep(poll_result_interval)
        try:
            return result.get(timeout=timeout)
        except queue.Empty:
            raise RuntimeError(f"Worker {id(worker)} died") from None

    return inner


@component
def MainComp(self):
    show, set_show = use_state(False)
    with Window():
        if show:
            with View(style={"align": "top"}):
                Button(title="Hide", on_click=lambda ev: set_show(False))
                TestComp()
        else:
            with View(style={"align": "top"}):
                Button(title="Show", on_click=lambda ev: set_show(True))


@component
def AbsoluteButton(self, i: int, text: str) -> None:
    with ButtonView(style={"left": i * 50, "top": 0}):
        Label(text)


def example_worker(i: int, callback: Callable[[list[str]], None]):
    time.sleep(0.5)
    callback([str(i)])


@component
def TestComp(self):
    print("TestComp instance " + str(id(self)))

    x, x_setter = use_state(cast(list[str], []))

    async def fetch():
        print(f"async {x}")
        loop = asyncio.get_running_loop()
        worker = spawn_worker(example_worker)

        def on_result(xs: list[str]) -> None:
            x_setter(lambda old: xs + old)

        def on_result_thread(xs: list[str]) -> None:
            loop.call_soon_threadsafe(on_result, xs)

        try:
            await worker(len(x), on_result_thread)
        except Exception as ex:
            print(f"async {x} cancelled")
            raise ex

    print(f"use_async(fetch, {x})")
    use_async(fetch, x)

    with View(style={"align": "top"}):
        with ButtonView(on_trigger=lambda _: x_setter(lambda old: [f"manual {len(old)}"] + old)):
            Label("Prepend text")
        with View(layout="none", style={"width": 800, "height": 900}):
            for i, text in enumerate(x):
                AbsoluteButton(i, text)


if __name__ == "__main__":
    my_app = App(MainComp())
    my_app.start()
