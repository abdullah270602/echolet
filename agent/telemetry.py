"""
Per-call latency telemetry for the voice agent.

LiveKit emits metrics for every pipeline stage. What a caller feels is the gap between
finishing a sentence and hearing the reply, which LiveKit breaks into three parts:
end-of-utterance detection delay + LLM time-to-first-token + TTS time-to-first-byte.
This collects them per call and logs one summary line (p50/p95) when the call ends, so
`lk agent logs` answers "how fast does Emma respond?" without extra infrastructure.
"""

from __future__ import annotations

import statistics


def _pct(values: list[float], q: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=100, method="inclusive")[int(q) - 1]


class CallLatency:
    def __init__(self) -> None:
        self.eou: list[float] = []   # end-of-utterance delay (caller stopped -> turn committed)
        self.ttft: list[float] = []  # LLM time to first token
        self.ttfb: list[float] = []  # TTS time to first audio byte

    def record(self, m) -> None:
        """Record one LiveKit metrics object (EOUMetrics, LLMMetrics or TTSMetrics)."""
        kind = type(m).__name__
        if kind == "EOUMetrics" and m.end_of_utterance_delay > 0:
            self.eou.append(m.end_of_utterance_delay)
        elif kind == "LLMMetrics" and m.ttft > 0:
            self.ttft.append(m.ttft)
        elif kind == "TTSMetrics" and m.ttfb > 0:
            self.ttfb.append(m.ttfb)

    def summary(self) -> dict:
        """Median and p95 per stage, plus the estimated reply delay (sum of medians / p95s)."""
        out = {"turns": len(self.ttft)}
        for name, values in (("eou", self.eou), ("llm_ttft", self.ttft), ("tts_ttfb", self.ttfb)):
            out[f"{name}_p50"] = _round(_pct(values, 50))
            out[f"{name}_p95"] = _round(_pct(values, 95))
        for q in ("p50", "p95"):
            parts = [out[f"{s}_{q}"] for s in ("eou", "llm_ttft", "tts_ttfb")]
            out[f"reply_{q}"] = _round(sum(parts)) if all(p is not None for p in parts) else None
        return out


def _round(v: float | None) -> float | None:
    return None if v is None else round(v, 2)
