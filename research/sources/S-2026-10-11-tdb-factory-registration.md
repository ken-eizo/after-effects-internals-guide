---
status: source-index
last_verified: 2026-10-11
---
# Evidence provenance: TDB host-native type creator registration

| Ref | Class | Material | Establishes | Does NOT establish |
| --- | --- | --- | --- | --- |
| TDB-01 | E2-L | Installed AE2025 `TDB.dll` SHA-256 `2ed19824997f3de797a75fef6f22d4d11ac8548c9d35f6093aa2afc1a6ed2e69` | Internal TDB StreamFactory and Scoped register exports | Supported plugin ABI |
| TDB-02 | E2-L | Installed AE2026 `TDB.dll` SHA-256 `82677a20bdf871878b579522c4b4e0def8af0a50a810e3b9972da1170f546c1b` | Same factory registration family in a later binary | ABI stability |
| TDB-03 | E2-L | `datasets/ae-bee-registerstreams-iat-targets-2025-2026.json` | BEE->TDB resolved import call chain | Runtime host execution or arbitrary registration |
| TDB-04 | E2-L | `datasets/ae-tdb-register-callsite-disasm-2025-2026.json` | Register->RegisterFactoryFunc->CreateStream and unregister control | Private layout/ownership |
| TDB-05 | E2-L | `datasets/ae-tdb-vector-canstore-disasm-2025-2026.json` and locally decoded RIP strings | Shape parent candidate-name prefix rules | Unknown custom-name acceptance |
| TDB-05b | E2-L | `datasets/ae-vector-canstore-prefix-literals-2025-2026.json` | Exact Shape/Graphic/Filter ASCII constants and RIP instruction RVAs in both BEE versions | Runtime external unknown-name admission |
| TDB-06 | E2-X | Three archived AE2026 ShapeLayerAE v2 TSV logs: `experiments/vector-shape/runs/EXP-SHAPE-005/20261011-user-host-v2/` | Existing group CanAdd matrix, zero UID anomaly | Factory type registration or native tool integration |
| TDB-07 | E0-H | Adobe SDK 25.6 `AE_GeneralPlug.h` | AEGP typed stream/CanAdd/get UID contract | Private TDB implementation |
| TDB-08 | E0-G | https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/ | Published AEGP suite limits | Supported custom native Indexed Group constructor |
| TDB-09 | H | `H-SHAPE-005-creator-registration-native-contents.md` | Falsifiable model for plugin-origin native stream types | Demonstration of capability |

No Adobe binary, private headers, or proprietary DLL contents are redistributed as generated source artifacts. Disassembly and symbol inventories are derived forensic evidence only.

## 2026-10-11 v3 host and creator/evaluation boundary source additions

| Ref | Class | Source | Claim boundary |
| --- | --- | --- | --- |
| TDB-10 | E2-X | `experiments/vector-shape/runs/EXP-SHAPE-009-010/20261011-user-host-v3/ShapeLayerAE_private_factory_probe.tsv` SHA256 `390bb93c2de843cb55aa50983173e7af50348122a63d277bc81c1cefd8eba017` | External AEGP invoked the **private no-argument getter**; returned non-null; no registration or dereference. |
| TDB-11 | E2-X | `.../ShapeLayerAE_canadd_unknown.tsv` SHA256 `9a229ded137d826ac9c8d4d006e4891d167295c5cfbf98a1d952513aad2f0095` | Unknown native Shape/Graphic/Filter prefixes accepted in existing Contents; not created. |
| TDB-12 | E2-X | `.../ShapeLayerAE_stream_metadata.tsv` SHA256 `1a5355c8a6ff0810285cd68aa47b240c93b83952ac16462a6a95efd96c4a4816` | 359/359 public session ID returned 0 twice, each API error 0; cause unresolved. |
| TDB-13 | E2-L | `datasets/ae-vector-creator-registration-bundles-2025-2026.json` SHA256 `B51DC197A4826AB399CC45A3FC294EF3F085730637BA39A1D3E7596940A92286` | Built-in typed vector creator callbacks referenced within BEE functions repeatedly importing TDB `Register`. |
| TDB-14 | E2-L | `datasets/ae-vectorart-render-entry-calls-2025-2026.json` SHA256 `70482A8AE5C5408B74A7F7E76C5363E82B6BCE21AF29DFBFA2FFA2A95ABCB787` | GetVectorArt creates TDB stream path, calls PopulateVectorArt and GetBounds. |

## Dual-registry evaluator code and RTTI provenance (E2-L, 2026-10-11)

- `datasets/ae-tdb-factory-lifetime-canonical-controlflow-2025-2026.json`: TDB eager CreateStream/Canonical/SeparatedDimensions registrar and unregister control flow in both installed versions.
- `datasets/ae-vector-stream-populate-dispatch-2025-2026.json`, `datasets/ae-native-vector-populate-recursive-helpers-2025-2026.json`: private native traversal, MatchName evaluator lookup, vtable dispatch.
- `datasets/ae-vector-evaluator-registry-xrefs-2025-2026.json`: bounded-memory full PE x64 code xrefs, 20 native BEE evaluator registration sites in 2025 and 2026; identifies global registry constructor and users.
- `datasets/ae-native-vector-evaluator-registry-lifecycle-2025-2026.json`: BEE evaluator registry initialization, tree ownership and shutdown.
- `datasets/ae-native-vector-evaluator-registration-records-2025-2026.json`: each evaluator registrar callsite and its static MatchName global RVA in both versions.
- `datasets/ae-vector-evaluator-matchname-xrefs-2025.json` and `...2026.json`: source code xrefs connecting static C++ MatchName globals to initializers/registrars.
- `datasets/ae-vector-evaluator-matchname-identities-2025-2026.json`: 20 exact native operator MatchNames, same identity order in both versions, with constructor literal addresses.
- `datasets/ae-native-vector-evaluator-vtable-rtti-2025-2026.json`: callsite-local polymorphic operator vtables, concrete MSVC RTTI classes, multiple-subobject offsets, `PathFilterOperatorT<Params>` intermediate types. Derived from installed binary only, **not a stable external ABI**.

Reproduction source: `experiments/vector-shape/probe-src/tools`, recorded in `SOURCE_SNAPSHOT.json`. Evidence interpretation: `research/findings/F-VECTOR-013-tdb-eager-canonical-lifecycle.md` and `F-VECTOR-014-dual-native-vector-evaluator-registry.md`. These are **static internal Adobe implementations**, never private registration exercised from external plug-in; distinct earlier E2-X TDB getter and CanAdd read-only experiments remain separate.

## 2026-10-11 third phase: evaluator vtables, RTTI and origin construction in concrete algorithms

The local AE2025 and AE2026 BEE.dll runtime static experiments establish 20 concrete primary/secondary `BEE_VectorStream::*Operator` vtables, with a second RTTI subobject at offset 24 bytes and a common dvacore reference-counted class family. Every primary vtable has a mode dispatch at `+0x18`: **9 Group/Shape/Graphic operators test integer mode 0; 11 Filters compare mode 1**. Concrete vector generators use further polymorphic functions at `+0x20`; Filter evaluations use further methods at `+0x28` or shared dispatcher. The exact second argument representation is read from machine code and not a published external C++ enum or class contract.

`ShapeOperator`, `RectOperator` and `EllipseOperator` concrete evaluation call sequences include `GetPathDataFromOM` / `GetRectPathData` / `GetEllipsePathData` to produce `CAIMBezierPath`, native `BEE_VectorArt::Path` construction, `OriginInfo(TDB_StreamIDPath)` and `SetOriginInfo`. Repeater's native concrete filter algorithm **directly** calls `AppendSyntheticIndex` twice in both AE2025/AE2026 while constructing derived art groups and setting origin/opacity. This is stronger than prior synthetic-ID speculation, but does not establish Pen-tool selection or that effects can own native BEE VectorArt.

Evidence datasets:
- `datasets/ae-vector-evaluator-vtable-slot-map-2025-2026.json`
- `datasets/ae-native-vector-evaluator-virtual-evaluation-2025-2026.json`
- `datasets/ae-vector-evaluator-mode-abi-2025-2026.json`
- `datasets/ae-native-vector-operator-rtti-inheritance-2025-2026.json`
- `datasets/ae-vector-operator-vectorart-provenance-calls-2025-2026.json`

Reproduction scripts mirrored at `experiments/vector-shape/probe-src/tools`; findings F-VECTOR-015/016 and experiments EXP-SHAPE-015/016. This is local, read-only reverse-engineering against the user's installed binary only; **no private function call** was performed in AE, no Adobe binary or header committed. Official external chronology: https://github.com/AdobeDocs/after-effects-feature-history (Shape Layers introduced AE CS3/8.0 in 2007). Current native SVG import documentation: https://helpx.adobe.com/after-effects/desktop/import-files/import-svg-files/import-svg-files.html — imports as editable Shape Layers, **not** effect-owned native vector output.
