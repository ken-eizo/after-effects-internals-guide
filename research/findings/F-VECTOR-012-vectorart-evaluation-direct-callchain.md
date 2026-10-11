---
status: strongly-supported-static
last_verified: 2026-10-11
evidence: E2-L + H
versions: AE2025 and AE2026 BEE.dll
---

# F-VECTOR-012 — VectorLayer::GetVectorArt directly creates TDB source path, populates evaluated art, and queries bounds

## Direct CALL evidence

Two versions of BEE.dll have the function `BEE_VectorLayer::GetVectorArt(time, transform, abort, param bag)`. Its decorated C++ return type is an intrusive reference-counted `BEE_VectorArt::Group`, **not PF_World**.

2026 disassembly of the function (RVA `0x7081B0`) resolves, among others:

- `0x708348`: `BEE_VectorArt::Group::Group(M_Matrix3 const&)`
- `0x7083A7`: `TDB_StreamID::TDB_StreamID(TDB_MatchName const&)`
- `0x7083B5`: `TDB_StreamIDPath::TDB_StreamIDPath(TDB_StreamID const&)`
- `0x7083E3`: `BEE_VectorStream::PopulateVectorArt(...)`
- `0x708448`: `BEE_VectorArt::GetBounds(...)`

The same sequence is present in 2025: `0x6E3A4F`, `0x6E3ABA`, `0x6E3ACD`, `0x6E3AFC`, `0x6E3BBB`.

This proves a **direct static evaluation entry path** from a native VectorLayer owner through authored TDB stream identity to vector art materialization and explicit bounds. It does not prove that an arbitrary third-party stream subclass is traversed, nor any vector output from a standard effect plug-in.

## Additional renderer/editor-specific boundaries

- `BEE_VectorArt::Path` has constructors accepting `CAGMPath` and `CAIMBezierPath`. It is an internal geometric object and cannot be assumed to be a reusable effect-output type.
- `BEE_VectorArt::StreamBasedFilter` constructor includes `BEE_VectorLayer const&`, `TDB_StreamIDPath const&`, `T_Time const&`: native filters explicitly capture the owning native vector layer and authored source stream path/time.
- `BEE_VectorArt::OriginInfo(TDB_StreamIDPath const&)` provides origin provenance. Selection subsystem also consumes `TDB_StreamIDPath`. No native external Pen Tool target registration discovered.
- `BEE_VectorLayer::Rasterize2DGraph` returns an intrusive `RG_RenderNode` — a separate renderer graph output rather than a `PF_World` at method return. Its internal direct calls include layer render options and matrix handling; the exact art-to-render-node callback connection is still unresolved.
- The private `C_AGMDLTranslatePort` accepts `PF_World*`, confirming a possible raster bridge. It is not a vector input socket for a public Effect SDK effect.

**Architecture barrier:** Building custom `BEE_VectorArt::Group` geometry in an external plug-in would not, by itself, attach that object to a BEE VectorLayer owner, native Pen/selection path, TDB stream tree, render graph, or project serializer. Independent plugin-owned native vector sources need a **provider/owner integration point**, not merely an AGMPath constructor.

## Evidence

`datasets/ae-vectorart-render-entry-calls-2025-2026.json` (two versions, bounded by x64 runtime function entries).
`datasets/ae-native-vector-render-edit-boundary-2025-2026.json` (reconstructed type/constructor inventory).
`docs/vector-shape-system/runtime-architecture.md` (topological overview).
