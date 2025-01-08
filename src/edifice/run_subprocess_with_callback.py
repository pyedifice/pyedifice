from __future__ import annotations

import asyncio
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

def _run_subprocess(
    subprocess: typing.Callable[[typing.Callable[_P_callback, None]], typing.Awaitable[_T_subprocess]],
    qup: queue.Queue,
) -> _T_subprocess | BaseException: # type of Queue?
    subloop = asyncio.new_event_loop()
    async def work() -> _T_subprocess | BaseException:
        try:
            def _run_callback(*args: _P_callback.args, **kwargs: _P_callback.kwargs) -> None:
                qup.put((args, kwargs))
            r = await subprocess(_run_callback)
        except BaseException as e:  # noqa: BLE001
            return e
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
    Run an async :code:`subprocess` in a
    `ProcessPoolExecutor <https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor>`_
    and return the result.

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

    While the :code:`subprocess` is running, it may call the supplied :code:`callback` function.
    The :code:`callback` function will run in the main event loop of the calling process.

    If this async :func:`run_subprocess_with_callback` function is cancelled,
    the :code:`subprocess` will be terminated by calling
    `Process.terminate() <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process.terminate>`_.

    Exceptions raised in the :code:`subprocess` will be re-raised and will cancel :func:`run_subprocess_with_callback`.

    Exceptions raised in the :code:`callback` will be re-raised and will cancel :func:`run_subprocess_with_callback`.

    This function is useful for a long-running parallel worker
    subprocess for which we want to report progress back to the main GUI event loop.
    Like :code:`pytorch` stuff.

    .. code-block:: python
        :caption: Example

        def my_callback(x:int) -> None:
            # This function will run in the main process event loop.
            print(f"callback {x}")

        async def my_subprocess(callback: Callable[[int], None]) -> str:
            # This function will run in a sub-process in a new event loop.
            callback(1)
            await asyncio.sleep(1)
            callback(2)
            await asyncio.sleep(1)
            callback(3)
            return "done"

        async def main() -> None:
            y = await run_subprocess_with_callback(my_subprocess, my_callback)
            print(f"subprocess returned {y}")

    .. note::

        Because “only picklable objects can be executed” by a
        `ProcessPoolExecutor <https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor>`_,
        we cannot pass a local function as the :code:`subprocess`. The best
        workaround is to define a :code:`subprocess` module top-level function
        which takes all its parameters as arguments, and then use
        `functools.partial <https://docs.python.org/3/library/functools.html#functools.partial>`_
        to bind local values to the :code:`subprocess` parameters.

    The :func:`run_subprocess_with_callback` function provides a :code:`callback`
    function for signalling back up to the main process, but it does not provide a
    build-in way to signal down to the subprocess. You can create and bind
    signalling objects to the :code:`subprocess`, for example a
    `multiprocessing.synchronize.Event <https://docs.python.org/3/library/multiprocessing.html#multiprocessing.managers.SyncManager.Event>`_.

    .. code-block:: python
        :caption: Example of Event signalling from the main process to the subprocess

        async def my_subprocess(
            event: threading.Event,
            callback: Callable[[int], None],
        ) -> str:
            # This function will run in a sub-process in a new event loop.
            if event.is_set():
                return "early return"
            callback(10)
            await asyncio.sleep(1)
            if event.is_set():
                return "early return"
            callback(20)
            await asyncio.sleep(1)
            if event.is_set():
                return "early return" # We will return here.
            callback(30)
            return "done"

        async def main() -> None:
            with multiprocessing.Manager() as manager:
                event = manager.Event()

                def local_callback(x:int) -> None:
                    # This function will run in the main process event loop.
                    print(f"callback {x}")
                    if x > 10:
                        event.set()

                y = await run_subprocess_with_callback(
                    functools.partial(my_subprocess, event),
                    local_callback,
                )
                print(f"subprocess returned {y}")

    """


    with (
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
                    callback(*(i[0]), **(i[1])) # type: ignore  # noqa: PGH003

            get_messages_task = asyncio.create_task(get_messages())

            retval, _ = await asyncio.gather(subtask, get_messages_task)
            if isinstance(retval, BaseException):
                raise retval  # noqa: TRY301
            return retval  # noqa: TRY300
        except BaseException: # including asyncio.CancelledError
            # We must terminate the process pool workers because the
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
