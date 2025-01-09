import asyncio
import functools
import multiprocessing
import multiprocessing.synchronize
import queue
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
    callback: typing.Callable[[bool], None],
) -> str:
    if event.is_set():
        return "early"
    callback(False)
    await asyncio.sleep(0.1)
    if event.is_set():
        return "early"
    callback(True)
    await asyncio.sleep(0.5)
    if event.is_set():
        return "return here" # We will return here.
    return "done"

async def subprocess_queue(
    queue: queue.Queue[str],
    callback: typing.Callable[[int], None],
) -> str:
    while (i := queue.get()) != "finish":
        callback(len(i))
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
        try:
            await run_subprocess_with_callback(subprocess_throw, callback_return)
            assert False
        except ValueError:
            assert True

    async def test_callback_throw(self):
        try:
            await run_subprocess_with_callback(subprocess_return, callback_throw)
            assert True
        except ValueError:
            assert False

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
            event: threading.Event = manager.Event()

            def local_callback(signal: bool) -> None:
                # This function will run in the main process event loop.
                if signal:
                    event.set()

            y = await run_subprocess_with_callback(
                functools.partial(subprocess_event, event),
                local_callback,
            )
            assert y == "return here"

    async def test_queue(self) -> None:
        with multiprocessing.Manager() as manager:
            msg_queue: queue.Queue[str] = manager.Queue()

            def local_callback(x:int) -> None:
                # This function will run in the main process event loop.
                pass

            async def send_messages() -> None:
                msg_queue.put("one")
                msg_queue.put("three")
                msg_queue.put("finish")

            y, _ = await asyncio.gather(
                run_subprocess_with_callback(
                    functools.partial(subprocess_queue, msg_queue),
                    local_callback,
                ),
                send_messages(),
            )

            assert y == "done"

    async def test_queue_cancel(self) -> None:
        with multiprocessing.Manager() as manager:
            msg_queue: queue.Queue[str] = manager.Queue()

            def local_callback(x:int) -> None:
                # This function will run in the main process event loop.
                pass

            y = asyncio.create_task(run_subprocess_with_callback(
                functools.partial(subprocess_queue, msg_queue),
                local_callback,
            ))
            await asyncio.sleep(0.1)
            msg_queue.put("one")
            await asyncio.sleep(0.1)
            y.cancel()

            try:
                await y
                assert False
            except:
                assert True

if __name__ == "__main__":
    unittest.main()
