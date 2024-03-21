from enum import IntEnum

from staliro import TestOptions, models, optimizers, specifications, staliro


class System:
    class Mode(IntEnum):
        HEATING = 1
        COOLING = 2

    def __init__(self, initial_temp: float):
        self.temp = initial_temp
        self.mode = System.Mode.COOLING

    def step(self, step_size: float) -> None:
        if self.temp < 19.0:
            self.mode = System.Mode.HEATING

        if self.temp > 21.0:
            self.mode = System.Mode.COOLING

        x_dot = 1.0 * self.temp

        if self.mode is System.Mode.HEATING:
            x_dot = 5.0 - x_dot

        self.temp = self.temp - x_dot * step_size


@models.blackbox()
def blackbox(inputs: models.Blackbox.Inputs) -> models.Trace[list[float]]:
    system = System(inputs.static["temp"])
    states = {}
    step_size = 0.1

    for step in range(100):
        time = step * step_size
        states[time] = [system.temp]
        system.step(step_size)

    return models.Trace(states)


if __name__ == "__main__":
    req = specifications.RTAMTDense("always (temp >= 18.0)", {"temp": 0})
    optimizer = optimizers.UniformRandom()
    options = TestOptions(
        runs=1,
        iterations=10,
        static_parameters={"temp": (18.0, 22.0)},
    )

    runs = staliro(blackbox, req, optimizer, options)
