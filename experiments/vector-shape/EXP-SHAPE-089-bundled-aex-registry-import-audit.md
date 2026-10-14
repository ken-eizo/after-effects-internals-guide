# EXP-SHAPE-089 — Native TDB/BEE direct registrar imports across installed AEX

**PASS static, read-only**: AE2025 **481** installed AEX, AE2026 **633** installed AEX, all PE imports parsed.

TDB direct import counts 22/23; BEE direct import counts 50/52. The exact native `TDB_ScRegisterStreams::Register` / `TDB_StreamFactory::RegisterFactoryFunc` / `UnregisterFactoryFunc` and `BEE_{AV,}Layer::RegisterStreams` functions had **zero direct AEX imports** among those modules in both installed versions.

Sources: `experiments/vector-shape/probe-src/tools/verify_aex_native_registrar_imports_2025_2026.py`.
Dataset: `datasets/ae-installed-aex-native-registry-direct-imports-2025-2026-aggregate.json`.
Privacy: original installed third-party add-on filenames are **not included** in the published dataset.

**Critical limitations:** does not scan delay-imports or dynamic symbol lookups or supported/unsupported host Suites. No private API called or user AE project touched. This does NOT prove foreign registration impossible.

Details: F-VECTOR-089.
