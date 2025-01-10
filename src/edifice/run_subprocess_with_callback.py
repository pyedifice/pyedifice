from __future__ import annotations

import asyncio
import dataclasses
import typing
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
from multiprocessing.context import SpawnContext

if typing.TYPE_CHECKING:
    import queue

_T_subprocess = typing.TypeVar("_T_subprocess")
_P_callback = typing.ParamSpec("_P_callback")


class _EndProcess:
    pass


@dataclasses.dataclass
class _ExceptionWrapper:
    ex: BaseException


def _run_subprocess(
    subprocess: typing.Callable[[typing.Callable[_P_callback, None]], typing.Awaitable[_T_subprocess]],
    qup: queue.Queue,  # type of Queue?
) -> _T_subprocess | _ExceptionWrapper:
    subloop = asyncio.new_event_loop()

    async def work() -> _T_subprocess | _ExceptionWrapper:
        try:

            def _run_callback(*args: _P_callback.args, **kwargs: _P_callback.kwargs) -> None:
                qup.put((args, kwargs))

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
            return _ExceptionWrapper(e)
        else:
            return r
        finally:
            qup.put(_EndProcess())

    return subloop.run_until_complete(work())


async def run_subprocess_with_callback(
    subprocess: typing.Callable[[typing.Callable[_P_callback, None]], typing.Awaitable[_T_subprocess]],
    callback: typing.Callable[_P_callback, None],
) -> _T_subprocess:
    """
    Run an
    async :code:`subprocess` in a
    `ProcessPoolExecutor <https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor>`_
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
            `ProcessPoolExecutor <https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor>`_.
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
    `'spawn' start method <https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods>`_,
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

    Exceptions raised in the :code:`callback` will be suppressed.

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
        `ProcessPoolExecutor <https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor>`_,
        we cannot pass a local function as the :code:`subprocess`. The best
        workaround is to define at the module top-level a :code:`subprocess`
        function which takes all its parameters as arguments, and then use
        `functools.partial <https://docs.python.org/3/library/functools.html#functools.partial>`_
        to bind local values to the :code:`subprocess` parameters.

        The :code:`callback` does not have this problem; we can pass a local
        function as the :code:`callback`.

    The :func:`run_subprocess_with_callback` function provides a :code:`callback`
    function for messaging back up to the main process, but it does not provide a
    built-in way to message down to the subprocess. To accomplish this we can create
    and pass a messaging object to the :code:`subprocess`, for example a
    `multiprocessing.managers.SyncManager.Queue <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.managers.SyncManager.Queue>`_.

    .. code-block:: python
        :caption: Example of Queue messaging from the main process to the subprocess

        async def my_subprocess(
            # This function will run in a subprocess in a new event loop.
            queue: queue.Queue[str],
            callback: typing.Callable[[int], None],
        ) -> str:
            while (msg := queue.get()) != "finish":
                callback(len(msg))
            return "done"

        async def main() -> None:
            with multiprocessing.Manager() as manager:
                msg_queue: queue.Queue[str] = manager.Queue()

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

    """

    with (
        # https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Manager
        # “corresponds to a spawned child process”
        Manager() as manager,
        # We must have 2 parallel workers. Therefore 2 ProcessPoolExecutors.
        ProcessPoolExecutor(max_workers=1, mp_context=SpawnContext()) as executor_sub,
        ProcessPoolExecutor(max_workers=1, mp_context=SpawnContext()) as executor_queue,
    ):
        try:
            qup: queue.Queue = manager.Queue()

            loop = asyncio.get_running_loop()
            subtask = loop.run_in_executor(executor_sub, _run_subprocess, subprocess, qup)

            async def get_messages() -> None:
                while type(i := (await loop.run_in_executor(executor_queue, qup.get))) is not _EndProcess:
                    try:
                        callback(*(i[0]), **(i[1]))  # type: ignore  # noqa: PGH003
                    except:  # noqa: PERF203, S110, E722
                        # We have to suppress callback exceptions because
                        # asyncio.gather will not cancel the subtask if the
                        # callback raises an exception.
                        # https://docs.python.org/3/library/asyncio-task.html#asyncio.gather
                        # We cannot use TaskGroup because we require Python 3.10.
                        pass

            retval, _ = await asyncio.gather(subtask, get_messages())
            match retval:
                case _ExceptionWrapper(ex):
                    raise ex  # noqa: TRY301
                case _:
                    return retval
            return retval  # noqa: TRY300
        except BaseException:  # including asyncio.CancelledError
            # We must terminate the process pool workers because cancelling the
            # loop.run_in_executor() call will not terminate the workers.
            for process in executor_sub._processes.values():
                # https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process.terminate
                if process.is_alive():
                    process.terminate()
                process.join()
            for process in executor_queue._processes.values():
                # https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process.terminate
                if process.is_alive():
                    process.terminate()
                process.join()
            raise
