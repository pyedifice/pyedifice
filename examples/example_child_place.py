import edifice as ed


@ed.component
def Main(self: ed.Element) -> None:
    with ed.Window(
        style={
            "min-width": 700,
            "min-height": 700,
        },
    ):
        with ed.View(style={"background": "blue"}):
            label = ed.Label("Label")
            with ed.View(style={"background": "red", "margin-top": 100}):
                ed.child_place(label)


def main_loop() -> None:
    app = ed.App(Main())
    app.start()


if __name__ == "__main__":
    main_loop()
