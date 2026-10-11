---
status: confirmed-in-host
last_verified: 2026-10-11
evidence: E0-H + E2-X + E2-L
versions: SDK 25.6; target AE 2026
---
# EXP-SHAPE-009 — Unknown but syntactically Shape-prefixed names; UID sentinel controls

`ShapeLayerAE` has an **optional**, separate Animation menu command `ShapeLayerAE: Probe Unknown Shape Names (Experimental)`. Nothing except a direct user invocation of that command enables the unknown-name probes.

It calls **only** `AEGP_CanAddStream` on **existing INDEXED_GROUPs** with:
- `ADBE Vector Shape - ShapeLayerAEProbe`
- `ADBE Vector Graphic - ShapeLayerAEProbe`
- `ADBE Vector Filter - ShapeLayerAEProbe`
- `ADBE Vector Group - ShapeLayerAEProbe`
- `ShapeLayerAE Custom Stream`
- `ADBE Vector Filter - Repeater` (known control)

It **does not call `AEGP_AddStream`, `RegisterFactoryFunc`, or any other mutation API**. If the first three return CanAdd=true but the name is unknown to factory, it supports **parent category predicate** separate from **type creation**; it does not establish safe creation. The latter two unknown controls help reject an overbroad "accepts all strings" model.

Additionally, even the normal Dump Stream Tree now performs two `AEGP_GetUniqueStreamID` calls, preinitializing the output to two different nonzero sentinels. The results and error codes appear as two extra columns on `ShapeLayerAE_stream_metadata.tsv`. The prior AE2026 host showed 359/359 zero IDs with error zero; this isolates untouched output from deliberate zero assignment.

Files written to `%TEMP%`: `ShapeLayerAE_canadd_unknown.tsv`, `ShapeLayerAE_stream_metadata.tsv` and original `ShapeLayerAE_stream_tree.tsv`. Existing known-type CanAdd remains in the normal menu command and its `ShapeLayerAE_canadd.tsv`.

**Observed outcome:** on 2026-10-11 the user's AE2026 host returned `CanAddStream=true` for three unknown Shape/Graphic/Filter prefixes under native Contents and `false` for negative controls; 72 queries, all error zero. UID was zero on both nonzero-sentinel calls for all 359 streams. These are observed data, not proof of actual creation. Raw input and hashes: `experiments/vector-shape/EXP-SHAPE-009-010-v3-host-confirmation.md`.

Run only in a disposable project and after replacing the AEX with AE **closed**, then restarting. Do not attempt actual AddStream on a custom name, regardless of CanAdd result. Store logs and host exact version/hashes as E2-X before changing the hypothesis.
