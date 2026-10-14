---
date: 2026-10-14
status: PASS in-host Adobe After Effects 2026 native Paint hierarchy read-only inspector; 35 streams, 6 parent-admission tests
evidence: E3 actual user-run CNLNativeShapeLayer AEX command, timestamped TSV, SHA-pinned original receipt
---
# F-VECTOR-083 — AE2026 user-run brush-created Paint native Stream hierarchy and parent admission

## Host observation: a genuine built-in Paint effect

The user executed `Animation > ChapeLayer: Inspect Adobe Paint Native Streams (Read Only)` against an AE2026 project with a brush-tool-generated **Paint** effect (never Paint Bucket or Brush Strokes).

Original timestamped `%TEMP%/ChapeLayer_PaintNativeHierarchy.tsv` was accessed directly from the authorized Windows host, verified, and copied byte-for-byte to `datasets/ae-paint-native-hierarchy-host-2026-20261014.tsv`.

The exact TSV SHA-256 is `1441288c22269fed5755d90b5e040ea02516c1d487d9fccfa4b9579570886440`. Last modified 2026-10-14 12:00:13 local. Summary: `datasets/ae-paint-native-hierarchy-host-2026-20261014-summary.json`.

**Measured:** `paint_found=1`, effect Parade `count=1`, one actual Paint Brush/Stroke child, `inspected_nodes=35`, `errors=0`, `host_project_mutated=0`, `private_host_calls=0`, AEGP menu-registration success with all hook/insertion statuses zero.

Extracted exact native hierarchy:

```text
ADBE Paint (named group, 4 children; display: Paint)
├── ADBE Paint-0000 (leaf)
├── ADBE Paint On Transparent (leaf)
├── ADBE Paint Group (indexed group, 1 child; display: Strokes)
│   └── ADBE Paint Atom (named group, 6 children; display: Brush)
│       ├── ADBE Paint Transfer Mode (leaf; Blending Mode)
│       ├── ADBE Paint Duration (leaf)
│       ├── ADBE Paint Shape (leaf; Path)
│       ├── ADBE Paint Properties (named group, 16 children; Stroke Options)
│       │   ├── Start, End, Color, Diameter, Angle, Hardness,
│       │   │   Roundness, Spacing, Channels, Opacity, Flow
│       │   └── Clone Source, Position, Time, Time Shift, Source Type
│       ├── ADBE Paint Transform (named group, 4 children)
│       │   └── Anchor Point, Position, Scale, Rotation
│       └── ADBE Paint Nibbler Group (indexed group, zero children)
└── ADBE Effect Built In Params (named group; Compositing Options)
```

Note: the inferred label `NO_DATA` for `ADBE Paint-0000` above means the inspector observed `groupingType=0` (leaf), **not** that `AEGP_GetStreamType` established an AEGP_StreamType_NO_DATA value. Do not conflate grouping type with stream-value type.

## Measured public AEGP_CanAddStream matrix

Parent for all six is the **actual** indexed `ADBE Paint Group`:

| Child candidate MatchName | CanAdd | API error |
|---|---:|---:|
| `ADBE Paint Atom` | TRUE | 0 |
| `ADBE Paint Nibbler Atom` | FALSE | 0 |
| `ADBE Paint Shape` | FALSE | 0 |
| `ADBE Vector Group` | FALSE | 0 |
| `CNL:PaintAtom` | FALSE | 0 |
| `ADBE Paint Atom - CNLProbe` | FALSE | 0 |

This is strong experimental evidence of a **strict admissible child kind** for Paint Strokes in this AE2026 fixture. It is not merely a permissive name-prefix check. Compare Shape's `ADBE Vector Shape - CNLProbe` can-add result reported in F-VECTOR-063/065; **different parent grammar, different results**.

Crucial boundaries:
- This API checks *parent admission only*, not full registry-wide class-creator presence, factory constructability, editor capability, or archive correctness.
- Existing `ADBE Paint Atom` is admitted; **unknown synthetic name is not**. Therefore Paint as a built-in AE effect does *not* provide evidence of arbitrary third-party native Stream type registration.
- Public `AEGP_DynamicStreamSuite` can traverse real built-in Paint native named/indexed groups and manipulate **existing registered native Brush** objects (confirmed separately by Adobe SDK 25.6 `Examples/AEGP/Streamie/Streamie.cpp`).
- The project reported unchanged, and no private TDB/BEE calls were made in this experiment. No external `BEE_PaintAtom` replacement was created.
- Only one actual Paint effect and one Brush instance were sampled. This does not establish all admissible children for all possible paint states or host releases.

## Updated product decision

**Partially proven**: A third-party AEGP can see Adobe-native Paint's actual hierarchy, and can potentially edit Adobe's registered Brush children using the Adobe-authored public Streamie sample.

**Not achieved**: register `CNL:CustomGroup` as a new host-native property class, attach it within an arbitrary Effect or native Layer, display arbitrary third-party native group/leaf properties in the standard Timeline with full AE-owned keyframes/undo/archive, or provide new custom BEE Layer type.

The remaining engineering target is the safe, supported, lifecycle-valid foreign TDB Stream class registrar + host owner editor/serialization contract, not painting or replacing an existing registered Brush.

## Reproduction and receipts

- Compiled source: `D:/Developer/ShapeLayerAE/labs/native_shape_layer_prototype/ChapePaintNativeInspector.cpp`.
- Offline research copy: `experiments/vector-shape/probe-src/tools/ChapePaintNativeInspector.cpp`.
- Raw host receipt: `datasets/ae-paint-native-hierarchy-host-2026-20261014.tsv`.
- Structured host receipt: `datasets/ae-paint-native-hierarchy-host-2026-20261014-summary.json`.
- Verifier: `experiments/vector-shape/probe-src/tools/verify_paint_host_receipt.py`.
- Prior findings F-VECTOR-080, 081, 082 show BEE/TDB register chain, private Paint Suite host table and public Adobe SDK Streamie.

No private Adobe host API executed as part of this receipt, and no production project changes were requested or performed by the inspector.
