#
# python examples/async.py
#


import asyncio
from concurrent.futures import ThreadPoolExecutor
import edifice as ed
from typing import cast, Callable


@ed.component
def ComponentWithAsync(self):
    """
    Component with an async Hook so we can test unmounting.
    """

    x, set_x = ed.use_state("async incomplete")

    async def set_label():
        print("async start")
        try:
            await asyncio.sleep(1)
            print("async complete")
            set_x("async complete")
        except asyncio.CancelledError as ex:
            print("async cancelled")
            set_x("async cancelled")
            raise ex

    ed.use_async(set_label, ())

    ed.Label(x)


@ed.component
def Main(self):
    ##########

    checked, set_checked = ed.use_state(False)

    #########

    a, set_a = ed.use_state(0)
    b, set_b = ed.use_state(0)

    async def _on_change1(v: int):
        """
        Test regular async event handlers.
        """
        set_a(v)
        await asyncio.sleep(1)
        set_b(v)

    ##########

    c, set_c = ed.use_state(0)

    async def async_callback1(v: int):
        set_c(v)

    callback1, _ = ed.use_async_call(async_callback1)

    async def _on_change2(v: int):
        """
        Test async callbacks from another thread.
        """
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            await loop.run_in_executor(pool, lambda: callback1(v))

    ###########

    d, set_d = ed.use_state(0)
    e, set_e = ed.use_state(0)

    async def _on_change3():
        """
        Test use_async
        """
        set_e(d)

    ed.use_async(_on_change3, d)

    ##########

    k, set_k = ed.use_state(cast(list[tuple[int, str]], []))

    async def start_k_async():
        def k_updater_new():
            def updater(k_):
                k_u = k_[:]
                k_u.insert(0, (0, "Running"))
                return k_u

            return updater

        def k_updater_progress(progress, message):
            def updater(k_):
                k_u = k_[:]
                k_u[0] = (progress, message)
                return k_u

            return updater

        def k_updater_cancel():
            def updater(k_):
                k_u = k_[:]
                k_u[0] = (k_[0][0], "Cancelled")
                return k_u

            return updater

        try:
            set_k(k_updater_new())
            for i in range(1, 9):
                await asyncio.sleep(0.1)
                set_k(k_updater_progress(i * 10, "Running"))
            await asyncio.sleep(0.1)
            set_k(k_updater_progress(100, "Finished"))
        except asyncio.CancelledError as e:
            set_k(k_updater_cancel())
            raise e

    start_k, cancel_k = ed.use_async_call(start_k_async)

    ##########

    with ed.View():
        with ed.View(
            style={
                "margin-top": 20,
                "margin-bottom": 20,
                "border-top-width": "1px",
                "border-top-style": "solid",
                "border-top-color": "black",
            },
        ):
            with ed.View(layout="row"):
                ed.CheckBox(
                    checked=checked,
                    on_change=set_checked,
                )
                if checked:
                    ComponentWithAsync()

        with ed.View(
            style={
                "margin-top": 20,
                "margin-bottom": 20,
                "border-top-width": "1px",
                "border-top-style": "solid",
                "border-top-color": "black",
            },
        ):
            ed.Label(str(a))
            ed.Label(str(b))
            ed.Slider(a, min_value=0, max_value=100, on_change=_on_change1)

        with ed.View(
            style={
                "margin-top": 20,
                "margin-bottom": 20,
                "border-top-width": "1px",
                "border-top-style": "solid",
                "border-top-color": "black",
            },
        ):
            ed.Label(str(c))
            ed.Slider(c, min_value=0, max_value=100, on_change=_on_change2)

        with ed.View(
            style={
                "margin-top": 20,
                "margin-bottom": 20,
                "border-top-width": "1px",
                "border-top-style": "solid",
                "border-top-color": "black",
            },
        ):
            ed.Label(str(e))
            ed.Slider(d, min_value=0, max_value=100, on_change=set_d)

        with ed.View(
            style={
                "margin-top": 20,
                "margin-bottom": 20,
                "border-top-width": "1px",
                "border-top-style": "solid",
                "border-top-color": "black",
            },
        ):
            with ed.View(layout="row"):
                with ed.ButtonView(
                    on_click=lambda _ev: start_k(),
                ):
                    ed.Label(text="Start")
                with ed.ButtonView(
                    on_click=lambda _ev: cancel_k(),
                    enabled=len(k) > 0 and k[0][1] == "Running",
                ):
                    ed.Label(text="Cancel")
            for k_ in k:
                ed.ProgressBar(value=k_[0], format=k_[1])


if __name__ == "__main__":
    ed.App(ed.Window(title="Async Example")(Main())).start()
