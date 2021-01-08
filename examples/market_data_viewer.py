import edifice as ed
import random

stylesheet = ed.PropsDict(dict(
    price_box={
        "padding-top": "2px",
        "top": "0px",
        "min-width": "50px", "max-width": "50px",
        "qproperty-alignment": "AlignRight",
        "border-top": "1px solid black",
        "border-left": "1px solid black", 
        "min-height": "25px", "max-height": "25px", "height": "25px",
    },
    size_box={
        "color": "rgba(220, 230, 220, 1)", "margin": "0px",
        "padding": "2px", "top": "0px",
        "qproperty-alignment": "AlignRight",
        "border-top": "1px solid black",
        "min-width": "50px", "max-width": "50px",
        "width": "50px",
        "min-height": "25px", "max-height": "25px", "height": "25px",
    },
    size_bar={
        "min-height": "25px", "max-height": "25px", "height": "25px",
        "margin-left": "10px",
        "padding": "2px",
        "qproperty-alignment": "AlignLeft",
    },
    play_button={
        "min-width": "50px", "max-width": "50px",
        "min-height": "25px", "max-height": "25px", "margin-left": "5px"
    },
))

class PriceLevel(ed.Component):

    @ed.register_props
    def __init__(self, price, size, side, last=False):
        super().__init__()

    def render(self):
        if self.props.side == "bid":
            color = "rgba(50, 50, 255, 1)"
        else:
            color = "rgba(255, 50, 50, 1)"

        price_box_style = dict(stylesheet.price_box)
        size_box_style = dict(stylesheet.size_box)
        size_bar_style = dict(stylesheet.size_bar)

        size_box_style["background-color"] = color
        size_bar_style.update({
            "background-color": color,
            "min-width": "%spx" % (self.props.size / 5), "max-width": "%spx" % (self.props.size / 5)
        })
        if self.props.last:
            price_box_style["border-bottom"] = "1px solid black"
            size_box_style["border-bottom"] = "1px solid black"

        return ed.View(layout="row", style={"padding": "0px", "min-width": "100px", "align": "left"})(
            ed.Label(self.props.price, style=price_box_style).set_key("price"),
            ed.Label(self.props.size, style=size_box_style).set_key("size"),
            ed.Label("", style=size_bar_style).set_key("vis_size")
        )

class Book(ed.Component):

    @ed.register_props
    def __init__(self, book):
        pass

    def render(self):
        book = self.props.book
        sizes = book["sizes"]
        market_price = book["price"]
        return ed.View(layout="column", style={"margin": "10px", "padding": "0px"})(
            *[PriceLevel(price=p, size=sizes[p],
                         side="bid" if p < market_price else "ask",
                         last=(p==1)).set_key(str(p))
              for p in range(20, 0, -1)]
        )


class App(ed.Component):

    def __init__(self):
        super().__init__()
        self.book = {
            "price": 10,
            "sizes": [random.randint(100, 300) for _ in range(21)]
        }
        self.playing = False
        self.timer = ed.Timer(self.update_book)

    def update_book(self):
        with self.render_changes():
            self.book = {
                "price": 10,
                "sizes": [random.randint(100, 300) for _ in range(21)]
            }

    def will_unmount(self):
        self.timer.stop()

    def play(self):
        if self.playing:
            self.timer.stop()
        else:
            self.timer.start(50)
        self.set_state(playing=not self.playing)

    def render(self):
        return ed.View(layout="column")(
            ed.View(layout="row", style={"align": "left", "margin-left": "10px"})(
                ed.Icon(name="chart-line", size=14).set_key("Icon"),
                ed.Label("Market Data Viewer", style={"margin-left": "5px"} ).set_key("Label"),
                ed.IconButton(name="pause" if self.playing else "play",
                              style=stylesheet.play_button, size=10, on_click=self.play,
                ).set_key("Play"),
            ).set_key("Controls"),
            Book(self.book).set_key("Book"),
        )

if __name__ == "__main__":
    ed.app(App()).start()
