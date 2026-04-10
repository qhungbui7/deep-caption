from dataclasses import dataclass


@dataclass(slots=True)
class MetricsSnapshot:
    pipeline_latency_ms: float = 0.0
    translation_latency_ms: float = 0.0
