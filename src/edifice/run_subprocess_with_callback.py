# MIT License
#
# Copyright 2021 David Ding
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# Edifice run_subprocess_with_callback 2025 by James D. Brock
#
# This run_subprocess_with_callback module file depends only on the Python
# standard library so it can copied and pasted into any project without
# modification.


from __future__ import annotations

import asyncio
import dataclasses
import multiprocessing
import multiprocessing.process
import multiprocessing.queues
import queue
import traceback
import typing

if typing.TYPE_CHECKING:
    from multiprocessing.context import SpawnContext

_T_subprocess = typing.TypeVar("_T_subprocess")
_P_callback = typing.ParamSpec("_P_callback")


@dataclasses.dataclass
class _EndProcess:
    """
    The result returned by the subprocess
    """

    result: typing.Any


@dataclasses.dataclass
class _ExceptionWrapper:
    """
    Wrap an exception raised in the subprocess
    """

    ex: BaseException
    ex_string: list[str]


def _run_subprocess(
    subprocess: typing.Callable[[typing.Callable[_P_callback, None]], typing.Awaitable[_T_subprocess]],
    callback_send: multiprocessing.queues.Queue,
) -> None:
    subloop = asyncio.new_event_loop()

    async def work() -> None:
        def _run_callback(*args: _P_callback.args, **kwargs: _P_callback.kwargs) -> None:
            callback_send.put((args, kwargs))

        try:
            r = await subprocess(_run_callback)

            # It would be nice if the subprocess could be cancelled
            # by .cancel() so it it could have a chance to handle CancelledError
            # and clean up before it gets .terminate()ed.
            #
            # But we have to ask: what if the subprocess is blocked?
            # Making blocking I/O calls in a subprocess should be supported
            # and encouranged. That's the whole point of using a subprocess.
            #
            # So I think the best and simplest thing to do is to terminate
            # on cancellation.

        except BaseException as e:  # noqa: BLE001
            callback_send.put(_ExceptionWrapper(e, traceback.format_exception(e)))
        else:
            callback_send.put(_EndProcess(r))

    return subloop.run_until_complete(work())
    # https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Queue.join_thread
    # > “By default if a process is not the creator of the queue then on
    # > exit it will attempt to join the queue's background thread.”
    #
    # https://docs.python.org/3/library/multiprocessing.html#pipes-and-queues
    # > “if a child process has put items on a queue (and it has not used
    # > JoinableQueue.cancel_join_thread), then that process will not
    # > terminate until all buffered items have been flushed to the pipe.”


async def run_subprocess_with_callback(
    subprocess: typing.Callable[[typing.Callable[_P_callback, None]], typing.Awaitable[_T_subprocess]],
    callback: typing.Callable[_P_callback, None],
) -> _T_subprocess:
    """
    Run an
    async :code:`subprocess` in a
    `Process <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process>`_
    and return the result.

    The advantage of :func:`run_subprocess_with_callback` is that it behaves
    well and cleans up properly in the event of exceptions and
    `cancellation <https://docs.python.org/3/library/asyncio-task.html#task-cancellation>`_.
    This function is useful for a long-running parallel worker
    subprocess for which we want to report progress back to the main GUI event loop.
    Like *pytorch* stuff.

    Args:
        subprocess:
            The async function to run in a
            `Process <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process>`_.
            The :code:`subprocess` function will run in a sub-process in a new event loop.
            This :code:`subprocess` function takes a single argument: a function with the same type
            as the :code:`callback` function.
            The :code:`subprocess` function must be picklable.
        callback:
            The :code:`callback` function to pass to the :code:`subprocess` when it starts.
            This function will run in the main process event loop.
            All of the arguments to the :code:`callback` function must be picklable.

    The :code:`subprocess` will be started when :func:`run_subprocess_with_callback`
    is entered, and the :code:`subprocess` is guaranteed to be terminated when
    :func:`run_subprocess_with_callback` completes.

    The :code:`subprocess` will be started with the
    `"spawn" start method <https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods>`_,
    so it will not inherit any file handles from the calling process.

    While the :code:`subprocess` is running, it may call the supplied :code:`callback` function.
    The :code:`callback` function will run in the main event loop of the calling process.

    If this async :func:`run_subprocess_with_callback` function is
    `cancelled <https://docs.python.org/3/library/asyncio-task.html#task-cancellation>`_,
    the :code:`subprocess` will be terminated by calling
    `Process.terminate() <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process.terminate>`_.
    Termination of the :code:`subprocess` will occur even if
    the :code:`subprocess` is blocked. Note that
    :code:`CancelledError` will not be raised in the :code:`subprocess`,
    instead the :code:`subprocess` will be terminated immediately. If you
    want to perform sudden cleanup and halt of the :code:`subprocess` then
    send it a message as in the below “Example of Queue messaging.”

    Exceptions raised in the :code:`subprocess` will be re-raised from :func:`run_subprocess_with_callback`.
    Because the Exception must be pickled back to the main process, it will
    lose its `traceback <https://docs.python.org/3/reference/datamodel.html#traceback-objects>`_.
    In Python ≥3.11, the traceback string from the :code:`subprocess` stack will be added
    to the Exception `__notes__ <https://docs.python.org/3/library/exceptions.html#BaseException.__notes__>`_.

    Exceptions raised in the :code:`callback` will be suppressed.

    The :code:`subprocess` is started as a
    `daemon <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process.daemon>`_
    so it will be terminated if it is still running when the main process exits.

    .. code-block:: python
        :caption: Example

        async def my_subprocess(callback: Callable[[int], None]) -> str:
            # This function will run in a subprocess in a new event loop.
            callback(1)
            await asyncio.sleep(1)
            callback(2)
            await asyncio.sleep(1)
            callback(3)
            return "done"

        def my_callback(x:int) -> None:
            # This function will run in the main process event loop.
            print(f"callback {x}")

        async def main() -> None:
            y = await run_subprocess_with_callback(my_subprocess, my_callback)

            # If this main() function is cancelled while awaiting the
            # subprocess then the subprocess will be terminated.

            print(f"my_subprocess returned {y}")

    .. note::

        Because “only picklable objects can be executed” by a
        `Process <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process>`_.
        we cannot pass a local function as the :code:`subprocess`. The best
        workaround is to define at the module top-level a :code:`subprocess`
        function which takes all its parameters as arguments, and then use
        `functools.partial <https://docs.python.org/3/library/functools.html#functools.partial>`_
        to bind local values to the :code:`subprocess` parameters.

        The :code:`callback` does not have this problem; we can pass a local
        function as the :code:`callback`.

    The :func:`run_subprocess_with_callback` function provides a :code:`callback`
    function for messaging back up to the main process, but it does not provide a
    built-in way to message down to the :code:`subprocess`.

    To message down to the :code:`subprocess` we can create
    and pass a messaging object to the :code:`subprocess`, for example a
    `multiprocessing.Queue <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Queue>`_.

    Because the :code:`subprocess` is started in the
    `"spawn" context <https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods>`_,
    we must create the :code:`Queue` in the :code:`"spawn"` context.

    .. code-block:: python
        :caption: Example of Queue messaging from the main process to the subprocess

        async def my_subprocess(
            # This function will run in a subprocess in a new event loop.
            msg_queue: multiprocessing.queues.Queue[str],
            callback: typing.Callable[[int], None],
        ) -> str:
            while (msg := msg_queue.get()) != "finish":
                callback(len(msg))
            return "done"

        async def main() -> None:
            msg_queue: multiprocessing.queues.Queue[str] = multiprocessing.get_context("spawn").Queue()

            def local_callback(x:int) -> None:
                # This function will run in the main process event loop.
                print(f"callback {x}")

            async def send_messages() -> None:
                msg_queue.put("one")
                msg_queue.put("finish")

            y, _ = await asyncio.gather(
                run_subprocess_with_callback(
                    functools.partial(my_subprocess, msg_queue),
                    local_callback,
                ),
                send_messages())
            )

            print(f"my_subprocess returned {y}")

    .. note::

        To get proper type hinting on the :code:`Queue`:

        .. code-block:: python

            from __future__ import annotations

    """

    # multiprocessing.Queue can only be used with spawn startmethod
    # if we get it from a spawn context.
    # https://stackoverflow.com/questions/34847203/queue-objects-should-only-be-shared-between-processes-through-inheritance
    # https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods
    #
    # “You generally can't pass a multiprocessing.Queue as argument after a
    # Process has already started, you need to pass it already to the constructor
    # of the Process object.”
    # https://stackoverflow.com/questions/63419229/passing-a-queue-with-concurrent-futures-regardless-of-executor-type#comment112144271_63419229

    spawncontext: SpawnContext = multiprocessing.get_context("spawn")
    callback_send = spawncontext.Queue()
    proc = spawncontext.Process(
        group=None,
        target=_run_subprocess,
        args=(subprocess, callback_send),
        daemon=True,
    )
    # We alternate waiting on the queue and waiting on the event loop.
    # There is no good way in Python to wait on both at the same time.
    # Mostly we wait on the event loop, and poll the queue.
    # Because we want to be able to cancel the task.
    # Because then the event loop can run.
    # Unfortunately this means
    #   1. We raise queue.Empty errors all the time internally.
    #   2. There is an extra <100ms delay calling the callback.
    #   3. There is some extra CPU busy-waiting while the subprocess is running.
    proc.start()
    while True:
        try:
            while True:
                # Pull messages out of the queue as fast as we can until
                # the queue is empty.
                # Then wait on the event loop for 100ms and check the queue
                # again.
                message = callback_send.get_nowait()
                match message:
                    case _EndProcess(r):
                        # subprocess returned
                        proc.join()  # We know that process end is imminent.
                        return r
                    case _ExceptionWrapper(ex, ex_string):
                        # subprocess raised an exception
                        if hasattr(ex, "add_note"):
                            # https://docs.python.org/3/library/exceptions.html#BaseException.add_note
                            ex.add_note("".join(ex_string))  # type: ignore  # noqa: PGH003
                        proc.join()  # We know that process end is imminent.
                        raise ex  # including CancelledError
                    case (args, kwargs):
                        # subprocess called callback
                        try:
                            callback(*args, **kwargs)  # type: ignore  # noqa: PGH003
                        except:  # noqa: S110, E722
                            # We suppress exceptions in the callback.
                            pass
                    case _:
                        raise RuntimeError("unreachable")
        except queue.Empty:
            pass
        # Can the callback_send queue raise any other kind of exception?
        try:
            await asyncio.sleep(0.1)  # CancelledError can be raised here
        except asyncio.CancelledError:
            # https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process.terminate
            # > “Warning: If this method is used when the associated process is
            # > using a pipe or queue then the pipe or queue is liable to become
            # corrupted and may become unusable by other process.”
            #
            # Really?

            # https://docs.python.org/3/library/multiprocessing.html#pipes-and-queues
            # > “Warning If a process is killed using Process.terminate() while
            # > it is trying to use a Queue, then the data in the queue is
            # > likely to become corrupted. This may cause any other process to
            # get an exception when it tries to use the queue later on.”
            #
            # What kind of exception?

            # Windows
            # https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess#remarks
            # > “The terminated process cannot exit until all pending I/O has
            # > been completed or canceled.”

            proc.terminate()

            # https://docs.python.org/3/library/multiprocessing.html#pipes-and-queues
            # > ”This means that if you try joining that process you may get a
            # > deadlock unless you are sure that all items which have been put
            # > on the queue have been consumed.”
            try:
                while True:
                    callback_send.get_nowait()
            except queue.Empty:
                pass

            # https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process.join
            proc.join()

            # proc.close()?
            # https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process.close
            # https://stackoverflow.com/questions/58866837/python3-multiprocessing-terminate-vs-kill-vs-close/58866932#58866932
            # > “close allows you to ensure the resources are definitely cleaned at a
            # > specific point in time”
            # We don't need to call close() because we are not worried about
            # the OS running out of file descriptors.

            raise
