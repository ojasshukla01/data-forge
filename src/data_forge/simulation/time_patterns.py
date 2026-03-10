"""Time-aware workload patterns for pipeline simulation."""

import random
from enum import Enum


class EventPattern(str, Enum):
    """Event distribution pattern over time."""

    STEADY = "steady"
    BURST = "burst"
    SEASONAL = "seasonal"
    GROWTH = "growth"


def apply_time_pattern(
    event_count: int,
    pattern: EventPattern,
    start_ts: float,
    end_ts: float,
    seed: int = 42,
) -> list[float]:
    """
    Return list of timestamps for events, distributed according to pattern.
    Timestamps are in seconds since epoch (float).
    Deterministic with fixed seed.
    """
    rng = random.Random(seed)
    if event_count <= 0 or end_ts <= start_ts:
        return []

    duration = end_ts - start_ts

    if pattern == EventPattern.STEADY:
        # Uniform distribution
        return sorted([start_ts + duration * rng.random() for _ in range(event_count)])

    if pattern == EventPattern.BURST:
        # Occasional spikes: 70% in first half, 30% in second half with a spike
        ts_list: list[float] = []
        spike = 0.3
        n_spike = int(event_count * spike)
        n_normal = event_count - n_spike
        for _ in range(n_normal):
            ts_list.append(start_ts + duration * rng.random())
        # Spike in a narrow window (last 10% of timeline)
        spike_start = start_ts + duration * 0.9
        spike_end = end_ts
        for _ in range(n_spike):
            ts_list.append(spike_start + (spike_end - spike_start) * rng.random())
        return sorted(ts_list)

    if pattern == EventPattern.SEASONAL:
        # Cyclical: higher in "day" windows (every 1/4 of timeline)
        ts_list = []
        for i in range(event_count):
            phase = i / max(event_count, 1)
            base = start_ts + duration * phase
            # Add noise with seasonal bias
            cycle = 4  # 4 "seasons" in timeline
            t = (base - start_ts) / duration
            bias = 0.5 + 0.5 * (1 if int(t * cycle) % 2 == 0 else 0.3)
            jitter = duration * 0.05 * (rng.random() - 0.5)
            ts_list.append(max(start_ts, min(end_ts, base + jitter * bias)))
        return sorted(ts_list)

    if pattern == EventPattern.GROWTH:
        # Increasing density over time
        ts_list = []
        for i in range(event_count):
            # Square root bias: more events toward end
            u = (i + rng.random()) / event_count
            t = u**0.5  # sqrt gives growth
            ts_list.append(start_ts + duration * min(1.0, t))
        return sorted(ts_list)

    # Default: steady
    return sorted([start_ts + duration * rng.random() for _ in range(event_count)])
