"""Pipeline simulation: event streams, time patterns, workload profiles."""

from data_forge.simulation.event_stream import generate_event_stream
from data_forge.simulation.time_patterns import EventPattern, apply_time_pattern

__all__ = [
    "generate_event_stream",
    "EventPattern",
    "apply_time_pattern",
]
