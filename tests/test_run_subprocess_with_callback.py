import asyncio
import functools
import multiprocessing
import multiprocessing.synchronize
import threading
import typing
import unittest

from edifice import run_subprocess_with_callback


def callback_return(x:int) -> None:
    return

def callback_throw(x:int) -> None:
    raise ValueError("interrupt the callback")

async def subprocess_return(callback: typing.Callable[[int], None]) -> str:
    callback(1)
    callback(2)
    return "done"

async def subprocess_throw(callback: typing.Callable[[int], None]) -> str:
    callback(1)
    raise ValueError("interrupt the subprocess")

def callback_closure(x:int, y:int) -> None:
    return

async def subprocess_closure(retval:str, callback: typing.Callable[[int], None]) -> str:
    callback(1)
    callback(2)
    return retval

async def subprocess_event(
    event: threading.Event,
    callback: typing.Callable[[int], None],
) -> str:
    if event.is_set():
        return "early"
    callback(10)
    await asyncio.sleep(0.1)
    if event.is_set():
        return "early"
    callback(20)
    await asyncio.sleep(0.1)
    if event.is_set():
        return "return here" # We will return here.
    callback(30)
    return "done"

class IntegrationTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_success(self):
        assert "done" == await run_subprocess_with_callback(subprocess_return, callback_return)

    async def test_cancel(self):
        y_task = asyncio.create_task(run_subprocess_with_callback(subprocess_return, callback_return))
        async def canceller():
            await asyncio.sleep(0.05)
            y_task.cancel()
        await asyncio.create_task(canceller())
        try:
            await y_task
            assert False
        except asyncio.CancelledError:
            assert True

    async def test_subprocess_throw(self):
        y_task = asyncio.create_task(run_subprocess_with_callback(subprocess_throw, callback_return))
        try:
            await y_task
            assert False
        except ValueError:
            assert True

    async def test_callback_throw(self):
        y_task = asyncio.create_task(run_subprocess_with_callback(subprocess_return, callback_throw))
        try:
            await y_task
            assert False
        except ValueError:
            assert True

    async def test_closure(self):
        def callback_local(x:int) -> None:
            return
        retval = "closuredone"
        assert retval == await run_subprocess_with_callback(
            functools.partial(subprocess_closure, retval),
            callback_local,
        )

    async def test_event(self) -> None:
        with multiprocessing.Manager() as manager:
            event = manager.Event()

            def local_callback(x:int) -> None:
                # This function will run in the main process event loop.
                if x > 10:
                    event.set()

            y = await run_subprocess_with_callback(
                functools.partial(subprocess_event, event),
                local_callback,
            )
            assert y == "return here"

if __name__ == "__main__":
    unittest.main()
