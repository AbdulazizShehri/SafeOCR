from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WerBreakdown:
    wer: float
    substitution: float
    deletion: float
    insertion: float


@dataclass(frozen=True, slots=True)
class SummaryStats:
    n: int
    mean: float
    ci_low: float
    ci_high: float
    q1: float
    median: float
    q3: float
    minimum: float
    maximum: float


def word_error_rate(gold: str, pred: str) -> WerBreakdown:
    """ClinOCR-Bench-compatible whitespace-token WER.

    This follows the MIT-licensed ClinOCR-Bench-Baseline implementation pinned
    for the SafeOCR external validation protocol.
    """

    ref = gold.split()
    hyp = pred.split()

    if len(ref) == 0:
        value = 0.0 if len(hyp) == 0 else math.inf
        return WerBreakdown(value, value, value, value)

    n, m = len(ref), len(hyp)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref[i - 1] == hyp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j - 1],
                    dp[i - 1][j],
                    dp[i][j - 1],
                )

    substitutions = deletions = insertions = 0
    i, j = n, m
    while i > 0 or j > 0:
        if (
            i > 0
            and j > 0
            and ref[i - 1] == hyp[j - 1]
            and dp[i][j] == dp[i - 1][j - 1]
        ):
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            substitutions += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            deletions += 1
            i -= 1
        else:
            insertions += 1
            j -= 1

    denominator = len(ref)
    return WerBreakdown(
        wer=(substitutions + deletions + insertions) / denominator,
        substitution=substitutions / denominator,
        deletion=deletions / denominator,
        insertion=insertions / denominator,
    )


def _percentile(sorted_values: list[float], percentile: float) -> float:
    index = (len(sorted_values) - 1) * percentile / 100.0
    lower = int(index)
    upper = math.ceil(index)
    return sorted_values[lower] + (
        sorted_values[upper] - sorted_values[lower]
    ) * (index - lower)


def summary_stats(values: tuple[float, ...]) -> SummaryStats:
    finite = sorted(value for value in values if math.isfinite(value))
    if not finite:
        raise ValueError("at least one finite value is required")
    n = len(finite)
    mean = sum(finite) / n
    std = math.sqrt(sum((value - mean) ** 2 for value in finite) / n)
    margin = 1.96 * std / math.sqrt(n)
    return SummaryStats(
        n=n,
        mean=mean,
        ci_low=mean - margin,
        ci_high=mean + margin,
        q1=_percentile(finite, 25.0),
        median=_percentile(finite, 50.0),
        q3=_percentile(finite, 75.0),
        minimum=finite[0],
        maximum=finite[-1],
    )
