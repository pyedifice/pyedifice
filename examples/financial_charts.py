"""An example financial data plotting application.

The application allows arbitrary number of plots (on the same axis).
For each plot, the x and y axis could represent any field of any stock.
Everything is reactive -- changes will automatically be reflected in the entire application.
"""

#
# python examples/financial_charts.py
#

from collections import OrderedDict
import typing as tp
import edifice as ed
from edifice import Dropdown, IconButton, Label, Slider, TextInput, View
from edifice.extra.matplotlib_figure import MatplotlibFigure

import matplotlib.colors
import pandas as pd
import yfinance as yf


def _create_state_for_plot() -> dict[str, tp.Any]:
    """Creates the default params associated with a plot."""
    return {
        # Data to show on x-axis (data type, data source)
        "xaxis.data": ("Date", "AAPL"),
        # Transformation applied to x-axis (transform type, transform param)
        "xaxis.transform": ("None", 30),
        "yaxis.data": ("Close", "AAPL"),
        "yaxis.transform": ("None", 30),
        # Plot type (line or scatter) and plot color
        "type": "line",
        "color": "peru",
    }


data_types = ["Date", "Close", "Volume"]
transform_types = ["None", "EMA"]


# We create a component which describes the options for each axis (data source, transform).
@ed.component
def AxisDescriptor(
    self,
    name,
    key,
    plot,
    plot_change: tp.Callable[[dict[str, tp.Any]], None],
):
    data = plot[f"{key}.data"]
    data_type, ticker = data
    data_type_selection: int = data_types.index(data_type)
    transform = plot[f"{key}.transform"]
    transform_type, param = transform
    transform_type_selection: int = transform_types.index(transform_type)

    # We can use CSS styling. See https://pyedifice.github.io/styling.html
    row_style = {"align": "left", "width": 350}

    def handle_data_type(data_type_index: int):
        plot_ = plot.copy()
        plot_[f"{key}.data"] = (data_types[data_type_index], ticker)
        plot_change(plot_)

    def handle_ticker(ticker_text):
        plot_ = plot.copy()
        plot_[f"{key}.data"] = (data_type, ticker_text)
        plot_change(plot_)

    def handle_transform_type(transform_type_index: int):
        plot_ = plot.copy()
        plot_[f"{key}.transform"] = (transform_types[transform_type_index], param)
        plot_change(plot_)

    def handle_param(param_val):
        plot_ = plot.copy()
        plot_[f"{key}.transform"] = (transform_type, param_val)
        plot_change(plot_)

    with View(layout="column").render():
        with View(layout="row", style=row_style).render():
            Label(name, style={"width": 100}).render()
            Dropdown(
                selection=data_type_selection,
                options=data_types,
                on_select=handle_data_type,
            ).render()
            if data_type != "Date":
                TextInput(text=ticker, style={"padding": 2}, on_change=handle_ticker).render()

        with View(layout="row", style=row_style).render():
            Label("Transform:", style={"width": 100}).render()
            Dropdown(
                selection=transform_type_selection,
                options=transform_types,
                on_select=handle_transform_type,
            ).render()
            if transform_type == "EMA":
                Label(f"Half Life ({param} days)", style={"width": 120}).render()
            if transform_type == "EMA":
                Slider(value=param, min_value=1, max_value=90, on_change=handle_param).render()


# We create a shorthand for creating a component with a label
def labeled_elem(label, comp):
    with View(layout="row", style={"align": "left"}).render():
        Label(label, style={"width": 100}).render()
        comp().render()


def add_divider(comp):
    with View(layout="column").render():
        comp().render()
        View(style={"height": 0, "border": "1px solid gray"}).render()


plot_types = ["scatter", "line"]
# https://matplotlib.org/stable/api/colors_api.html#exported-colors
plot_colors = list(matplotlib.colors.CSS4_COLORS.keys())


# Now we make a component to describe the entire plot: the descriptions of both axis,
# plot type, and color
@ed.component
def PlotDescriptor(self, plot: dict[str, tp.Any], plot_change: tp.Callable[[dict[str, tp.Any]], None]):
    plot_type = plot_types.index(plot["type"])
    color = plot_colors.index(plot["color"])

    def handle_plot_type(plot_type_index: int):
        plot_ = plot.copy()
        plot_["type"] = plot_types[plot_type_index]
        plot_change(plot_)

    def handle_color(color_index: int):
        plot_ = plot.copy()
        plot_["color"] = plot_colors[color_index]
        plot_change(plot_)

    with View(layout="row", style={"margin": 5, "align": "left"}).render():
        with View(layout="column", style={"align": "top", "width": 400}).render():
            AxisDescriptor("x-axis", "xaxis", plot, plot_change).render()
            AxisDescriptor("y-axis", "yaxis", plot, plot_change).render()
        with View(layout="column", style={"align": "top", "margin-left": 10}).render():
            labeled_elem(
                "Chart type", lambda: Dropdown(selection=plot_type, options=plot_types, on_select=handle_plot_type)
            )
            labeled_elem("Color", lambda: Dropdown(selection=color, options=plot_colors, on_select=handle_color))


# Finally, we create a component that contains the plot descriptions, a button to add a plot,
# and the actual Matplotlib figure.
@ed.component
def App(self):
    next_i, next_i_set = ed.use_state(int(1))
    plots, plots_set = ed.use_state(OrderedDict([(int(0), _create_state_for_plot())]))

    # Adding a plot is very simple conceptually (and in Edifice).
    # Just add new state for the new plot!
    # The state is immutable, so we need to create a new state object
    # with a shallow copy of the old state and the new plot.
    def add_plot(e):
        plots_ = plots.copy()
        plots_.update({next_i: _create_state_for_plot()})
        next_i_set(lambda j: j + 1)
        plots_set(plots_)

    # The Plotting function called by the MatplotlibFigure component.
    # The plotting function is passed a Matplotlib axis object.
    def plot_figure(ax):
        def get_data(df, label, transform, param):
            if label == "Date":
                return df.index
            if transform == "None":
                return df[label]
            return df[label].ewm(halflife=param).mean()

        for plot in plots.values():
            xdata, xticker = plot["xaxis.data"]
            xtransform, xparam = plot["xaxis.transform"]
            ydata, yticker = plot["yaxis.data"]
            ytransform, yparam = plot["yaxis.transform"]
            plot_type = plot["type"]
            color = plot["color"]

            # TODO fetch data asynchronously with use_async
            xdf = yf.Ticker(xticker).history("1y")
            ydf = yf.Ticker(yticker).history("1y")

            df = pd.DataFrame({"xdata": get_data(xdf, xdata, xtransform, xparam)}, index=xdf.index)
            df = df.merge(
                pd.DataFrame({"ydata": get_data(ydf, ydata, ytransform, yparam)}, index=ydf.index),
                left_index=True,
                right_index=True,
            )
            if plot_type == "line":
                ax.plot(df.xdata, df.ydata, color=color)
            elif plot_type == "scatter":
                ax.scatter(df.xdata, df.ydata, color=color)

    with View(layout="column", style={"margin": 10, "align": "top"}).render():
        with View(layout="column").render():
            for key, plot in plots.items():

                def plot_change(p: dict[str, tp.Any]) -> None:
                    plots_ = plots.copy()
                    plots_.update([(key, p)])
                    plots_set(plots_)

                add_divider(lambda: PlotDescriptor(plot, plot_change))
            # Edifice comes with Font-Awesome icons for your convenience
            IconButton(name="plus", title="Add Plot", on_click=add_plot)

        with View(style={"height": 500, "margin-top": 10}).render():
            MatplotlibFigure(plot_figure).render()


@ed.component
def Main(self):
    with ed.Window(title="Financial Charts").render():
        App().render()


# Finally to start the the app, we pass the Element to the edifice.App object
# and call the start function to start the event loop.
if __name__ == "__main__":
    ed.App(Main()).start()
