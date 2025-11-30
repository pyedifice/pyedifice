#
# python examples/marker_data_viewer.py
#

import asyncio
import importlib.resources
import logging
import random

import edifice as ed

stylesheet = {
    "price_box": {
        "padding-top": 0,
        "padding": 0,
        "width": "50px",
        "align": "right",
        "border": "1px solid black",
        "height": "25px",
    },
    "size_box": {
        "color": "rgba(220, 230, 220, 1)",
        "margin": "0px",
        "padding": "2px",
        "top": "0px",
        "align": "right",
        "border-top": "1px solid black",
        "width": "50px",
        "height": "25px",
    },
    "size_bar": {
        "height": "25px",
        "margin-left": "10px",
        "padding": "2px",
        "align": "left",
    },
}

logger = logging.getLogger("Edifice")
logger.setLevel(logging.INFO)


@ed.component
def PriceLevel(self, price, size, side, last=False):
    if side == "bid":
        color = "rgba(50, 50, 255, 1)"
    else:
        color = "rgba(255, 50, 50, 1)"

    price_box_style = stylesheet["price_box"].copy()
    size_box_style = stylesheet["size_box"].copy()
    size_bar_style = stylesheet["size_bar"].copy()

    size_box_style["background-color"] = color
    size_bar_style.update(
        {
            "background-color": color,
            "width": "%spx" % (size / 5),
        },
    )
    if last:
        price_box_style["border-bottom"] = "1px solid black"
        size_box_style["border-bottom"] = "1px solid black"

    with ed.HBoxView(style={"padding": "0px", "width": "360px", "align": "left"}):
        ed.Label(str(price), style=price_box_style).set_key("price")
        ed.Label(str(size), style=size_box_style).set_key("size")
        ed.Label("", style=size_bar_style).set_key("vis_size")


@ed.component
def Book(self, book):
    sizes = book["sizes"]
    market_price = book["price"]
    with ed.VBoxView(style={"padding": "10px", "width": 360}):
        for p in range(20, 0, -1):
            PriceLevel(price=p, size=sizes[p], side="bid" if p < market_price else "ask", last=(p == 1)).set_key(str(p))


book_init = {"price": 10, "sizes": [random.randint(100, 300) for _ in range(21)]}  # noqa: S311


@ed.component
def App(self):
    book, book_set = ed.use_state(book_init)

    playing, playing_set = ed.use_state(False)

    def update_book():
        book_set({"price": 10, "sizes": [random.randint(100, 300) for _ in range(21)]})  # noqa: S311

    async def play_tick():
        while playing:
            update_book()
            await asyncio.sleep(0.05)

    ed.use_async(play_tick, playing)

    def play(e):
        playing_set(lambda p: not p)

    with ed.Window():
        with ed.VBoxView():
            with ed.HBoxView(style={"align": "left", "padding-left": "10px"}):
                ed.ImageSvg(
                    src=str(importlib.resources.files("edifice") / "icons/font-awesome/solid/chart-line.svg"),
                    style={"width": 20, "height": 20},
                )
                ed.Label("Market Data Viewer", style={"margin-left": "5px"})
                with ed.HBoxView(style={"align": "left", "padding-left": "10px"}):
                    with ed.ButtonView(
                        style={"width": "50px", "height": "25px"},
                        on_trigger=play,
                    ):
                        ed.ImageSvg(
                            src=str(
                                importlib.resources.files("edifice")
                                / (
                                    "icons/font-awesome/solid/pause.svg"
                                    if playing
                                    else "icons/font-awesome/solid/play.svg"
                                ),
                            ),
                            style={"width": 10, "height": 10},
                        )
            Book(book)


if __name__ == "__main__":
    ed.App(App()).start()
