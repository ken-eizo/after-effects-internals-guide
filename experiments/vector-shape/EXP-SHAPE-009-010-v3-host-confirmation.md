---
status: confirmed-in-host
last_verified: 2026-10-11
evidence: E2-X + E2-L
versions: AE2026, ShapeLayerAE v3 from SDK25.6
---

# EXP-SHAPE-009/010 — Real AE2026 private getter and unknown native Contents type admission

The user ran the three ShapeLayerAE v3 commands on AE2026 (confirmed running host process; AEX installed hash matched built Release AEX). The user supplied dialogs that identify the commands' successful receipt writing and the actual five fresh raw TSV files were read and archived from the host's Windows TEMP folder. No native stream creation, registration, deletion or edit took place in these commands.

## Private TDB getter: **E2-X confirmed**

`ShapeLayerAE_private_factory_probe.tsv` at 19:29:43 local:

```text
module_found  export_found  code_fingerprint_ok  factory_pointer_nonnull
1             1             1                    1
```

Input SHA-256 `390bb93c2de843cb55aa50983173e7af50348122a63d277bc81c1cefd8eba017`. This confirms the private no-argument getter returned non-null when called from user-installed AEGP. No pointer addresses were exposed, no pointer dereference or method invoked, no mutations.

## Native shape-prefix grammar: **E2-X confirmed for CanAdd only**

`ShapeLayerAE_canadd_unknown.tsv` at 19:30:24 local contained 72 calls (6 existing indexed groups × 12 candidate names), all `query_error=0`. In the Root Vectors Group and two nested Vectors Group instances:

| candidate | result |
| --- | --- |
| `ADBE Vector Shape - ShapeLayerAEProbe` | allow |
| `ADBE Vector Graphic - ShapeLayerAEProbe` | allow |
| `ADBE Vector Filter - ShapeLayerAEProbe` | allow |
| `ADBE Vector Group - ShapeLayerAEProbe` | deny |
| `ShapeLayerAE Custom Stream` | deny |
| `ADBE Vector Filter - Repeater` | allow |
| `ADBE Slider Control` | deny |

Effect Parade rejected all the tested vector-prefix candidates but allowed Slider Control; Mask Parade and Layer Sets rejected these tested names.

Raw SHA-256 `9a229ded137d826ac9c8d4d006e4891d167295c5cfbf98a1d952513aad2f0095`. The behavior is consistent with separately confirmed private `BEE_VectorStream::VectorsStreamGroup::CanStore` prefix literals. It validates a parent-side **admission predicate even for unknown candidate names**. It does NOT prove the TDB factory can instantiate those names or that the name registration exists.

## Public StreamSuite6 UID anomaly retested

`ShapeLayerAE_stream_metadata.tsv` (359 streams, SHA-256 `1a5355c8a6ff0810285cd68aa47b240c93b83952ac16462a6a95efd96c4a4816`) includes **two independent calls** per stream, each with different nonzero initial sentinel, and corresponding error codes.

- 359/359 initial UID calls returned 0, `uid_error=0`.
- 359/359 second UID calls returned 0, `second_uid_error=0`.
- 0 disagreements, and 0 SDK depth mismatches.
- This is *not* simply an unwritten zero-initialized output buffer, but one host/build/fixture still does not establish a global SDK bug. No identity mapping to private `TDB_StreamIDPath` has been proven.

## Archived exact evidence

`experiments/vector-shape/runs/EXP-SHAPE-009-010/20261011-user-host-v3/`

- `ShapeLayerAE_private_factory_probe.tsv` 1 row
- `ShapeLayerAE_canadd_unknown.tsv` 72 rows
- `ShapeLayerAE_stream_metadata.tsv` 359 rows
- `ShapeLayerAE_stream_tree.tsv` 359 rows, SHA-256 `38243e05de1d447d8b71104c4d73f4ddd01d778b627d6abceaf14db0ff9b5432`
- `ShapeLayerAE_canadd.tsv` 36 known builtin candidates, SHA-256 `8b51d257014bebcfdc9a7ee1ae348d43d863e408244b6bf026d584c61a40fba0`
- `analysis.json` machine-generated exact digests, file modification dates, row counts, UID distributions, admission matrix and original Windows TEMP provenance.

Deployed/built AEX SHA-256: `6a20aaa59100a68aaa5e8aa4af126756a9dd8dd6cf50951dce8cf1bf6ec6dbf1`; corresponding source in `probe-src/src/ShapeLayerProbe.cpp`.

## Proof threshold — native CompNodeAE vector object

**Not achieved:** A new independent TDB stream type registered from a third-party AEGP, native owned vector Contents under an effect, built-in Pen tool control, persistent serialization, or native BEE/AGM geometry output. The private getter success is a meaningful, separately measured prerequisite, not equivalent to any of these.
