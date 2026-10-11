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
