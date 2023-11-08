#
# python examples/tablegrid1.py
#

import os, sys
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
import edifice as ed
from edifice.hooks import use_state
from edifice import TableGridView
from edifice import ButtonView

@ed.component
def myComponent(self):

    row_key, set_row_key = use_state(1)
    rows, set_rows = use_state([])

    def add_key():
        new_rows = rows.copy()
        new_rows.append(row_key)
        set_rows(new_rows)
        set_row_key(row_key + 1)

    def del_key(i: int):
        new_rows = rows.copy()
        new_rows.remove(i)
        set_rows(new_rows)

    with ed.View(style = {"align": "top"}):

        with ed.View(style={"margin":10}):
            with ButtonView(
                on_click=lambda ev: add_key(),
                style={"width": 100, "height": 30, "margin": 10},
            ):
                ed.Label(text="Add Row")

        with TableGridView(
        ) as tgv:
            for rkey in rows:
                with tgv.row():
                    ed.Label(text="Key " + str(rkey) + " Column 0").set_key(str(rkey) + "_0")
                    ed.Label(text="Key " + str(rkey) + " Column 1").set_key(str(rkey) + "_1")
                    with ButtonView(
                        on_click=lambda ev, rkey=rkey: del_key(rkey)
                    ).set_key(str(rkey) + "_2"):
                        ed.Label(text="Delete Key " + str(rkey))

if __name__ == "__main__":
    ed.App(myComponent()).start()
