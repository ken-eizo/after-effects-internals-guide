---
date: 2026-10-14
status: PASS real in-host AE2026 Paint v2 property metadata inspection; plugin-defined native Stream still NOT demonstrated
evidence: E3 user-run AE2026 plugin output, SHA256-pinned TSV, independent offline receipt verifier
---
# F-VECTOR-087 — Paint native leaf properties and keyframes verified in the actual AE 2026 timeline

## Direct host result

The user ran `ChapeLayer: Inspect Adobe Paint Native Streams (Read Only)` within **Adobe After Effects 2026** on a real Brush-created **Paint** effect (NOT Paint Bucket or Brush Strokes), after the v2 native leaf-metadata AEX was installed.

The original TSV was retrieved from the authorized PC's `%TEMP%\ChapeLayer_PaintNativeHierarchy.tsv` and preserved byte-for-byte in:

- `datasets/ae-paint-native-hierarchy-host-v2-2026-20261014.tsv`
- `datasets/ae-paint-native-hierarchy-host-v2-2026-20261014-summary.json`

TSV SHA-256: `860f60b2d25b57ebe698afa778dcee1cba06cfac76e0060f91f11a34ef529553`.

- Paint effect successfully identified: `paint_found=1`.
- Actual Brush stroke instances: **6**.
- Actual native Stream nodes: **170**.
- Native leaf Stream metadata rows: **142**.
- Leaves admitting temporal variation: **109**.
- Currently time-varying leaves: **0** in this exact fixture.
- Nonzero native keyframe counts: **0** in this exact fixture, not a failed keyframe API.
- API/traversal errors: **0**; metadata query errors: **0**.
- Public inspector reports `host_project_mutated=0`, `private_host_calls=0`.

## The nontrivial native Path result

All six `ADBE Paint Shape` leaves (displayed as **Path**) returned:

```text
AEGP_GetStreamType          = 0  (AEGP_StreamType_NO_DATA)
AEGP_CanVaryOverTime        = TRUE
AEGP_IsStreamTimevarying    = FALSE (no keys/expressions currently)
AEGP_GetStreamNumKFs        = intentionally skipped for NO_DATA
```

The host-native Paint Path exists and is editable via Adobe's special internal implementation, yet the public `AEGP_StreamType` does not offer its path value as ordinary `MASK` or `ARBITRARY` data. The official 25.6 SDK comment says `NO_DATA` streams cannot have values retrieved through standard `AEGP_GetNewStreamValue`; therefore the C++ inspector correctly avoids trying to access it. This **does not** imply the Path has no data or lacks host native keyframing.

Other measured leaf types:
- Paint Color: `AEGP_StreamType_COLOR` = 6; `CanVaryOverTime=TRUE`.
- Paint Position: `AEGP_StreamType_TwoD_SPATIAL` = 3; `CanVaryOverTime=TRUE`.
- Paint Opacity: `AEGP_StreamType_OneD` = 5; `CanVaryOverTime=TRUE`.

## Parent admission remains strict

The read-only `AEGP_CanAddStream` matrix against the actual indexed `ADBE Paint Group` again permitted only the registered Adobe `ADBE Paint Atom` among six tested names and denied `CNL:PaintAtom` and `ADBE Paint Atom - CNLProbe`. Factory ownership is not changed by querying admission.

## Verifier / boundaries

Run:
```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_paint_host_v2_receipt.py"
```

PASS: SHA, 170 nodes, 6 Brush instances, 142 leaves, 109 can-vary, NO_DATA Paint Path, 0 AEGP errors, read-only flags.

What this proves: Adobe-native Paint has sophisticated leaf kinds and genuine time-variable host properties, and a third-party AEGP can enumerate their **metadata**.

What this does **NOT** prove: user AEX can register an arbitrary new `TDB_StreamBase` native class, define an arbitrary child grammar, display `CNL:Group` in AE's standard Timeline, save/reopen a custom host-owned class or replace Paint's private Path evaluator.
