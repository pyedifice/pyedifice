#
# python examples/tablegrid1.py
#

import typing as tp
from copy import copy

import edifice as ed


@ed.component
def Main(self):
    row_key, set_row_key = ed.use_state(1)
    rows, set_rows = ed.use_state(tp.cast(list[int], []))

    def add_key():
        new_rows = copy(rows)
        new_rows.append(row_key)
        set_rows(new_rows)
        set_row_key(row_key + 1)

    def del_key(i: int):
        new_rows = copy(rows)
        new_rows.remove(i)
        set_rows(new_rows)

    with ed.Window():
        with ed.VBoxView(style={"align": "top"}):
            with ed.VBoxView(style={"padding": 10}):
                with ed.ButtonView(
                    on_click=lambda _ev: add_key(),
                    style={"width": 100, "height": 30, "padding": 10},
                ):
                    ed.Label(text="Add Row")

            with ed.TableGridView():
                for rkey in rows:
                    with ed.TableGridRow().set_key(str(rkey)):
                        ed.Label(text="Key " + str(rkey) + " Column 0")
                        ed.Label(text="Key " + str(rkey) + " Column 1")
                        with ed.ButtonView(on_click=lambda _ev, rkey=rkey: del_key(rkey)):
                            ed.Label(text="Delete Key " + str(rkey))


if __name__ == "__main__":
    ed.App(Main()).start()
