# Example to test the FlowView children re-ordering.

from dataclasses import dataclass, replace

import edifice as ed


@dataclass(frozen=True)
class Item:
    rank: int
    is_available: bool


@ed.component
def Main(self: ed.Element) -> None:
    def _init() -> tuple[Item, ...]:
        return tuple(Item(i, False) for i in range(1, 11))

    items, items_set = ed.use_state(_init)
    sort_method, sort_method_set = ed.use_state(1)

    def _toggle_available(rank: int, is_available: bool) -> None:
        new_items = list(items)
        for i in range(len(new_items)):
            if new_items[i].rank == rank:
                new_items[i] = replace(new_items[i], is_available=is_available)
        items_set(tuple(new_items))

    # print(f"Sort method: {sort_method}")
    match sort_method:
        case 0:
            display_times = items[::-1]
        case 1:
            display_times = items
        case _:
            display_times = tuple(sorted(
                items,
                key=lambda item: int(item.is_available),
                reverse=True,
            ))

    with ed.Window(_size_open=(500, 200)):
        with ed.VBoxView():
            ed.Dropdown(
                selection=sort_method,
                options=["Highest to lowest", "Lowest to highest", "Selected first"],
                enable_mouse_scroll=False,
                on_select=sort_method_set,
            )
            with ed.FlowView():
                # print("Rendering items ---------")
                for item in display_times:
                    # print(item.rank)
                    ed.CheckBox(
                        checked=item.is_available,
                        text=str(item.rank),
                        on_change=lambda is_available, rank=item.rank: _toggle_available(rank, is_available),
                        style={"padding": 5},
                    ).set_key(str(item.rank))


if __name__ == "__main__":
    ed.App(Main()).start()
