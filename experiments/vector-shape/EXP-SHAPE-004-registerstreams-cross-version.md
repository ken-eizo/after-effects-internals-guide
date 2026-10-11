---
status: observed-static-only
last_verified: 2026-10-11
evidence: E2-L and E0-H; no E2-X
versions: installed AE 2025 / AE 2026, SDK CS6 / CC2014 / 25.6
---
# EXP-SHAPE-004 — RegisterStreams and vector rendering lineage

Offline scripts in \`D:\Developer\ShapeLayerAE\tools\`:

- \`compare_vector_lineage.py\`: compares selected current/historical public headers and BEE binary exports; saves \`datasets/ae-shape-native-extension-lineage-2026.json\`.
- \`analyze_registerstreams.py\`: disassembles bounded windows in \`BEE.dll\` at RVAs selected from the *same exact binary version's* exports, identifies direct call targets by nearest exact exported RVA; saves \`datasets/ae-vector-registerstreams-static-2025-2026.json\`.
- \`scan_factory_extensions.py\`: prints broader factory, registration and owner candidates for discovery, without executing AE functions.

AE 2025 \`BEE.dll\` SHA-256 \`98c682351e30f38cb7021eaa142f5ec473aea92885e14915d87c157cda971730\`.
AE 2026 \`BEE.dll\` SHA-256 \`5fd8d318456228b9fd2a6733a5758f6b84206b7a8effcba5202957cd27ac680e\`.

Counted 13647 exports in 2025 and 14182 in 2026. The standard vector stream subsystem persists in both; the registered layer routines and raster boundaries have moved to new RVAs. These counts are a single *binary artifact category*, not a proof of a closed/open registry.

The 2025 vector \`RegisterStreams\` window has **115 decoded instructions / 12 calls**, the 2026 vector window **106 instructions / 12 calls**. Several direct calls resolve to \`BEE_CmdSetStreamBaseFlag\`, \`BEE_CmdSetStreamVary\`, \`BEE_ResetStream\`, \`BEE_CmdSetExpressionEnabled\`, \`BEE_CmdSetExpression\`, \`BEE_CmdSetExpressionFlags\`, and \`BEE_SelectKeyframe\`. **This contradicts a naive belief that “RegisterStreams” necessarily performs native schema/type registration.** Revisit the target's semantic name and ownership before planning private API tests.

Only limited instruction windows were decoded (until nearby exported code or 4096 bytes). Indirect call targets and register/dataflow were not resolved, and no debugger trace has confirmed runtime control-flow. Thus the experiment is E2-L static analysis only, not L5 dynamic/host observation.

Next: identify callers of \`BEE_VectorLayer::RegisterStreams\`, initialization ordering, command registration storage vs factory instance storage; compare functions against text and base AV layer registration; and separately identify VectorArt/AGM ownership and Pen-tool bind points. Any dynamic probe must be isolated and hypothesis-driven.
