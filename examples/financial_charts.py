"""An example financial data plotting application.

The application allows arbitrary number of plots (on the same axis).
For each plot, the x and y axis could represent any field of any stock.
Everything is reactive -- changes will automatically be reflected in the entire application.
"""

#
# pip install pandas yfinance matplotlib
#
# python examples/harmonic_oscillator.py
#

import sys, os
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
import asyncio
from collections import OrderedDict
import typing as tp
import edifice as ed
from edifice import Dropdown, IconButton, Label, ScrollView, Slider, TextInput, View
from edifice.components import plotting

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

# We create a component which describes the options for each axis (data source, transform).
# Since this component owns no state, we can simply write a render function and use the
# component decorator.
@ed.component
def AxisDescriptor(self, name, key, plot, plots_set): #TODO does plots_set change on every render?
    # We subscribe to app_state, so that state changes would trigger a re-render
    # Subscribe returns the data stored in app_state
    data = plot[f"{key}.data"]
    data_type, ticker = data
    transform = plot[f"{key}.transform"]
    transform_type, param = transform
    # We can use CSS styling. See https://pyedifice.github.io/styling.html
    row_style = {"align": "left", "width": 350}

    def handle_data_type(data_type_text):
        plot[f"{key}.data"] = (data_type_text, ticker)
        plots_set(lambda x: x)

    def handle_ticker(ticker_text):
        plot[f"{key}.data"] = (data_type, ticker_text)
        plots_set(lambda x: x)

    def handle_transform_type(transform_type_text):
        plot[f"{key}.transform"] = (transform_type_text, param)
        plots_set(lambda x: x)

    def handle_param(param_val):
        plot[f"{key}.transform"] = (transform_type, param_val)
        plots_set(lambda x: x)


    with View(layout="column"):
        with View(layout="row", style=row_style):
            Label(name, style={"width": 40})
            Dropdown(selection=data_type, options=["Date", "Close", "Volume"],
                     on_select=handle_data_type
            )
            if data_type != "Date":
                TextInput( text=ticker, style={"padding": 2},
                    on_change=handle_ticker
                )

        with View(layout="row", style=row_style):
            Label("Transform:", style={"width": 70})
            Dropdown(selection=transform_type, options=["None", "EMA"],
                     on_select=handle_transform_type)
            if transform == "EMA":
                Label(f"Half Life ({param} days)", style={"width": 120})
            if transform == "EMA":
                Slider(
                    value=param, min_value=1, max_value=90, dtype=int,
                    on_change=handle_param
                )


# We create a shorthand for creating a component with a label
def labeled_elem(label, comp):
    with View(layout="row", style={"align": "left"}):
        Label(label, style={"width": 80})
        comp()

def add_divider(comp):
    with View(layout="column"):
        comp()
        View(style={"height": 0, "border": "1px solid gray"})


# Now we make a component to describe the entire plot: the descriptions of both axis,
# plot type, and color
@ed.component
def PlotDescriptor(self, plot, plots_set):
    plot_type = plot["type"]
    color = plot["color"]

    def handle_plot_type(plot_type_text):
        plot["type"] = plot_type_text
        plots_set(lambda x: x)

    def handle_color(color_text):
        plot["color"] = color_text
        plots_set(lambda x: x)

    with View(layout="row", style={"margin": 5}):
        with View(layout="column", style={"align": "top"}):
            AxisDescriptor("x-axis", "xaxis", plot, plots_set)
            AxisDescriptor("y-axis", "yaxis", plot, plots_set)
        with View(layout="column", style={"align": "top", "margin-left": 10}):
            labeled_elem(
                "Chart type",
                lambda: Dropdown(selection=plot_type, options=["scatter", "line"],
                         on_select=handle_plot_type)
            )
            labeled_elem(
                "Color",
                lambda: Dropdown(
                    selection=color,
                    options=list(matplotlib.colors.CSS4_COLORS.keys()),
                    on_select=handle_color
                )
            )


# Finally, we create a component that contains the plot descriptions, a button to add a plot,
# and the actual Matplotlib figure.
@ed.component
def App(self):

    next_i, next_i_set = ed.use_state(int(1))
    # We're cheating a bit here with the plots state.
    # plots is a mutable dictionary, so we mutate the dictionary
    # and then call plots_set to notify Edifice that it changed.
    plots, plots_set = ed.use_state(OrderedDict([(int(0), _create_state_for_plot())]))

    # Adding a plot is very simple conceptually (and in Edifice).
    # Just add new state for the new plot!
    def add_plot(e):
        plots.update([(next_i, _create_state_for_plot())])
        next_i_set(lambda j: j+1)
        plots_set(plots) # sets to the same mutable OrderedDict

    # The Plotting function called by the plotting.Figure component.
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
            df = df.merge(pd.DataFrame({"ydata": get_data(ydf, ydata, ytransform, yparam)}, index=ydf.index),
                          left_index=True, right_index=True)
            if plot_type == "line":
                ax.plot(df.xdata, df.ydata, color=color)
            elif plot_type == "scatter":
                ax.scatter(df.xdata, df.ydata, color=color)

    with ed.Window(title="Financial Charts"):
        with View(layout="column", style={"margin": 10}):
            with ScrollView(layout="column"):
                for plot in plots.values():
                    add_divider(lambda: PlotDescriptor(plot, plots_set))

            # Edifice comes with Font-Awesome icons for your convenience
            IconButton(name="plus", title="Add Plot", on_click=add_plot)
            # We create a lambda fuction so that the method doesn't compare equal to itself.
            # This forces re-renders everytime this entire component renders.
            plotting.Figure(lambda ax: plot_figure(ax))


# Finally to start the the app, we pass the Element to the edifice.App object
# and call the start function to start the event loop.
if __name__ == "__main__":
    ed.App(App()).start()
