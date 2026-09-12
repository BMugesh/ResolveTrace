import numpy as np
from scipy.spatial.distance import jensenshannon
from typing import Dict, List, Any

def compute_jsd(p_dist: Dict[str, float], q_dist: Dict[str, float]) -> float:
    """
    Computes Jensen-Shannon Divergence between two categorical probability distributions.
    D_JS(P || Q) = 1/2 * D_KL(P || M) + 1/2 * D_KL(Q || M), where M = (P + Q)/2.
    Returns value in [0.0, 1.0].
    """
    all_keys = sorted(list(set(p_dist.keys()) | set(q_dist.keys())))
    if not all_keys:
        return 0.0

    p_vec = np.array([p_dist.get(k, 0.0) for k in all_keys], dtype=np.float64)
    q_vec = np.array([q_dist.get(k, 0.0) for k in all_keys], dtype=np.float64)

    # Normalize
    p_sum = p_vec.sum()
    q_sum = q_vec.sum()
    if p_sum > 0:
        p_vec /= p_sum
    if q_sum > 0:
        q_vec /= q_sum

    if p_sum == 0 or q_sum == 0:
        return 0.0

    # scipy jensenshannon returns the square root of JSD (Jensen-Shannon distance) with base 2
    # We square it to get standard JSD divergence
    js_dist = jensenshannon(p_vec, q_vec, base=2)
    js_div = js_dist ** 2
    return float(round(js_div, 4))
