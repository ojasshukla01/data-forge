"""Distribution-aware value generation: skewed, categorical, seasonal."""

import math
import random
from typing import Any


def apply_distribution(
    base_value: Any,
    distribution: str,
    params: dict[str, Any],
    seed: int,
) -> Any:
    """
    Apply a distribution to a value (or generate from distribution if base unused).
    Returns value of same type as base_value where possible.
    """
    rng = random.Random(seed)
    dist = distribution.lower()

    if dist == "uniform":
        return base_value

    if dist == "normal" or dist == "gaussian":
        mu = params.get("mu", 0)
        sigma = params.get("sigma", 1)
        x = rng.gauss(mu, sigma)
        if isinstance(base_value, int):
            return int(round(x))
        if isinstance(base_value, (float, type(None))):
            return round(x, 4)
        return base_value

    if dist == "skewed" or dist == "lognormal":
        mu = params.get("mu", 0)
        sigma = params.get("sigma", 1)
        x = rng.lognormvariate(mu, sigma)
        if isinstance(base_value, int):
            return max(0, int(round(x)))
        return round(x, 4)

    if dist == "categorical":
        categories = params.get("categories", [])
        weights = params.get("weights", [])
        if not categories:
            return base_value
        if weights and len(weights) == len(categories):
            return rng.choices(categories, weights=weights, k=1)[0]
        return rng.choice(categories)

    if dist == "seasonal":
        # phase in [0,1] for time of year; amplitude for spike
        phase = params.get("phase", 0.25)  # Q4 spike default
        amplitude = params.get("amplitude", 1.5)
        t = rng.random()
        mult = 1.0 + (amplitude - 1.0) * math.exp(-((t - phase) ** 2) * 20)
        if isinstance(base_value, (int, float)):
            return type(base_value)(base_value * mult) if base_value else 0
        return base_value

    if dist == "long_tail":
        # Most small, few large
        p = rng.random()
        if p < params.get("head_ratio", 0.9):
            scale = params.get("head_scale", 1.0)
            if isinstance(base_value, (int, float)):
                return type(base_value)((base_value or 0) * scale * rng.random())
        else:
            scale = params.get("tail_scale", 10.0)
            if isinstance(base_value, (int, float)):
                return type(base_value)((base_value or 1) * scale * (1 + rng.random()))
        return base_value

    return base_value
