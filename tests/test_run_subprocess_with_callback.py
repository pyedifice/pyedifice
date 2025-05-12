from __future__ import annotations

import asyncio
import functools
import multiprocessing
import multiprocessing.connection
import multiprocessing.queues
import multiprocessing.synchronize
import os
import time
import typing
import unittest

from edifice import run_subprocess_with_callback


def callback_return(x: int) -> None:
    return


def callback_throw(x: int) -> None:
    raise ValueError("interrupt the callback")


def subprocess_return(callback: typing.Callable[[int], None]) -> str:
    callback(1)
    callback(2)
    return "done"


def subprocess_throw(callback: typing.Callable[[int], None]) -> str:
    callback(1)
    raise ValueError("interrupt the subprocess")


def callback_closure(x: int, y: int) -> None:
    return


def subprocess_closure(retval: str, callback: typing.Callable[[int], None]) -> str:
    callback(1)
    callback(2)
    return retval


def subprocess_event(
    event: multiprocessing.synchronize.Event,
    callback: typing.Callable[[bool], None],
) -> str:
    if event.is_set():
        return "early"
    callback(False)
    time.sleep(0.1)
    if event.is_set():
        return "early"
    callback(True)
    while not event.is_set():
        time.sleep(0.1)
        return "return here"  # We will return here.
    return "done"


def subprocess_queue(
    msg_queue: multiprocessing.queues.Queue[str],
    callback: typing.Callable[[int], None],
) -> str:
    while (i := msg_queue.get()) != "finish":
        callback(len(i))
    return "done"


def subprocess_pipe(
    rx: multiprocessing.connection.Connection[str, str],
    callback: typing.Callable[[int], None],
) -> str:
    while (i := rx.recv()) != "finish":
        callback(len(i))
    return "done"


def subprocess_exit(callback: typing.Callable[[str], None]) -> str:
    callback("one and done")
    os._exit(1)


def subprocess_async(callback: typing.Callable[[int], None]) -> str:
    async def work() -> str:
        callback(1)
        return "done"

    return asyncio.new_event_loop().run_until_complete(work())


def subprocess_async_cancel(callback: typing.Callable[[int], None]) -> str:
    async def work() -> str:
        raise asyncio.CancelledError
        return "done"

    return asyncio.new_event_loop().run_until_complete(work())


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
        except:
            assert False

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
        except:
            assert False

    async def test_closure(self):
        def callback_local(x: int) -> None:
            return

        retval = "closuredone"
        assert retval == await run_subprocess_with_callback(
            functools.partial(subprocess_closure, retval),
            callback_local,
        )

    async def test_subprocess_exit(self):
        try:
            await run_subprocess_with_callback(subprocess_exit, lambda _: None, daemon=True)
            assert False
        except multiprocessing.ProcessError:
            assert True
        except:
            assert False

    async def test_subprocess_async(self):
        await run_subprocess_with_callback(subprocess_async, callback_return)
        assert True

    async def test_subprocess_async_cancel(self) -> None:
        try:
            await run_subprocess_with_callback(subprocess_async_cancel, callback_return)
            assert False
        except asyncio.CancelledError:
            assert True
        except:
            assert False

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

        def local_callback(x: int) -> None:
            # This function will run in the main process event loop.
            pass

        async def send_messages() -> None:
            for i in range(1000):
                msg_queue.put(str(i))
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

        def local_callback(x: int) -> None:
            # This function will run in the main process event loop.
            pass

        y = asyncio.create_task(
            run_subprocess_with_callback(
                functools.partial(subprocess_queue, msg_queue),
                local_callback,
            )
        )
        for i in range(1000):
            msg_queue.put(str(i))
        y.cancel()

        try:
            await y
            assert False
        except asyncio.CancelledError:
            assert True
        except:
            assert False

    async def test_pipe(self) -> None:
        rx: multiprocessing.connection.Connection[str, str]
        tx: multiprocessing.connection.Connection[str, str]
        rx, tx = multiprocessing.get_context("spawn").Pipe(duplex=False)

        def local_callback(x: int) -> None:
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
        # TODO This test passes but then the unittest framework prints a strange
        # error message:
        #
        # ...Exception ignored in: <function BaseEventLoop.__del__ at 0x7fffe8e7e170>
        # ValueError: Invalid file descriptor: -1
        #
        # This behavior first appeared in v2.11.2.
        # This behavior only happens in
        #
        #     ./run_tests.py
        #
        # but not in
        #
        #     python tests/test_run_subprocess_with_callback.py
        #
        # nor in the VS Code debugger.

    async def test_pipe_cancel(self) -> None:
        rx: multiprocessing.connection.Connection[str, str]
        tx: multiprocessing.connection.Connection[str, str]
        rx, tx = multiprocessing.get_context("spawn").Pipe(duplex=False)

        def local_callback(x: int) -> None:
            # This function will run in the main process event loop.
            pass

        y = asyncio.get_event_loop().create_task(
            run_subprocess_with_callback(
                functools.partial(subprocess_pipe, rx),
                local_callback,
            )
        )
        await asyncio.sleep(0.1)
        tx.send("one")
        await asyncio.sleep(0.1)
        y.cancel()

        try:
            await y
            assert False
        except asyncio.CancelledError:
            assert True
        except:
            assert False


if __name__ == "__main__":
    unittest.main()
