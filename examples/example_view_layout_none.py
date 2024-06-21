import edifice as ed
from edifice.engine import TreeBuilder


@ed.component
def Main(self: ed.Element) -> ed.Element:
    put = TreeBuilder()
    with put(
        ed.Window(
            style={
                "min-width": 700,
                "min-height": 700,
            },
        )
    ) as root:
        items, items_set = ed.use_state([200, 400, 600])

        def on_change_list(checked: bool, item: int) -> None:
            if checked and item not in items:
                items_ = items.copy()
                items_.append(item)
                items_.sort()
                items_set(items_)
            elif not checked and item in items:
                items_ = items.copy()
                items_.remove(item)
                items_set(items_)

        with put(ed.View(layout="column")):
            with put(ed.View(layout="row")):
                for i in [100, 200, 300, 400, 500, 600]:
                    put(
                        ed.CheckBox(
                            checked=True if i in items else False,
                            on_change=lambda checked, i=i: on_change_list(checked, i),
                            text=str(i),
                        )
                    )
            with put(ed.View(layout="none", style={"width": 640, "height": 640, "background-color": "black"})):
                for v in items:
                    put(
                        ed.Label(
                            text=str(v),
                            word_wrap=False,
                            style={"top": v, "left": v},
                        )
                    )
        return root


def main_loop() -> None:
    app = ed.App(Main())
    app.start()


if __name__ == "__main__":
    main_loop()
