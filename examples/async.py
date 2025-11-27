#
# python examples/async.py
#


import asyncio
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

    ######### Test max_concurrent=None

    a, set_a = ed.use_state(0)
    b, set_b = ed.use_state(0)

    async def _on_change1_later(v: int):
        set_a(v)
        await asyncio.sleep(1)
        set_b(v)

    _on_change1, _ = ed.use_async_call(_on_change1_later, max_concurrent=None)

    ##########

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

    ########## Test use_async_call max_concurrent

    async def do_thing_async(i: int):
        print(f"do_thing {i} started")  # noqa: T201
        try:
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            print(f"do_thing {i} cancelled")  # noqa: T201
            raise
        print(f"do_thing {i} finished")  # noqa: T201

    do_thing, _ = ed.use_async_call(do_thing_async, max_concurrent=3)

    def three_things():
        for i in range(5):
            do_thing(i)

    k, set_k = ed.use_state(cast(list[tuple[int, str]], []))

    async def start_k_async():
        print("start_k_async")  # noqa: T201

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
            print("start_k_async cancelled")  # noqa: T201
            set_k(k_updater_cancel())
            raise
        print("start_k_async complete")  # noqa: T201

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
                "padding": 20,
            },
        ):
            with ed.ButtonView(
                on_trigger=lambda _ev: three_things(),
            ):
                ed.Label(text="Do 5 async things (max 3 concurrent)")

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
