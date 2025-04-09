#
# python examples/use_context_select1.py
#

import edifice as ed


@ed.component
def Main(self):
    with ed.Window(_size_open=(800, 400)):
        ProviderComponent()


@ed.component
def ProviderComponent(self):
    intxt: str
    intxt, intxt_set = ed.provide_context("ctxkey", "")

    print("render ProviderComponent")
    with ed.VBoxView():
        ed.TextInput(
            text=intxt,
            on_change=intxt_set,
            placeholder_text="Enter comma-separated values",
        )
        with ed.FlowView():
            for i in range(10):
                Item(i=i)


@ed.component
def Item(self, i: int):
    def selector_fn(intxt: str) -> str | None:
        splits = intxt.split(",")
        if i >= len(splits):
            return None
        return splits[i]

    intxt_item: str | None
    intxt_item = ed.use_context_select("ctxkey", selector_fn)

    print(f"render Item {i} with value {intxt_item}")

    with ed.VBoxView(style={"padding": 5}):
        ed.Label(text=f"Item {i}")
        with ed.HBoxView(style={"padding": 5, "border": "1px solid black", "min-width": 30}):
            if intxt_item is None:
                ed.Label(
                    text="🥚",
                    style={
                        "font-family": "Noto Color Emoji",
                        "font-size": 20,
                    },
                )
            else:
                ed.Label(text=intxt_item)


if __name__ == "__main__":
    ed.App(Main()).start()
