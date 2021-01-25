import edifice as ed

from edifice.components import plotting
import numpy as np


class Oscillator(ed.Component):
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

    def __init__(self):
        super().__init__()
        # Spring parameters: frequency and damping factor. Damping must be negative
        self.angular_frequency = 2
        self.damping = -0.5

        # We create time range once so we don't have to recreate it each plot
        self.time_range = np.linspace(0, 10, num=120)
        self.is_playing = False
        self.simulation_time = 0
        self.dt = 0.03

        # Animation timer. It simply adds dt to self.simulation_time each tick
        self.timer = ed.Timer(lambda: self.set_state(simulation_time=self.simulation_time + self.dt))

    def plot(self, ax):
        # Plotting function, called by the Matplotlib component. This is standard matplotlib code.
        ax.plot(self.time_range, self.calculate_harmonic_motion(self.time_range))

    def calculate_harmonic_motion(self, t):
        # Formula for harmonic motion. We use complex numbers because the formula is nicer this way
        # (no special cases)
        sqrt_expr = np.ones([], dtype=complex) * self.damping ** 2 - 4 * self.angular_frequency ** 2
        complex_phase = (self.damping - np.sqrt(sqrt_expr)) / 2
        return np.real(np.exp(complex_phase * t))

    def did_render(self):
        # Based on the is_playing status, we check whether or not to start or stop the timer.
        if self.is_playing:
            self.timer.start(int(self.dt * 1000))
        else:
            self.timer.stop()

    def will_dismount(self):
        # Cleanup function
        self.timer.stop()

    def render(self):
        return ed.View(layout="row")(
            ed.View(layout="column", style={"width": 720, "margin": 10}) (
                ed.View(layout="row")(
                    ed.IconButton("pause" if self.is_playing else "play",
                                  on_click=lambda e: self.set_state(is_playing=not self.is_playing)),
                    ed.Button("Reset", on_click=lambda e: self.set_state(simulation_time=0)),
                ),
                plotting.Figure(lambda figure: self.plot(figure)),
                ed.View(layout="row", style={"margin": 10})(
                    ed.Label("Angular Frequency"),
                    ed.Slider(value=self.angular_frequency, min_value=1, max_value=10,
                              on_change=lambda value: self.set_state(angular_frequency=value, simulation_time=0)),
                    ed.Label("Damping Factor"),
                    ed.Slider(value=self.damping, min_value=-3, max_value=0,
                              on_change=lambda value: self.set_state(damping=value, simulation_time=0)),
                ),
                # We position the ball and the centroid using absolute positioning.
                # The label and ball offsets are different since we have to take into-account the size of the ball
                ed.View(layout="none", style={"width": 720, "height": 10, "margin-top": 40}) (
                    ed.Icon("bowling-ball", size=20, color=(255, 0, 0, 255),
                            style={"left": 350 +  200 * self.calculate_harmonic_motion(self.simulation_time)}),
                    ed.Label("|", style={"left": 356, "font-size": 20, "color": "blue"}),
                )
            )
        )


if __name__ == "__main__":
    ed.App(Oscillator()).start()
