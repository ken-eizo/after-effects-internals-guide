# EXP-SHAPE-083 — AE2026 in-host genuine Paint Group/Brush native admission

**Status: PASS — actual in-host AEGP read-only inspector executed by user (2026-10-14 12:00:13).**

The effect is the special **Paint** automatically created by AE's brush tool, not Paint Bucket and not Brush Strokes.

## Protocol

Run the built AEGP menu command `Animation > ChapeLayer: Inspect Adobe Paint Native Streams (Read Only)` with a layer selected that contains Paint and one or more brush strokes.

Acquire the generated `%TEMP%/ChapeLayer_PaintNativeHierarchy.tsv` from the authorized host. This run has:
- `paint_found=1` (exact `ADBE Paint` MatchName).
- `inspected_nodes=35`, `errors=0`; one actual `ADBE Paint Atom` under `ADBE Paint Group`.
- Real `ADBE Paint Group` is an INDEXED group (type 2), one child `ADBE Paint Atom` is a NAMED group (type 1) with six children.
- `ADBE Paint Properties` 16 fixed child Streams, `ADBE Paint Transform` 4.
- `AEGP_CanAddStream` on `ADBE Paint Group`: **TRUE only for the built-in `ADBE Paint Atom`** among tested candidates. All other five candidates, including `CNL:PaintAtom` and the prefix-deceptive `ADBE Paint Atom - CNLProbe`, returned FALSE; all calls returned error 0.
- Inspector-reported `host_project_mutated=0`, `private_host_calls=0`.

## Reproducible receipts

Original exact TSV preserved as:
`datasets/ae-paint-native-hierarchy-host-2026-20261014.tsv`
SHA256: `1441288c22269fed5755d90b5e040ea02516c1d487d9fccfa4b9579570886440`.

Structured evidence:
`datasets/ae-paint-native-hierarchy-host-2026-20261014-summary.json`.

Verifier:
`python experiments/vector-shape/probe-src/tools/verify_paint_host_receipt.py`
PASS: raw SHA, 35 Stream nodes and group type/counts, six admission decisions and 0 errors.

## Remaining admission gap

The experiment proves legal access to **already host-registered native Paint Streams** and a strict Paint Strokes group acceptance filter for tested names. It does **not** prove an arbitrary plugin-native TDB Stream factory registration, a novel custom property insertion, or third-party subclass lifecycle/persistence. It does not justify direct calls to Adobe-private `TDB_ScRegisterStreams` inside a live host. Only one host session/one stroke was checked.

Finding: `research/findings/F-VECTOR-083-paint-inhost-native-stream-hierarchy-admission.md`.
