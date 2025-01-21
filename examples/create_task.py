import asyncio

tasks = set()

def use_async(fn_coroutine):
    """
    If we change edifice.use_async to take a Coroutine instead of a () -> Couroutine,
    then it works fine but prints a warning to stderr like:

    /home/jbrock/work/oth/pyedifice/pyedifice/examples/run_subprocess.py:30: RuntimeWarning: coroutine 'my_subprocess' was never awaited

    This is an experimental use_async which takes a Coroutine instead of a () -> Couroutine.

    No matter how hard I try I cannot get this to issue the warning.

    This is where
    RuntimeWarning: coroutine 'done_callback' was never awaited
    gets generated.
    https://github.com/python/cpython/blob/d40692db06cdae89447c26b6c1b5d2a682c0974f/Objects/genobject.c#L116-L120
    See also
    https://github.com/python/cpython/blob/d40692db06cdae89447c26b6c1b5d2a682c0974f/Lib/warnings.py#L684

    """
    def on_done(t: asyncio.Task) -> None:
        tasks.discard(t)
        print("Task done")
        # t.result()

    task = asyncio.create_task(fn_coroutine)
    task.add_done_callback(on_done)
    tasks.add(task)

async def main() -> None:

    async def my_coroutine() -> int:
        await asyncio.sleep(1.0)
        # raise ValueError("interrupt the coroutine")
        return 1

    use_async(my_coroutine())
    await asyncio.sleep(2.0)

if __name__ == "__main__":
    asyncio.run(main())
    # qasync.run(main())
