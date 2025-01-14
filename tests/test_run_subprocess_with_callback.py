from __future__ import annotations

import asyncio
import functools
import multiprocessing
import multiprocessing.connection
import multiprocessing.queues
import multiprocessing.synchronize
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
    event: multiprocessing.synchronize.Event,
    callback: typing.Callable[[bool], None],
) -> str:
    if event.is_set():
        return "early"
    callback(False)
    await asyncio.sleep(0.1)
    if event.is_set():
        return "early"
    callback(True)
    while not event.is_set():
        await asyncio.sleep(0.1)
        return "return here" # We will return here.
    return "done"

async def subprocess_queue(
    msg_queue: multiprocessing.queues.Queue[str],
    callback: typing.Callable[[int], None],
) -> str:
    while (i := msg_queue.get()) != "finish":
        callback(len(i))
    return "done"

async def subprocess_pipe(
    rx: multiprocessing.connection.Connection[str, str],
    callback: typing.Callable[[int], None],
) -> str:
    while (i := rx.recv()) != "finish":
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
        # For testing with Python 3.11:
        # > except BaseException as e:
        # >     print(f"Exception: {type(e)} ")
        # >     print(str(e))
        # >     print(e.__notes__)
        # >     assert True

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
        event: multiprocessing.synchronize.Event = multiprocessing.get_context("spawn").Event()

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
        msg_queue: multiprocessing.queues.Queue[str] = multiprocessing.get_context("spawn").Queue()

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
        msg_queue: multiprocessing.queues.Queue[str] = multiprocessing.get_context("spawn").Queue()

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

    async def test_pipe(self) -> None:
        rx: multiprocessing.connection.Connection[str, str]
        tx: multiprocessing.connection.Connection[str, str]
        rx, tx = multiprocessing.get_context("spawn").Pipe()

        def local_callback(x:int) -> None:
            # This function will run in the main process event loop.
            pass

        async def send_messages() -> None:
            tx.send("one")
            tx.send("three")
            tx.send("finish")

        y, _ = await asyncio.gather(
            run_subprocess_with_callback(
                functools.partial(subprocess_pipe, rx),
                local_callback,
            ),
            send_messages(),
        )

        assert y == "done"

    async def test_pipe_cancel(self) -> None:
        rx: multiprocessing.connection.Connection[str, str]
        tx: multiprocessing.connection.Connection[str, str]
        rx, tx = multiprocessing.get_context("spawn").Pipe()

        def local_callback(x:int) -> None:
            # This function will run in the main process event loop.
            pass

        y = asyncio.create_task(run_subprocess_with_callback(
            functools.partial(subprocess_pipe, rx),
            local_callback,
        ))
        await asyncio.sleep(0.1)
        tx.send("one")
        await asyncio.sleep(0.1)
        y.cancel()

        try:
            await y
            assert False
        except:
            assert True

if __name__ == "__main__":
    unittest.main()
