"""An example financial data plotting application."""

#
# python examples/financial_charts.py
#
from __future__ import annotations

import multiprocessing
import typing as tp
from collections import OrderedDict
from dataclasses import dataclass, replace
from functools import partial

import matplotlib.pyplot as plt
import yfinance as yf

import edifice as ed
from edifice.extra.matplotlib_figure import MatplotlibFigure
from edifice.qt import QT_VERSION

if tp.TYPE_CHECKING:
    from multiprocessing.queues import Queue

    import pandas as pd
    from matplotlib.axes import Axes

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication, QSizePolicy
else:
    from PySide6.QtCore import Qt
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
                        "color": plot.color,
                        "font-size": 25,
                    },
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
                if plot.x_ticker != "":
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


async def fetch_subprocess(
    request_queue: Queue[str],
    response_callback: tp.Callable[[str, Failed | Received], None],
) -> None:
    """
    Synchronous subprocess function to fetch data from Yahoo Finance.
    It is async def because we will pass it to run_subprocess_with_callback.
    The whole point of this subprocess is that we can make an async call
    to the blocking function .history() in the yfinance API without blocking
    the GUI.
    """
    while True:
        ticker = request_queue.get()
        try:
            response_callback(ticker, Received(yf.Ticker(ticker).history("1y")))
        except Exception as e:  # noqa: BLE001
            response_callback(ticker, Failed(e))


# Finally, we create a component that contains the plot descriptions
# and the actual Matplotlib figure.
@ed.component
def App(self, plot_colors: list[str]):
    next_i, next_i_set = ed.use_state(1)

    def initializer() -> OrderedDict[int, PlotParams]:
        return OrderedDict([(0, PlotParams("AAPL", "Close", "None", 30, plot_colors[0]))])

    # The plots are enter by the user in the UI.
    plots: OrderedDict[int, PlotParams]
    plots, plots_set = ed.use_state(initializer)

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
            plots_.update({next_i: PlotParams("", "Close", "None", 30, plot_colors[next_i % len(plot_colors)])})
            next_i_set(lambda j: j + 1)
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

    ticker_queue: Queue[str] = ed.use_memo(lambda: multiprocessing.get_context("spawn").Queue())

    def receive_data(ticker: str, data: Failed | Received):
        match data:
            case Failed():
                plot_data_set(lambda pltd: pltd | {ticker: data})
            case Received(dataframe):
                if dataframe.empty:
                    plot_data_set(lambda pltd: pltd | {ticker: Failed(Exception("No data"))})
                else:
                    plot_data_set(lambda pltd: pltd | {ticker: data})

    async def wrap_fetch_subprocess() -> None:
        await ed.run_subprocess_with_callback(
            partial(fetch_subprocess, ticker_queue),
            receive_data,
        )

    ed.use_async(
        # The fetch_subprocess will run forever while this component is mounted.
        wrap_fetch_subprocess,
        # Why do we need wrap_fetch_subprocess? Is that a problem with the API?
        # Why can't we do here:
        #
        # > ed.run_subprocess_with_callback(
        # >     partial(fetch_subprocess, ticker_queue),
        # >     receive_data,
        # > )
    )

    tickers_needed: list[str] = [
        plot.x_ticker for plot in plots.values() if plot.x_ticker != "" and plot.x_ticker not in plot_data.keys()
    ]

    def check_fetch_data():
        if len(tickers_needed) > 0:
            # If we need some ticker data and we don't have it yet, then
            # fetch the first one that we need.
            ticker_queue.put(tickers_needed[0])

    # Call fetch_data whenever the first in the list of tickers needed changes
    ed.use_effect(check_fetch_data, tickers_needed[0:1])

    # The Plotting function called by the MatplotlibFigure component.
    # The plotting function is passed a Matplotlib axis object.
    def plot_figure(ax: Axes):
        for plot in plots.values():
            plot_datum = plot_data.get(plot.x_ticker, None)
            if isinstance(plot_datum, Received):
                if plot.y_transform == "EMA":
                    ax.plot(
                        plot_datum.dataframe.index,
                        plot_datum.dataframe[plot.y_label].ewm(halflife=plot.y_transform_param).mean(),
                        color=plot.color,
                    )
                else:
                    ax.plot(plot_datum.dataframe.index, plot_datum.dataframe[plot.y_label], color=plot.color)

    with ed.VBoxView(style={"align": "top"}):
        with ed.VBoxView(style={"padding": 10}):
            with ed.FlowView():
                for key, plot in plots.items():
                    PlotDescriptor(key, plot, plot_data.get(plot.x_ticker, None), plot_colors, plot_change)

        with ed.VBoxView(style={"height": 500, "margin-top": 10}):
            MatplotlibFigure(plot_figure)


@ed.component
def Main(self):
    def initializer():
        qapp = tp.cast(QApplication, QApplication.instance())
        qapp.setApplicationName("Financial Charts")
        if ed.theme_is_light():
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
            plot_colors = [
                "coral",
                "peachpuff",
                "greenyellow",
                "palevioletred",
                "lime",
                "plum",
                "ivory",
            ]
            plt.style.use("dark_background")
        return plot_colors

    plot_colors = ed.use_memo(initializer)

    with ed.Window(title="Financial Charts", _size_open=(1024, 768)):
        App(plot_colors)


# Finally to start the the app, we pass the Element to the edifice.App object
# and call the start function to start the event loop.
if __name__ == "__main__":
    ed.App(Main()).start()
