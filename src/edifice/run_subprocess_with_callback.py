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
    subprocess: typing.Callable[[typing.Callable[_P_callback, None]], _T_subprocess],
    callback_send: multiprocessing.queues.Queue,
) -> None:

    def _run_callback(*args: _P_callback.args, **kwargs: _P_callback.kwargs) -> None:
        callback_send.put((args, kwargs))

    try:
        r = subprocess(_run_callback)
    except BaseException as e:  # noqa: BLE001
        callback_send.put(_ExceptionWrapper(e, traceback.format_exception(e)))
    else:
        callback_send.put(_EndProcess(r))

    # https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Queue.join_thread
    # > “By default if a process is not the creator of the queue then on
    # > exit it will attempt to join the queue's background thread.”
    #
    # https://docs.python.org/3/library/multiprocessing.html#pipes-and-queues
    # > “if a child process has put items on a queue (and it has not used
    # > JoinableQueue.cancel_join_thread), then that process will not
    # > terminate until all buffered items have been flushed to the pipe.”


async def run_subprocess_with_callback(
    subprocess: typing.Callable[[typing.Callable[_P_callback, None]], _T_subprocess],
    callback: typing.Callable[_P_callback, None],
    daemon: bool | None = None,
) -> _T_subprocess:
    """
    Run a
    :code:`subprocess` function in a
    `Process <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process>`_
    and return the result.

    Args:
        subprocess:
            The function to run in a
            `Process <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process>`_.
            This :code:`subprocess` function takes a single argument: a function with the same type
            as the :code:`callback` function.
            The :code:`subprocess` function must be picklable.
        callback:
            The :code:`callback` function to pass to the :code:`subprocess` when it starts.
            The :code:`subprocess` may call the :code:`callback` function
            at any time.
            The :code:`callback` function will run in the main process event loop.
            All of the arguments to the :code:`callback` function must be picklable.
        daemon:
            Optional argument which will be passed to the Process
            `daemon <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process.daemon>`_
            argument.

    The advantage of :func:`run_subprocess_with_callback` over
    `run_in_executor <https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor>`_
    `ProcessPoolExecutor <https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor>`_
    is that :func:`run_subprocess_with_callback` behaves
    well and cleans up properly in the event of
    `cancellation <https://docs.python.org/3/library/asyncio-task.html#task-cancellation>`_,
    exceptions, and crashes.
    `ProcessPoolExecutor cannot be cancelled. <https://discuss.python.org/t/cancel-running-work-in-processpoolexecutor/58605>`_.
    This function is useful for a CPU-bound parallel worker
    subprocess for which we want to report progress back to the main GUI event loop.
    Like *PyTorch* stuff.

    The :code:`subprocess` will be started when :code:`await` :func:`run_subprocess_with_callback`
    is entered, and the :code:`subprocess` is guaranteed to be terminated when
    :code:`await` :func:`run_subprocess_with_callback` completes.

    While the :code:`subprocess` is running, it may call the supplied :code:`callback` function.
    The :code:`callback` function will run in the main event loop of the calling process.

    The :code:`subprocess` will be started with the
    `"spawn" start method <https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods>`_,
    so it will not inherit any file handles from the calling process.

    .. code-block:: python
        :caption: Example

        def my_subprocess(callback: Callable[[int], None]) -> str:
            # This function will run in a new Process.
            callback(1)
            time.sleep(1)
            callback(2)
            time.sleep(1)
            callback(3)
            return "done"

        def my_callback(x:int) -> None:
            # This function will run in the main process event loop.
            print(f"callback {x}")

        async def main() -> None:
            y = await run_subprocess_with_callback(my_subprocess, my_callback)

            # If this main() function is cancelled while awaiting
            # run_subprocess_with_callback then the subprocess will be terminated.

            print(f"my_subprocess returned {y}")

    Cancellation, Exceptions, Crashes
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    If this :code:`async` :func:`run_subprocess_with_callback` function is
    `cancelled <https://docs.python.org/3/library/asyncio-task.html#task-cancellation>`_,
    then the :code:`subprocess` will be terminated by calling
    `Process.terminate() <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process.terminate>`_.
    Termination of the :code:`subprocess` will occur even if
    the :code:`subprocess` is blocked. Note that
    `CancelledError <https://docs.python.org/3/library/asyncio-exceptions.html#asyncio.CancelledError>`_
    will not be raised in the :code:`subprocess`,
    instead the :code:`subprocess` will be terminated immediately. If you
    want to perform sudden cleanup and halt of the :code:`subprocess` then
    send it a message as in the below `Example of Queue messaging.`

    Exceptions raised in the :code:`subprocess` will be re-raised from :func:`run_subprocess_with_callback`,
    including
    `CancelledError <https://docs.python.org/3/library/asyncio-exceptions.html#asyncio.CancelledError>`_.
    Because the Exception must be pickled back to the main process, it will
    lose its `traceback <https://docs.python.org/3/reference/datamodel.html#traceback-objects>`_.
    In Python ≥3.11, the traceback string from the :code:`subprocess` stack will be added
    to the Exception `__notes__ <https://docs.python.org/3/library/exceptions.html#BaseException.__notes__>`_.

    Exceptions raised in the :code:`callback` will be suppressed.

    If the :code:`subprocess` exits abnormally without returning a value then a
    `ProcessError <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.ProcessError>`_
    will be raised from :func:`run_subprocess_with_callback`.

    Pickling the subprocess
    ^^^^^^^^^^^^^^^^^^^^^^^

    Because “only picklable objects can be executed” by a
    `Process <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process>`_.
    we cannot pass a local function with local variable bindings
    as the :code:`subprocess`. The best workaround is to define at the module
    top-level a :code:`subprocess` function which takes all its parameters as
    arguments, and then use
    `functools.partial <https://docs.python.org/3/library/functools.html#functools.partial>`_
    to bind local values to the :code:`subprocess` parameters.
    See below `Example of Queue messaging.`

    The :code:`callback` does not have this problem; we can pass a local
    function as the :code:`callback`.

    Messaging to the subprocess
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

        def my_subprocess(
            # This function will run in a new Process.
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

            # In this example we use gather() to run these 2 functions
            # concurrently (“at the same time”).
            #
            # 1. run_subprocess_with_callback()
            # 2. send_messages()
            #
            # In your code you will probably instead want to send_messages()
            # in reaction to some event.
            #
            y, _ = await asyncio.gather(
                run_subprocess_with_callback(
                    functools.partial(my_subprocess, msg_queue),
                    local_callback,
                ),
                send_messages(),
            )

            print(f"my_subprocess returned {y}")

    .. note::

        To get proper type hinting on the :code:`Queue`:

        .. code-block:: python

            from __future__ import annotations

    Async in the subprocess
    ^^^^^^^^^^^^^^^^^^^^^^^

    If you want the :code:`subprocess` to run an :code:`async` function then
    make a new event loop and use that as the event loop in the
    :code:`subprocess`.

    .. code-block:: python
        :caption: Example async subprocess function

        def my_subprocess(callback: typing.Callable[[int], None]) -> str:
            # This function will run in a new Process.

            async def work() -> str:
                callback(1)
                await asyncio.sleep(1)
                return "done"

            return asyncio.new_event_loop().run_until_complete(work())

    A cancelled :code:`await` in the :code:`subprocess` will raise
    `CancelledError <https://docs.python.org/3/library/asyncio-exceptions.html#asyncio.CancelledError>`_
    which will be propagated and re-raised from
    :func:`run_subprocess_with_callback` in the usual way.

    PyInstaller
    ^^^^^^^^^^^

    If you build a distribution with `PyInstaller <https://pyinstaller.org/>`_
    then you should call
    `multiprocessing.freeze_support() <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.freeze_support>`_
    to divert the spawn Process
    `before the __main__ imports <https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html#when-to-call-multiprocessing-freeze-support>`_
    so that the spawn Process starts up faster.

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
        daemon=daemon,
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
                            # TODO I don't like suppressing exceptions but
                            # but it's tricky to decide what to do with them
                            # here. If we raise them then we must also
                            # terminate the subprocess.
                            pass
                    case _:
                        raise RuntimeError("unreachable")
        except queue.Empty:
            pass
        # Can the callback_send queue raise any other kind of exception?
        if not proc.is_alive() and callback_send.empty():
            # Is that extra empty() check necessary and sufficient to avoid a
            # race condition when the process returns normally and exits?
            # Yes, because
            # https://docs.python.org/3/library/multiprocessing.html#pipes-and-queues
            # > “if a child process has put items on a queue (and it has not used
            # > JoinableQueue.cancel_join_thread), then that process will not
            # > terminate until all buffered items have been flushed to the pipe.”
            #
            # This is a lot of extra system calls, too bad we have to poll like this.
            raise multiprocessing.ProcessError(f"subprocess exited with code {proc.exitcode}")
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
