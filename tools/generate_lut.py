import math
import json
from pathlib import Path
from typing import List, Tuple

MATH = Path(__file__).resolve().parents[1] / 'math'

# Helpers
def clamp(x, a, b):
    return max(a, min(b, x))


# Base mode: truncated Pareto (alpha=1.0) over [mmin, mmax]
def base_quantile(u: float, mmin: float, mmax: float, alpha: float = 1.0) -> float:
    a = alpha
    # Truncated Pareto on [mmin, mmax]
    A = (mmin / mmax) ** a
    # Target CDF on [0,1): u = (1 - (mmin/m)^a) / (1 - A)
    # => (mmin/m)^a = A + (1 - u)*(1 - A)
    inner = A + (1.0 - u) * (1.0 - A)
    return mmin / max(inner, 1e-12) ** (1.0 / a)


def base_expected(mmin: float, mmax: float, samples: int = 8192) -> float:
    # numeric expectation under the quantile mapping above (alpha=1)
    s = 0.0
    for i in range(samples):
        u = (i + 0.5) / samples
        s += base_quantile(u, mmin, mmax)
    return s / samples


# Elevate mode: piecewise power-law survival with guided tail rarity
class PiecewisePareto:
    def __init__(self, knots, surv):
        # knots: list of m values (ascending)
        # surv: survival at those knots (relative, S(knots[0]) = 1.0)
        assert len(knots) == len(surv)
        self.knots = knots
        self.surv = surv
        # precompute segment alphas so that S(b) = S(a) * (a/b)^alpha
        self.alphas = []
        for i in range(len(knots) - 1):
            a, b = knots[i], knots[i + 1]
            Sa, Sb = surv[i], surv[i + 1]
            # Sa -> Sb = Sa * (a/b)^alpha => alpha = ln(Sb/Sa) / ln(a/b)
            alpha = math.log(Sb / Sa) / math.log(a / b)
            self.alphas.append(alpha)
        # total mass in positive payouts is 1 (since S(knots[0]) normalized)
        self.segment_mass = []
        for i in range(len(knots) - 1):
            a, b = knots[i], knots[i + 1]
            Sa, Sb = surv[i], surv[i + 1]
            self.segment_mass.append(Sa - Sb)
        self.total_mass = self.segment_mass[0]
        for m in self.segment_mass[1:]:
            self.total_mass += m

    def quantile(self, u: float) -> float:
        # u in [0,1) over positive-payout mass
        # find segment
        cum = 0.0
        for i in range(len(self.knots) - 1):
            a, b = self.knots[i], self.knots[i + 1]
            Sa, Sb = self.surv[i], self.surv[i + 1]
            seg = (Sa - Sb)
            if u <= cum + seg:
                # within segment i
                du = (u - cum) / seg if seg > 0 else 0.0
                # target survival S = Sa - du*(Sa - Sb)
                S = Sa - du * (Sa - Sb)
                alpha = self.alphas[i]
                # S = Sa * (a/m)^alpha => m = a * (Sa/S)^(1/alpha)
                m = a * (Sa / max(S, 1e-15)) ** (1.0 / alpha)
                return clamp(m, a, b)
            cum += seg
        return self.knots[-1]

    def expected(self, samples: int = 8192) -> float:
        s = 0.0
        for i in range(samples):
            u = (i + 0.5) / samples
            s += self.quantile(u * self.total_mass)
        return s / samples


def _normalize_to_int_weights(probs: List[float], scale: int = 10_000_000) -> List[int]:
    raw = [p * scale for p in probs]
    ints = [int(round(x)) for x in raw]
    s = sum(ints)
    if s == 0:
        # fallback to at least 1 per non-zero prob index
        ints = [1 if p > 0 else 0 for p in probs]
        s = sum(ints)
    # Adjust by distributing the difference
    diff = scale - s
    if diff != 0:
        # adjust the largest probabilities first
        order = sorted(range(len(probs)), key=lambda i: probs[i], reverse=True)
        i = 0
        while diff != 0 and i < len(order):
            idx = order[i]
            step = 1 if diff > 0 else -1
            newv = ints[idx] + step
            if newv >= 0:
                ints[idx] = newv
                diff -= step
            i = (i + 1) % len(order)
    return ints


def build_lookup_and_events(mode: str, payouts: list, target_rtp: float, cost: float, out_csv: Path, out_jsonl: Path, mmin: float, mmax: float):
    # Build 256-entry LUT using integer weights; design positive mass shape first
    N = 256
    N_ZERO = 64  # number of explicit zero rows (weights control real probability)
    N_POS = N - N_ZERO

    # Probability allocation across rows
    probs: List[float] = []
    payouts_rows: List[int] = []

    # Positive rows: select representative payouts via quantiles
    # and allocate relative weights w_j ~ (j+1)^-gamma to emphasize low multipliers
    gamma = 3.0 if mode == 'base' else 4.0
    w_raw: List[float] = []
    m_list: List[float] = []
    for j in range(N_POS):
        t = (j + 0.5) / N_POS
        idx = min(int(t * (len(payouts) - 1)), len(payouts) - 1)
        m = payouts[idx]
        m_list.append(m)
        w_raw.append((j + 1) ** (-gamma))

    w_sum = sum(w_raw)
    # Discrete positive expectation under our row weights
    E_pos_discrete = sum(w * m for w, m in zip(w_raw, m_list)) / max(w_sum, 1e-12)

    # Compute zero mass required for target RTP
    target_ev = target_rtp * cost
    p_zero = 1.0 - (target_ev / max(E_pos_discrete, 1e-12))
    p_zero = clamp(p_zero, 0.0, 0.9999999999)

    # Zeros equally split across N_ZERO rows
    for _ in range(N_ZERO):
        probs.append(p_zero / N_ZERO)
        payouts_rows.append(0)

    # Positive rows get probabilities proportional to w_raw
    mass_pos = 1.0 - p_zero
    for j in range(N_POS):
        probs.append(mass_pos * (w_raw[j] / w_sum))
        payouts_rows.append(int(round(m_list[j] * 100)))

    # Ensure last entry is max payout to encode hard cap
    payouts_rows[-1] = int(round(mmax * 100))

    # Convert probabilities to integer weights
    weights = _normalize_to_int_weights(probs, scale=10_000_000)

    # Assemble LUT rows: (id, weight, payoutMultiplier)
    lut = []
    for i in range(N):
        lut.append((i + 1, weights[i], payouts_rows[i]))

    # Write CSV
    with out_csv.open('w', encoding='utf-8', newline='\n') as f:
        for row in lut:
            f.write(f"{row[0]},{row[1]},{row[2]}\n")

    # Build JSONL events from unique payouts present
    uniq = sorted(set([pm for _, _, pm in lut]))
    with out_jsonl.open('w', encoding='utf-8', newline='\n') as out:
        for i, pm in enumerate(uniq, start=1):
            out.write(json.dumps({'id': i, 'events': [{}], 'payoutMultiplier': pm}, separators=(',', ':')) + '\n')

    # Return summary
    return {
        'mode': mode,
        'p_zero': p_zero,
        'unique_payouts': len(uniq),
        'min_pm': min(uniq),
        'max_pm': max(uniq),
        'E_pos': E_pos_discrete,
        'target_ev': target_ev,
    }


def main():
    target_rtp = 0.96

    # Base mode params
    base_cost = 1.0
    base_mmin = 1.01
    base_mmax = 10000.0
    # Build positive payout grid (log-spaced via Pareto alpha=1)
    base_pos = [base_quantile((i + 0.5) / 1024.0, base_mmin, base_mmax) for i in range(1024)]

    # Elevate mode params (piecewise guided)
    elev_cost = 3.0
    elev_mmin = 1000.0
    elev_mmax = 100000.0
    knots = [elev_mmin, 10000.0, 20000.0, 50000.0, elev_mmax]
    surv = [1.0, 0.1, 0.05, 0.005, 0.0005]
    pw = PiecewisePareto(knots, surv)
    elev_pos = [pw.quantile((i + 0.5) / 1024.0 * pw.total_mass) for i in range(1024)]

    # Outputs
    base_summary = build_lookup_and_events(
        'base', base_pos, target_rtp, base_cost,
        MATH / 'lookup_table_base.csv', MATH / 'game_logic_base.jsonl', base_mmin, base_mmax
    )
    elev_summary = build_lookup_and_events(
        'elevate', elev_pos, target_rtp, elev_cost,
        MATH / 'lookup_table_elevate.csv', MATH / 'game_logic_elevate.jsonl', elev_mmin, elev_mmax
    )

    print('Base summary:', base_summary)
    print('Elevate summary:', elev_summary)


if __name__ == '__main__':
    main()
