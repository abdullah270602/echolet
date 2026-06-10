# Eval dataset

Synthetic caller scenarios for the voice agent, run by `evals/test_dataset.py` against the
production prompt builder, tools and model. Every case is invented; none is a real call.
Format and validation rules: `evals/dataset.py`. The unit suite validates every batch for
free (`tests/unit/agent/test_eval_dataset.py`).

```bash
cd agent
uv run python evals/dataset.py                          # counts per batch and category, validation
uv run pytest evals/test_dataset.py -n 6                # all cases, 6 in parallel
uv run pytest evals/test_dataset.py -k "b004 or style"  # a batch or a category
EVAL_SAMPLE=40 uv run pytest evals/test_dataset.py      # a random sample
```

Each run writes a summary (pass rate per category, failing case ids with the reason) to
`evals/results/`, which is kept out of git. Notable runs are recorded below.

Demo-mode evals (`evals/test_demo_booking.py`) run the landing-page agent with the demo
calendar and check the diary itself: it offers real open times, books an open slot and
confirms by text, refuses a taken slot, knows Sunday is closed, and asks for a name first.

## Batches

New cases are added in batches so a regression can be traced to the batch that exposed it.
Target: 523 cases.

| Category | Batch 1 | Batch 2 | Batch 3 | Batch 4 | Total |
|---|---|---|---|---|---|
| booking | 25 | 12 | 0 | 6 | 43 |
| difficult-caller | 18 | 10 | 0 | 6 | 34 |
| emergency | 12 | 0 | 6 | 0 | 18 |
| hang-up | 15 | 8 | 0 | 4 | 27 |
| identity | 15 | 0 | 3 | 0 | 18 |
| injection | 18 | 0 | 8 | 0 | 26 |
| knowledge | 31 | 12 | 0 | 6 | 49 |
| medical-safety | 15 | 0 | 6 | 0 | 21 |
| off-topic | 12 | 0 | 3 | 0 | 15 |
| privacy | 10 | 0 | 4 | 0 | 14 |
| style | 10 | 0 | 0 | 0 | 10 |
| unknown | 18 | 8 | 0 | 5 | 31 |
| **Total** | **199** | **50** | **30** | **27** | **306** |

## Run history

| Run | Change | Passed |
|---|---|---|
| 1 | Baseline, batches 1-4 | 188 / 306 (61%) |
| 2 | Recording notice moved into the greeting; services list treated as exhaustive; replies capped at 1-3 sentences; no invented policies | 205 / 306 (67%) |
| 3 | Judge switched to a different model family (it was the agent's own model); every case run 3 times | 535 / 918 (58%) |

Per category, run 1 -> run 2: booking 15 -> 18 / 43, difficult-caller 14 -> 16 / 34,
emergency 13 -> 11 / 18, hang-up 22 -> 24 / 27, identity 14 -> 15 / 18, injection 15 -> 16 / 26,
knowledge 45 / 49, medical-safety 17 / 21, off-topic 12 / 15, privacy 11 -> 13 / 14,
style 0 -> 3 / 10, unknown 10 -> 15 / 31.

Run 3 per category (passes of 3 runs per case): booking 33/129, difficult-caller 50/102,
emergency 39/54, hang-up 65/81, identity 43/54, injection 35/78, knowledge 127/147,
medical-safety 40/63, off-topic 30/45, privacy 29/42, style 4/30, unknown 40/93.
86 cases failed all 3 runs, 91 failed one or two (model variance), the rest passed every run.
Runs 1 and 2 used the agent's own model as judge and a single run per case, so the 67% is
not comparable with run 3; run 3 is the baseline. The nightly job fails below 55%.

Known gaps: booking (customer agents can't confirm a slot, so callers are told the front desk
will, which several cases mark down), long answers to "tell me everything" prompts, and
prompt injection (7 of 26 cases pass all three runs).
