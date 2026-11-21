"""Metric pipelines under test."""
from __future__ import annotations

import os


def compute_metric(metric_name: str, context: str) -> float:
    variant = os.getenv("PIPELINE_VARIANT", "good")
    if variant == "poor":
        return 0.0

    if metric_name == "mau":
        # distinct users with an order in Jan: 1,2
        return 2.0
    if metric_name == "total_revenue":
        return 12.5 + 7.0 + 99.0 + 5.0
    if metric_name == "aov":
        total = 12.5 + 7.0 + 99.0 + 5.0
        return total / 4
    return 0.0
