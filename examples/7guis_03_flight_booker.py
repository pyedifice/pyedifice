#
# https://7guis.github.io/7guis/tasks#flight
#

from __future__ import annotations

import datetime

import edifice as ed


@ed.component
def Main(self):
    twoway, twoway_set = ed.use_state(False)
    t1, t1_set = ed.use_state("27.03.2014")
    t2, t2_set = ed.use_state("27.03.2014")
    booked, booked_set = ed.use_state(False)

    t1_date: datetime.date | None = None
    try:
        t1_date = datetime.datetime.strptime(t1, "%d.%m.%Y").date()  # noqa: DTZ007
    except ValueError:
        pass

    t2_date: datetime.date | None = None
    try:
        t2_date = datetime.datetime.strptime(t2, "%d.%m.%Y").date()  # noqa: DTZ007
    except ValueError:
        pass

    with ed.Window(title="Flight Booker"):
        with ed.VBoxView(style={"padding": 10}):
            if not booked:
                ed.Dropdown(
                    selection=0,
                    options=["one-way flight", "return flight"],
                    on_select=lambda index: twoway_set(index == 1),
                )
                ed.TextInput(
                    text=t1,
                    on_change=t1_set,
                    style={"background-color": "red"} if t1_date is None else {},
                )
                ed.TextInput(
                    text=t2,
                    on_change=t2_set,
                    enabled=twoway,
                    style={"background-color": "red"} if twoway and t2_date is None else {},
                )
                ed.Button(
                    title="Book",
                    enabled=(not twoway and t1_date is not None)
                    or (twoway and t1_date is not None and t2_date is not None and t1_date <= t2_date),
                    on_click=lambda _: booked_set(True),
                )
            elif not twoway:
                assert t1_date is not None
                ed.Label(
                    text=f"You have booked a one-way flight on {t1_date.strftime('%d.%m.%Y')}.",
                    word_wrap=True,
                )
            else:
                assert t1_date is not None
                assert t2_date is not None
                ed.Label(
                    text=f"You have booked a flight on"
                    f" {t1_date.strftime('%d.%m.%Y')} returning {t2_date.strftime('%d.%m.%Y')}.",
                    word_wrap=True,
                )


if __name__ == "__main__":
    ed.App(Main()).start()
