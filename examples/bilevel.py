import math

import aerobench.examples.gcas.gcas_autopilot as autopilot
import aerobench.run_f16_sim as f16_sim
import numpy as np

import staliro
import staliro.models as models
import staliro.optimizers as optimizers
import staliro.specifications as specifications

TSPAN = (0, 15)


@staliro.costfunc()
def outer(sample: staliro.Sample) -> float:
    @models.blackbox(step_size=0.1)
    def inner(inputs: models.Blackbox.Inputs) -> models.Trace[list[float]]:
        power = 9
        alpha = np.deg2rad(2.1215)
        beta = 0
        alt = sample.static["alt"]
        vel = 540
        phi = inputs.static["phi"]
        theta = inputs.static["theta"]
        psi = inputs.static["psi"]

        initial_state = [vel, alpha, beta, phi, theta, psi, 0, 0, 0, 0, 0, 0, alt, power]
        step = 1.0 / 30.0
        system = autopilot.GcasAutopilot(init_mode="roll", stdout=False)
        result = f16_sim.run_f16_sim(initial_state, TSPAN[1], system, step, extended_states=True)
        states = np.vstack(
            (
                np.array([0 if x == "standby" else 1 for x in result["modes"]]),
                result["states"][:, 4],  # roll
                result["states"][:, 5],  # pitch
                result["states"][:, 6],  # yaw
                result["states"][:, 12],  # altitude
            )
        )

        return models.Trace(times=result["times"], states=np.transpose(states).tolist())

    spec = specifications.rtamt.parse_dense("[] alt >= 0", {"alt": 0})
    optimizer = optimizers.UniformRandom[float]()
    options = staliro.TestOptions(
        runs=1,
        tspan=TSPAN,
        iterations=500,
        static_inputs={
            "phi": math.pi / 4 + np.array([-math.pi / 20, math.pi / 30]),
            "theta": -math.pi / 2 * 0.8 + np.array([0, math.pi / 20]),
            "psi": -math.pi / 4 + np.array([-math.pi / 8, math.pi / 8]),
        },
    )

    results = staliro.test(inner, spec, optimizer, options)
    result = results[0]

    return min(e.cost for e in result.evaluations)


if __name__ == "__main__":
    optimizer = optimizers.UniformRandom(min_cost=0.0)
    options = staliro.TestOptions(
        runs=1,
        iterations=100,
        static_inputs={"alt": (2200, 2500)},
    )

    results = staliro.test(outer, optimizer, options)
    result = results[0]
    min_cost = min(e.cost for e in result.evaluations)

    print(f"Minimum cost found: {min_cost}")
