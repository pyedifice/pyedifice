#
# python examples/harmonic_oscillator.py
#

import asyncio
import logging
import typing as tp

import numpy as np

# Import edifice before importing pyqtgraph so that pyqtgraph detects the same version of PyQt
import edifice as ed
from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtGui, QtWidgets
else:
    from PySide6 import QtGui, QtWidgets

import pyqtgraph as pg

from edifice.extra.pyqtgraph_plot import PyQtPlot

pg.setConfigOption("antialias", True)

logger = logging.getLogger("Edifice")
logger.setLevel(logging.INFO)

# We create time range once so we don't have to recreate it each plot
time_range = np.linspace(0, 10, num=200)


@ed.component
def Oscillator(self, palette: QtGui.QPalette):
    """
    The high level logic is: there are two sets of state, spring parameters, and simulation parameters.
    The spring parameters can be changed by a slider for each of the parameters.
    The simulation parameters can be changed by a timer (updating simulation time),
    a play/pause button (toggling if the simulation is running), a reset button (setting simulation time to 0),
    and spring parameter changes (resets the simulation time).
    Each UI component reflects this state in a straightforward manner: sliders should be set to the current parameters,
    graph should plot using the current spring parameters, and the position of the ball should be calculated
    based on current simulation time.
    """

    # Spring parameters: frequency and damping factor. Damping must be negative
    angular_frequency, angular_frequency_set = ed.use_state(2.0)
    damping, damping_set = ed.use_state(-0.5)

    is_playing, is_playing_set = ed.use_state(False)
    simulation_time, simulation_time_set = ed.use_state(0.0)
    dt = 0.02

    def plot(plot_item: pg.PlotItem):
        plot_item.setMouseEnabled(x=False, y=False)  # type: ignore  # noqa: PGH003
        plot_item.hideButtons()
        pen = pg.mkPen(width=3, color=palette.color(QtGui.QPalette.ColorRole.BrightText))
        plot_item.setRange(xRange=[0, 10], yRange=[-1, 1])  # type: ignore  # noqa: PGH003
        plot_item.plot(time_range, calculate_harmonic_motion(time_range), pen=pen)

    plot_fun, plot_fun_set = ed.use_state((lambda figure: plot(figure),))

    def calculate_harmonic_motion(t):
        # Formula for harmonic motion. We use complex numbers because the formula is nicer this way
        # (no special cases)
        sqrt_expr = np.ones([], dtype=complex) * damping**2 - 4 * angular_frequency**2
        complex_phase = (damping - np.sqrt(sqrt_expr)) / 2
        return np.real(np.exp(complex_phase * t))

    # Animation timer. Adds dt to simulation_time each tick
    async def play_tick():
        if is_playing:
            while True:
                simulation_time_set(lambda t: t + dt)
                await asyncio.sleep(dt)

    ed.use_async(play_tick, is_playing)

    def freq_slider_change(value):
        angular_frequency_set(float(value) / 20.0)
        simulation_time_set(0)
        plot_fun_set((lambda figure: plot(figure),))

    def damp_slider_change(value):
        damping_set(float(value) / 100.0)
        simulation_time_set(0)
        plot_fun_set((lambda figure: plot(figure),))

    owidth = 800
    oheight = 600

    shadowcolor = palette.color(QtGui.QPalette.ColorRole.Light)
    shadowcolor.setAlpha(220)

    with ed.HBoxView():
        with ed.FixView(style={"width": owidth, "height": oheight}):
            with ed.VBoxView(style={"width": owidth, "height": oheight}):
                PyQtPlot(plot_fun=plot_fun[0])
            with ed.HBoxView(style={"align": "center"}):
                with ed.FixView(style={"width": owidth, "height": oheight, "margin-top": 40}):
                    ed.Label(
                        text="🟠",
                        style={
                            "top": oheight
                            - 25
                            - (oheight / 2)
                            - (oheight * 0.45 * calculate_harmonic_motion(simulation_time)),
                            "left": 50,
                            "font-size": 30,
                            "font-family": "Noto Color Emoji",
                        },
                    )
            with ed.HBoxView(
                style={
                    "top": 15,
                    "left": 550,
                    "width": 200,
                    "background-color": shadowcolor,
                    "border-radius": 30,
                    "padding-left": 30,
                    "padding-right": 30,
                    "padding-top": 20,
                    "padding-bottom": 20,
                },
            ):
                with ed.ButtonView(
                    on_trigger=lambda _: is_playing_set(lambda p: not p),
                    size_policy=QtWidgets.QSizePolicy(
                        QtWidgets.QSizePolicy.Policy.Fixed,
                        QtWidgets.QSizePolicy.Policy.Fixed,
                    ),
                    style={
                        "padding": 6,
                    },
                ):
                    ed.Label(
                        text="⏸️" if is_playing else "▶️",
                        style={
                            "font-size": 40,
                            "font-family": "Noto Color Emoji",
                            "height": 40,
                        },
                    )
                with ed.ButtonView(
                    on_trigger=lambda _: simulation_time_set(0),
                    size_policy=QtWidgets.QSizePolicy(
                        QtWidgets.QSizePolicy.Policy.Fixed,
                        QtWidgets.QSizePolicy.Policy.Fixed,
                    ),
                    style={
                        "padding": 6,
                    },
                ):
                    ed.Label(
                        text="🔁",
                        style={
                            "font-size": 40,
                            "font-family": "Noto Color Emoji",
                            "height": 40,
                        },
                    )
            with ed.VBoxView(
                style={
                    "top": 120,
                    "left": 550,
                    "width": 200,
                    "background-color": shadowcolor,
                    "border-radius": 30,
                    "padding": 30,
                },
            ):
                ed.Label(
                    text="Angular Frequency",
                    style={"color": palette.color(QtGui.QPalette.ColorRole.BrightText)},
                )
                ed.Slider(
                    value=int(angular_frequency * 20.0),
                    min_value=20,
                    max_value=200,
                    on_change=freq_slider_change,
                )
            with ed.VBoxView(
                style={
                    "top": 220,
                    "left": 550,
                    "width": 200,
                    "background-color": shadowcolor,
                    "border-radius": 30,
                    "padding": 30,
                },
            ):
                ed.Label(
                    text="Damping Factor",
                    style={"color": palette.color(QtGui.QPalette.ColorRole.BrightText)},
                )
                ed.Slider(value=int(damping * 100.0), min_value=-300, max_value=0, on_change=damp_slider_change)


@ed.component
def Main(self):
    def initializer():
        qapp = tp.cast(QtWidgets.QApplication, QtWidgets.QApplication.instance())
        qapp.setApplicationName("Harmonic Oscillator")
        if ed.theme_is_light():
            palette = ed.palette_edifice_light()
        else:
            palette = ed.palette_edifice_dark()
        qapp.setPalette(palette)
        pg.setConfigOption("background", palette.color(QtGui.QPalette.ColorRole.Window).name())
        pg.setConfigOption("foreground", palette.color(QtGui.QPalette.ColorRole.Text).name())
        return palette

    palette = ed.use_memo(initializer)

    with ed.Window(title="Harmonic Oscillator", _size_open=(1, 500)):
        Oscillator(palette)


if __name__ == "__main__":
    ed.App(Main()).start()
