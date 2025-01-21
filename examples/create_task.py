
import asyncio
import qasync


def indirection(arg):
    return arg

async def fn_coroutine() -> int:
    # raise ValueError("interrupt the coroutine")
    return 1

tasks = set()

async def main() -> None:
    def on_done(t: asyncio.Task) -> None:
        tasks.discard(t)
        print("Task done")
        # t.result()

    # task = asyncio.create_task(fn_coroutine())
    # task = asyncio.create_task((lambda:fn_coroutine())())
    # task = asyncio.create_task((lambda:fn_coroutine)()())
    task = asyncio.create_task(indirection(fn_coroutine()))
    task.add_done_callback(on_done)
    tasks.add(task)

    # await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(main())
    # qasync.run(main())
