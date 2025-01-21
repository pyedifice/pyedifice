#
# python examples/async.py
#


import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import cast

import edifice as ed


def use_clocktick() -> int:
    tick, tick_set = ed.use_state(0)

    async def increment():
        while True:
            await asyncio.sleep(1)
            tick_set(lambda t: t + 1)

    ed.use_async(increment)

    return tick


@ed.component
def Clock(self):
    tick = use_clocktick()
    ed.Label(str(tick))


@ed.component
def ComponentWithAsync(self):
    """
    Component with an async Hook so we can test unmounting.
    """

    x, set_x = ed.use_state("async incomplete")

    async def set_label():
        print("async start")  # noqa: T201
        try:
            await asyncio.sleep(1)
            print("async complete")  # noqa: T201
            set_x("async complete")
        except asyncio.CancelledError:
            print("async cancelled")  # noqa: T201
            set_x("async cancelled")
            raise

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

    ########## Test that async exceptions are silently thrown away

    async def asyncthrow():
        await asyncio.sleep(1)
        raise ValueError("Test error")

    callthrow, _ = ed.use_async_call(asyncthrow)

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
        except asyncio.CancelledError:
            set_k(k_updater_cancel())
            raise

    start_k, cancel_k = ed.use_async_call(start_k_async)

    ##########

    show_clock, set_show_clock = ed.use_state(True)

    ##########

    with ed.VBoxView(style={"align": "top"}):
        with ed.VBoxView():
            ed.CheckBox(
                checked=show_clock,
                on_change=set_show_clock,
                text="Show Clock",
            )
            if show_clock:
                Clock()

        with ed.VBoxView(
            style={
                "padding-top": 20,
                "padding-bottom": 20,
                "border-top-width": "1px",
                "border-top-style": "solid",
                "border-top-color": "black",
            },
        ):
            with ed.HBoxView():
                ed.CheckBox(
                    checked=checked,
                    on_change=set_checked,
                )
                if checked:
                    ComponentWithAsync()

        with ed.VBoxView(
            style={
                "padding-top": 20,
                "padding-bottom": 20,
                "border-top-width": "1px",
                "border-top-style": "solid",
                "border-top-color": "black",
            },
        ):
            ed.Label(str(a))
            ed.Label(str(b))
            ed.Slider(a, min_value=0, max_value=100, on_change=_on_change1)

        with ed.VBoxView(
            style={
                "padding-top": 20,
                "padding-bottom": 20,
                "border-top-width": "1px",
                "border-top-style": "solid",
                "border-top-color": "black",
            },
        ):
            ed.Label(str(c))
            ed.Slider(c, min_value=0, max_value=100, on_change=_on_change2)

        with ed.VBoxView(
            style={
                "padding-top": 20,
                "padding-bottom": 20,
                "border-top-width": "1px",
                "border-top-style": "solid",
                "border-top-color": "black",
            },
        ):
            ed.Label(str(e))
            ed.Slider(d, min_value=0, max_value=100, on_change=set_d)

        with ed.VBoxView(
            style={
                "padding": 20,
            },
        ):
            with ed.ButtonView(
                on_trigger=lambda _ev: callthrow(),
            ):
                ed.Label(text="Async throw ValueError after 1 sec")

        with ed.VBoxView(
            style={
                "padding-top": 20,
                "padding-bottom": 20,
                "border-top-width": "1px",
                "border-top-style": "solid",
                "border-top-color": "black",
            },
        ):
            with ed.HBoxView():
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
