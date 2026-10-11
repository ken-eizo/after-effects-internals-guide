---
status: strongly-supported-local-artifact
last_verified: 2026-10-11
evidence: E2-L + E0-H
versions: installed AE 2025 and AE 2026 BEE.dll; SDK CS6/CC2014/25.6
---
# F-VECTOR-004 — RegisterStreams routines exist across layer classes and versions

## Confirmed E2-L

Local export records establish these distinct symbols in **both** 2025 and 2026 BEE DLLs:

- \`BEE_VectorLayer::RegisterStreams()\`
- \`BEE_TextLayer::RegisterStreams()\`
- \`BEE_AVLayer::RegisterStreams(char const*)\` (exact decorated ABI captured in dataset)
- \`BEE_Layer::RegisterStreams(bool)\`
- \`BEE_VectorStream::PopulateVectorArt(...)\`
- \`BEE_VectorLayer::Rasterize2DGraph(...)\`

The latest source of exact raw decorated names and RVA values is \`datasets/ae-shape-native-extension-lineage-2026.json\` and \`datasets/ae-vector-registerstreams-static-2025-2026.json\`.

The \`RegisterStreams\` symbol alone **does not** prove a type registry that a plug-in may augment. Bounded, offline disassembly of the vector routine shows calls to stream expression, keyframe and flag **command handlers**; \`BEE_AVLayer::RegisterStreams\` calls the indexed-group reorder command. It may be concerned with command binding. More reverse call-graph / data-write evidence is needed before choosing among factory, command, and mixed registry models.

## Important version and ABI limit

2025 and 2026 have different RVAs despite persistent named functions; a compiler-generated export is not an SDK entrypoint or guaranteed signature/lifetime/calling contract. A thunk, initialization ordering or internal host ownership could make a function unusable externally even if callable.

## Refutation tests

H-factory: locate an actual insertion of a third-party type descriptor and demonstrate that a new host-owned indexed group is recognized by native Timeline and project serialization without native Shape Layer creation. If only existing IDs register built-in commands, H-factory fails.

H-command: trace registration writes to a command dispatcher, and show no novel type factory storage; refuted by observed new stream-type registration via that function.

These tests are separate from reading existing paths. No native extension experiment has passed.
