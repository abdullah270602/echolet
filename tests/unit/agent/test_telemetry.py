"""Per-call latency summary: the right metric goes to the right stage, percentiles add up."""

import importlib.util
import os
from types import SimpleNamespace

_spec = importlib.util.spec_from_file_location(
    "agent_telemetry", os.path.join(os.path.dirname(__file__), "..", "..", "..", "agent", "telemetry.py")
)
telemetry = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(telemetry)


def _metric(kind, **fields):
    return type(kind, (SimpleNamespace,), {})(**fields)


def test_records_each_stage_and_ignores_others():
    lat = telemetry.CallLatency()
    for d in (0.4, 0.6):
        lat.record(_metric("EOUMetrics", end_of_utterance_delay=d))
    for t in (0.5, 0.7):
        lat.record(_metric("LLMMetrics", ttft=t))
    for b in (0.3, 0.5):
        lat.record(_metric("TTSMetrics", ttfb=b))
    lat.record(_metric("STTMetrics", duration=1.0))      # not part of reply delay
    lat.record(_metric("LLMMetrics", ttft=-1))            # unknown values are skipped
    s = lat.summary()
    assert s["turns"] == 2
    assert s["eou_p50"] == 0.5 and s["llm_ttft_p50"] == 0.6 and s["tts_ttfb_p50"] == 0.4
    assert s["reply_p50"] == 1.5                          # 0.5 + 0.6 + 0.4


def test_empty_call_has_no_numbers():
    s = telemetry.CallLatency().summary()
    assert s["turns"] == 0 and s["reply_p50"] is None and s["reply_p95"] is None
