"""
Clinical outcome simulator — Kaplan-Meier estimator + log-rank test, ported
from the frontend's JS implementation. The statistical methods are real; the
underlying survival times are SIMULATED (exponential distribution), not real
patient outcomes.
"""
import math
import random
from typing import List, Tuple


def erfc(x: float) -> float:
    """Abramowitz & Stegun 7.1.26 approximation (same one used in the frontend)."""
    t = 1 / (1 + 0.3275911 * abs(x))
    y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t
              - 0.284496736) * t + 0.254829592) * t * math.exp(-x * x)
    return 1 - y if x >= 0 else 1 + y


def chi2_survival_p(x: float) -> float:
    """Exact for 1 degree of freedom via the chi-square <-> normal identity:
    P(chi2_1 > x) = erfc(sqrt(x/2))."""
    return erfc(math.sqrt(max(x, 0) / 2))


def simulate_exponential(rate: float, rng: random.Random) -> float:
    return -math.log(1 - rng.random()) / rate


def kaplan_meier(times: List[float], events: List[int]):
    pairs = sorted(zip(times, events), key=lambda p: p[0])
    n0 = len(times)
    at_risk = n0
    surv = 1.0
    curve = [{"t": 0.0, "s": 1.0}]
    i = 0
    while i < len(pairs):
        t = pairs[i][0]
        deaths = censored = 0
        while i < len(pairs) and pairs[i][0] == t:
            if pairs[i][1]:
                deaths += 1
            else:
                censored += 1
            i += 1
        if deaths > 0:
            surv *= (1 - deaths / at_risk)
        at_risk -= (deaths + censored)
        curve.append({"t": t, "s": surv})
    return curve


def log_rank_test(times_a, events_a, times_b, events_b):
    all_rows = sorted(
        [(t, e, 0) for t, e in zip(times_a, events_a)] +
        [(t, e, 1) for t, e in zip(times_b, events_b)],
        key=lambda r: r[0]
    )
    n_a, n_b = len(times_a), len(times_b)
    o_minus_e = 0.0
    v = 0.0
    i = 0
    while i < len(all_rows):
        t = all_rows[i][0]
        d_a = d_b = c_a = c_b = 0
        while i < len(all_rows) and all_rows[i][0] == t:
            _, e, g = all_rows[i]
            if g == 0:
                d_a += e; c_a += (1 - e)
            else:
                d_b += e; c_b += (1 - e)
            i += 1
        d_tot = d_a + d_b
        n_tot = n_a + n_b
        if n_tot > 1 and d_tot > 0:
            expected_a = d_tot * (n_a / n_tot)
            variance = d_tot * (n_a / n_tot) * (n_b / n_tot) * ((n_tot - d_tot) / (n_tot - 1))
            o_minus_e += (d_a - expected_a)
            v += variance
        n_a -= (d_a + c_a)
        n_b -= (d_b + c_b)
    chi2 = (o_minus_e * o_minus_e) / v if v > 0 else 0.0
    return {"chi2": chi2, "p": chi2_survival_p(chi2)}


def run_simulation(efficacy: float, n_per_arm: int = 40, followup_months: int = 24,
                    control_hazard: float = 0.055, seed: int = None):
    rng = random.Random(seed)
    treat_hazard = control_hazard * (1 - efficacy)

    def arm(rate):
        times, events = [], []
        for _ in range(n_per_arm):
            t = simulate_exponential(rate, rng)
            if t > followup_months:
                times.append(followup_months); events.append(0)
            else:
                times.append(t); events.append(1)
        return times, events

    ctl_t, ctl_e = arm(control_hazard)
    tx_t, tx_e = arm(treat_hazard)

    km_ctl = kaplan_meier(ctl_t, ctl_e)
    km_tx = kaplan_meier(tx_t, tx_e)
    stats = log_rank_test(tx_t, tx_e, ctl_t, ctl_e)

    return {
        "treatment_hazard": treat_hazard,
        "control_hazard": control_hazard,
        "km_treatment": km_tx,
        "km_control": km_ctl,
        "log_rank_chi2": stats["chi2"],
        "log_rank_p": stats["p"],
        "followup_months": followup_months,
        "n_per_arm": n_per_arm,
    }
