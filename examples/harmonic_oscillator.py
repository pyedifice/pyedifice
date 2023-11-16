#
# python examples/harmonic_oscillator.py
#

import sys, os
# We need this sys.path line for running this example, especially in VSCode debugger.
sys.path.insert(0, os.path.join(sys.path[0], '..'))
import asyncio
import edifice as ed

from edifice.components.matplotlib_figure import MatplotlibFigure
import numpy as np

from edifice.qt import QT_VERSION
if QT_VERSION == "PyQt6":
    from PyQt6 import QtWidgets
else:
    from PySide6 import QtWidgets

# We create time range once so we don't have to recreate it each plot
time_range = np.linspace(0, 10, num=120)

@ed.component
def Oscillator(self):
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
    angular_frequency, angular_frequency_set = ed.use_state(2)
    damping, damping_set = ed.use_state(-0.5)

    is_playing, is_playing_set = ed.use_state(False)
    play_trigger, play_trigger_set = ed.use_state(False)
    simulation_time, simulation_time_set = ed.use_state(0.0)
    dt = 0.03

    def plot(ax):
        # Plotting function, called by the Matplotlib component. This is standard matplotlib code.
        ax.plot(time_range, calculate_harmonic_motion(time_range))

    plot_fun, plot_fun_set = ed.use_state((lambda figure: plot(figure),))

    def calculate_harmonic_motion(t):
        # Formula for harmonic motion. We use complex numbers because the formula is nicer this way
        # (no special cases)
        sqrt_expr = np.ones([], dtype=complex) * damping ** 2 - 4 * angular_frequency ** 2
        complex_phase = (damping - np.sqrt(sqrt_expr)) / 2
        return np.real(np.exp(complex_phase * t))

    # Animation timer. It simply adds dt to simulation_time each tick
    async def play_tick():
        if is_playing:
            simulation_time_set(lambda t: t + dt)
            await asyncio.sleep(dt)
            play_trigger_set(lambda p: not p)

    ed.use_async(play_tick, (is_playing, play_trigger))

    def freq_slider_change(value):
        angular_frequency_set(value)
        simulation_time_set(0)
        plot_fun_set((lambda figure: plot(figure),))

    def damp_slider_change(value):
        damping_set(value)
        simulation_time_set(0)
        plot_fun_set((lambda figure: plot(figure),))

    with ed.View(layout="row"):
        with ed.View(layout="column", style={"margin": 10}):
            with ed.View(layout="row"):
                ed.IconButton("pause" if is_playing else "play",
                                on_click=lambda e: is_playing_set(lambda p: not p))
                ed.Button("Reset", on_click=lambda e: simulation_time_set(0))
            with ed.View():
                MatplotlibFigure(plot_fun[0])
            with ed.View(layout="row", style={"margin": 10}):
                ed.Label("Angular Frequency")
                ed.Slider(value=angular_frequency, min_value=1, max_value=10,
                            on_change=freq_slider_change)
                ed.Label("Damping Factor")
                ed.Slider(value=damping, min_value=-3, max_value=0,
                            on_change=damp_slider_change)

            # We position the ball and the centroid using absolute positioning.
            # The label and ball offsets are different since we have to take into
            # account the size of the ball
            with ed.View(layout="row", style={"align": "center"}):
                with ed.View(layout="none", style={"width": 720, "height": 10, "margin-top": 40}):
                    ed.Icon("bowling-ball", size=20, color=(255, 0, 0, 255),
                            style={"left": 350 +  200 * calculate_harmonic_motion(simulation_time)})
                    ed.Label("|", style={"left": 356, "font-size": 20, "color": "blue"})

@ed.component
def Main(self):
    with ed.Window("Harmonic Oscillator"):
        Oscillator()

if __name__ == "__main__":
    ed.App(Main()).start()
