"""An example financial data plotting application."""

#
# python examples/financial_charts.py
#

from __future__ import annotations  # noqa: I001

import asyncio
import typing as tp
from collections import OrderedDict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, replace

import yfinance as yf

import edifice as ed
from edifice.extra.pyqtgraph_plot import PyQtPlot
from edifice.qt import QT_VERSION

import pyqtgraph as pg  # important: import pyqtgraph after edifice

if tp.TYPE_CHECKING:
    import pandas as pd

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QColor, QPen
    from PyQt6.QtWidgets import QApplication, QSizePolicy
else:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QPen
    from PySide6.QtWidgets import QApplication, QSizePolicy


@dataclass(frozen=True)
class PlotParams:
    """Dataclass to store the parameters of a plot."""

    x_ticker: str
    y_label: str  # "Close" "Volume"
    y_transform: tp.Literal["None", "EMA"]
    y_transform_param: int
    color: str


@dataclass
class Received:
    dataframe: pd.DataFrame

    def __bool__(self):
        """
        We need this to store a DataFrame in use_state because
        “ValueError: The truth value of a DataFrame is ambiguous.”
        """
        return True

    def __eq__(self, other):
        """
        We need this to store a DataFrame in use_state because
        “ValueError: The truth value of a DataFrame is ambiguous.”
        """
        return id(self) == id(other)


@dataclass(frozen=True)
class Failed:
    error: Exception


label_types = ["Date", "Close", "Volume"]
transform_types = ["None", "EMA"]


@ed.component
def PlotDescriptor(
    self,
    key: int,
    plot: PlotParams,
    plot_data: None | Received | Failed,
    plot_colors: list[str],
    plot_change: tp.Callable[[int, tp.Callable[[PlotParams], PlotParams]], None],
):
    """
    A component to render the UI for one plot.
    """

    def handle_color(color_index: int):
        plot_change(key, lambda p: replace(p, color=plot_colors[color_index]))

    def handle_ticker(ticker_text: str):
        plot_change(key, lambda p: replace(p, x_ticker=ticker_text.upper()))

    def handle_transform_type(transform_type_index: int):
        plot_change(key, lambda p: replace(p, y_transform=transform_types[transform_type_index]))

    def handle_param(param_val: int):
        plot_change(key, lambda p: replace(p, y_transform_param=param_val))

    with ed.HBoxView(style={"align": "left", "width": 300, "height": 100}):
        with ed.VBoxView(style={"align": "top"}):
            with ed.HBoxView(style={"align": "left"}):
                ed.TextInput(
                    text=plot.x_ticker,
                    style={
                        "padding": 2,
                        "width": 80,
                        "font-size": 25,
                    }
                    | ({"color": plot.color} if isinstance(plot_data, Received) else {}),
                    on_change=handle_ticker,
                )
                with ed.HBoxView(style={"padding-left": 10, "align": "left"}):
                    if isinstance(plot_data, Failed):
                        ed.Label(
                            f"No data for {plot.x_ticker}",
                            size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
                        )
                    elif isinstance(plot_data, Received):
                        ed.Dropdown(
                            selection=plot_colors.index(plot.color),
                            options=plot_colors,
                            on_select=handle_color,
                            size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
                            focus_policy=Qt.FocusPolicy.ClickFocus,
                        )
                    elif plot.x_ticker:
                        ed.Label(
                            text=f"Fetching {plot.x_ticker}...",
                            size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
                        )

            with ed.VBoxView(
                style={"align": "left", "padding-top": 5},
                size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
            ):
                if plot.x_ticker != "" and isinstance(plot_data, Received):
                    with ed.HBoxView(
                        style={"padding-right": 10, "align": "left"},
                    ):
                        ed.Label("Transform")
                        with ed.HBoxView(style={"padding-left": 10, "padding-right": 10, "align": "left"}):
                            ed.Dropdown(
                                selection=transform_types.index(plot.y_transform),
                                options=transform_types,
                                on_select=handle_transform_type,
                                size_policy=QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
                                focus_policy=Qt.FocusPolicy.ClickFocus,
                            )
                        if plot.y_transform == "EMA":
                            ed.Label(
                                text=f"half-life {plot.y_transform_param} days",
                                word_wrap=False,
                                tool_tip="Exponential Moving Average half-life",
                            )
                    with ed.HBoxView():
                        if plot.y_transform == "EMA":
                            ed.Slider(
                                value=plot.y_transform_param,
                                min_value=1,
                                max_value=90,
                                style={"min-width": 200},
                                on_change=handle_param,
                                tool_tip="Exponential Moving Average half-life",
                                focus_policy=Qt.FocusPolicy.ClickFocus,
                            )


def fetch_from_yahoo(ticker: str) -> pd.DataFrame:
    return yf.Ticker(ticker).history("1y")


# Finally, we create a component that contains the plot descriptions
# and the actual Matplotlib figure.
@ed.component
def App(self, plot_colors: list[str], plot_color_background: str):
    next_key, next_key_set = ed.use_state(1)

    def one_plot_aapl() -> OrderedDict[int, PlotParams]:
        return OrderedDict([(0, PlotParams("AAPL", "Close", "None", 30, plot_colors[0]))])

    # The plots are enter by the user in the UI.
    plots: OrderedDict[int, PlotParams]
    plots, plots_set = ed.use_state(one_plot_aapl)

    # The plot_data is what we fetch from Yahoo Finance.
    plot_data: dict[str, Received | Failed]
    plot_data, plot_data_set = ed.use_state(tp.cast(dict[str, Received | Failed], {}))

    def check_insert_blank_plot():
        """
        There should always be a blank ticker plot at the end of the list.
        If there isn't one already, add one.
        """
        if len(plots) == 0 or list(plots.values())[-1].x_ticker != "":
            plots_ = plots.copy()
            plots_.update({next_key: PlotParams("", "Close", "None", 30, plot_colors[next_key % len(plot_colors)])})
            next_key_set(lambda j: j + 1)
            plots_set(plots_)
        elif len(plots) > 1 and list(plots.values())[-2].x_ticker == "":
            # Else if the last two plots are blank then remove the last one.
            plots_ = plots.copy()
            plots_.popitem()
            plots_set(plots_)

    ed.use_effect(check_insert_blank_plot, plots)

    def plot_change(key: int, plot_setter: tp.Callable[[PlotParams], PlotParams]) -> None:
        plots_ = plots.copy()
        p = plots_[key]
        plots_.update([(key, plot_setter(p))])
        plots_set(plots_)

    tickers_needed: list[str] = [
        plot.x_ticker for plot in plots.values() if plot.x_ticker != "" and plot.x_ticker not in plot_data.keys()
    ]

    tickers_requested, tickers_requested_set = ed.use_state(tp.cast(list[str], []))

    fetch_executor = ed.use_memo(ProcessPoolExecutor)

    fetch_tasks, fetch_tasks_set = ed.use_state(tp.cast(list[asyncio.Task[None]], []))

    async def check_fetch_data():
        # If we need some ticker data and we don't have it yet, then
        # fetch it.
        for ticker in [t for t in tickers_needed if t not in tickers_requested]:
            tickers_requested_set(lambda tr_old, ticker=ticker: [*tr_old, ticker])
            try:
                data = await asyncio.get_event_loop().run_in_executor(fetch_executor, fetch_from_yahoo, ticker)
                if data.empty:
                    plot_data_set(lambda pltd, ticker=ticker: pltd | {ticker: Failed(Exception("No data"))})
                else:
                    plot_data_set(lambda pltd, ticker=ticker, data=data: pltd | {ticker: Received(data)})
            except Exception as e:  # noqa: BLE001
                plot_data_set(lambda pltd, ticker=ticker, e=e: pltd | {ticker: Failed(e)})

    def check_fetch_data_start():
        # We don't do
        #
        #     use_async(check_fetch_data, tickers_needed)
        #
        # because we don't want check_fetch_data to
        # be cancelled if it is called again before the last call finishes.

        # first reap the finished tasks
        fetch_tasks_set(lambda ft: [t for t in ft if not t.done()])
        # then start a new task
        t = asyncio.get_event_loop().create_task(check_fetch_data())
        fetch_tasks_set(lambda ft: [*ft, t])

    ed.use_effect(check_fetch_data_start, tickers_needed)

    def plot_fun(plot_item: pg.PlotItem):
        """
        The plotting function called by the PyQtPlot component.
        """

        plot_widget: pg.PlotWidget
        plot_widget = tp.cast(pg.PlotWidget, plot_item.getViewWidget())
        plot_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # type: ignore  # noqa: PGH003

        plot_item.setAxisItems(axisItems={"bottom": pg.DateAxisItem()})

        for plot in plots.values():
            match plot_data.get(plot.x_ticker, None):
                case Received(dataframe):
                    ys = (
                        dataframe[plot.y_label].ewm(halflife=plot.y_transform_param).mean()
                        if plot.y_transform == "EMA"
                        else dataframe[plot.y_label]
                    )
                    plot_item.plot(
                        # https://stackoverflow.com/questions/11865458/how-to-get-unix-timestamp-from-numpy-datetime64/45968949#45968949
                        x=[x.astype("datetime64[s]").astype("int") for x in dataframe.index.values],  # noqa: PD011
                        y=ys.values,
                        pen=pg.mkPen(QColor(plot.color), width=2),
                    )

    # render the UI
    with ed.VBoxView(style={"align": "top"}):
        with ed.VBoxView(style={"padding": 10}):
            with ed.FlowView():
                for key, plot in plots.items():
                    PlotDescriptor(key, plot, plot_data.get(plot.x_ticker, None), plot_colors, plot_change)

        with ed.VBoxView(
            style={
                "height": 500,
                "background-color": plot_color_background,
                "padding-top": 20,
                "padding-bottom": 20,
                "padding-left": 10,
                "padding-right": 10,
            },
            size_policy=QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed),
        ):
            PyQtPlot(
                plot_fun=plot_fun,
                focus_policy=Qt.FocusPolicy.ClickFocus,
            )


@ed.component
def Main(self):
    def initializer():
        qapp = tp.cast(QApplication, QApplication.instance())
        qapp.setApplicationName("Financial Charts")
        pg.setConfigOption("antialias", True)
        if ed.theme_is_light():
            plot_color_background = "white"
            pg.setConfigOption("foreground", "grey")
            pg.setConfigOption("background", "white")
            qapp.setPalette(ed.palette_edifice_light())
            plot_colors = [
                # https://matplotlib.org/stable/gallery/color/named_colors.html#css-colors
                "firebrick",
                "darkcyan",
                "darkred",
                "darkviolet",
                "darkturquoise",
                "darkmagenta",
                "darkgoldenrod",
            ]
        else:
            qapp.setPalette(ed.palette_edifice_dark())
            plot_color_background = "black"
            pg.setConfigOption("foreground", "grey")
            pg.setConfigOption("background", "black")
            plot_colors = [
                "coral",
                "peachpuff",
                "greenyellow",
                "palevioletred",
                "lime",
                "plum",
                "ivory",
            ]
        return plot_colors, plot_color_background

    plot_colors, plot_color_background = ed.use_memo(initializer)

    with ed.Window(title="Financial Charts", _size_open=(1024, 768)):
        App(plot_colors, plot_color_background)


# Finally to start the the app, we pass the Element to the edifice.App object
# and call the start function to start the event loop.
if __name__ == "__main__":
    ed.App(Main()).start()
