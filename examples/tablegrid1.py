#
# python examples/tablegrid1.py
#

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

    with ed.Window().render():
        with ed.View(style={"align": "top"}).render():
            with ed.View(style={"margin": 10}).render():
                with ButtonView(
                    on_click=lambda ev: add_key(),
                    style={"width": 100, "height": 30, "margin": 10},
                ).render():
                    ed.Label(text="Add Row").render()

            with TableGridView().render() as tgv:
                for rkey in rows:
                    with tgv.row().render():
                        ed.Label(text="Key " + str(rkey) + " Column 0").render()
                        ed.Label(text="Key " + str(rkey) + " Column 1").render()
                        with ButtonView(on_click=lambda ev, rkey=rkey: del_key(rkey)).render():
                            ed.Label(text="Delete Key " + str(rkey)).render()


if __name__ == "__main__":
    ed.App(myComponent()).start()
