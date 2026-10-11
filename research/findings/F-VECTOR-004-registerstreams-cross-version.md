---
status: strongly-supported-local-artifact
last_verified: 2026-10-11
evidence: E2-L + E0-H
versions: installed AE 2025 and AE 2026 BEE.dll; SDK CS6/CC2014/25.6
---
# F-VECTOR-004 — RegisterStreams routines exist across layer classes and versions

## Confirmed E2-L

Local export records establish these distinct symbols in **both** 2025 and 2026 BEE DLLs:

- `BEE_VectorLayer::RegisterStreams()`
- `BEE_TextLayer::RegisterStreams()`
- `BEE_AVLayer::RegisterStreams(char const*)` (exact decorated ABI captured in dataset)
- `BEE_Layer::RegisterStreams(bool)`
- `BEE_VectorStream::PopulateVectorArt(...)`
- `BEE_VectorLayer::Rasterize2DGraph(...)`

The latest source of exact raw decorated names and RVA values is `datasets/ae-shape-native-extension-lineage-2026.json` and `datasets/ae-vector-registerstreams-static-2025-2026.json`.

The `RegisterStreams` symbol alone **does not** prove a type registry that a plug-in may augment. Bounded, offline disassembly of the vector routine shows calls to stream expression, keyframe and flag **command handlers**; `BEE_AVLayer::RegisterStreams` calls the indexed-group reorder command. It may be concerned with command binding. More reverse call-graph / data-write evidence is needed before choosing among factory, command, and mixed registry models.

## Important version and ABI limit

2025 and 2026 have different RVAs despite persistent named functions; a compiler-generated export is not an SDK entrypoint or guaranteed signature/lifetime/calling contract. A thunk, initialization ordering or internal host ownership could make a function unusable externally even if callable.

## Refutation tests

H-factory: locate an actual insertion of a third-party type descriptor and demonstrate that a new host-owned indexed group is recognized by native Timeline and project serialization without native Shape Layer creation. If only existing IDs register built-in commands, H-factory fails.

H-command: trace registration writes to a command dispatcher, and show no novel type factory storage; refuted by observed new stream-type registration via that function.

These tests are separate from reading existing paths. No native extension experiment has passed.

## Direct caller sampling (2025 vs 2026)

A separate, full executable-section Capstone pass decoded approximately **4,488,162** instructions in AE 2025 and **4,626,191** in AE 2026 with SKIPDATA enabled. The manifest `datasets/ae-vector-registerstreams-xrefs-2025-2026.json` records binary hashes, direct CALL/JMP sites and approximate surrounding exports (SHA-256: `E73B6C9A428B208CBE5BD4147728155A19AC5310929A819F2CB0D7E53C0FF470`). The initial scan without SKIPDATA was **incomplete**, stopping after ~100k decoded instructions per version; these results were discarded and regenerated.

In *both* binaries a single disassembly region contains **consecutive direct calls** to `BEE_Layer::RegisterStreams`, `BEE_AVLayer::RegisterStreams`, `BEE_MaterialOverrideLayer::RegisterStreams`, `BEE_TextLayer::RegisterStreams`, `BEE_VectorLayer::RegisterStreams`, `BEE_CameraLayer::RegisterStreams`, etc. For example, in AE 2025 the direct vector registration call site is RVA `0x36DE38`; in AE 2026 it is `0x378858`. Inspection of surrounding instructions shows calls in precisely aligned multi-layer initialization sequences ending with a return. The **name of the enclosing internal function is not established**; the nearest preceding exported symbol is not reliable as an owning symbol.

This supports an internal **central layer registration/initialization dispatcher** in both versions. It does *not* establish an external plug-in registration contract or which fields are written. `PopulateVectorArt` has three scanned direct CALL references in each version; `BEE_VectorLayer::Rasterize2DGraph` has zero scanned direct calls, consistent with (but not proof of) a virtual/indirect dispatch path. Absent direct CALL references are not negative evidence of non-use.
