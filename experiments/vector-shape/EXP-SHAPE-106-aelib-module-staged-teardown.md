# EXP-SHAPE-106 — First-party aelib lifecycle staging and reverse teardown

**Result: PASS in both installed Windows AE2025 and AE2026 original images; offline x64 static verification only.**

## Test purpose

Distinguish the actual module lifecycle order from raw callsite address order. Determine where TDB, OM, FLT, BEE and general AEGP/plugin setdown sit in the real native host stage machine. This extends F-VECTOR-073/074 and gives concrete lifetime boundaries for the Undo-owned Stream teardown chain in F-VECTOR-099–104.

## Source and method

- Inspect the original SHA-pinned `aelib.dll` files from installed AE2025/AE2026.
- Resolve true C++ `InitIterator::operator++`, `TerminateIterator::operator--`, `TerminateIterator::backward` and `aelib::Terminate` exports.
- Decode each native 35-case x64 switch/jump table and its case-number / callsite relationship.
- Verify actual imported `TDB_Birth/Death`, `OM_Birth/Death`, `FLT_Birth/Death`, `BEE_Birth/Death` calls by CAPSTONE instruction boundaries and RIP-relative IAT.
- Verify the reverse iterator's one-based N → N-1 transition and its invocation in the termination loop.
- Confirm that Stage 32 invokes `MEE_AEGP_Death → MEE_AEGP_Terminate → SetdownGeneralPlugins`.

## Observed stage mapping

| Stage | Birth | Death |
| ---: | --- | --- |
| 15 | TDB_Birth | TDB_Death |
| 25 | OM_Birth | OM_Death |
| 27 | FLT_Birth | FLT_Death |
| 29 | BEE_Birth | BEE_Death |
| 32 | Other first-party startup work | AEGP Death, AEGP Terminate, general plugin Setdown |

**Normal full initialization advances stages; termination descends from highest initialized stage.**

### Safety and limits

No Adobe code was executed, no AEX was installed, and no project or Adobe executable was changed. This static native ordering does not establish a safe third-party C++ Stream provider or physical module unloading. A general plugin setdown callback does not prove all authored/detached/Undo-owned native Stream objects are gone.

## Reproduce

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_aelib_native_staged_init_reverse_teardown.py"
```

Machine receipts: `datasets/ae-aelib-native-staged-birth-reverse-death-2025-2026.json`.

Architecture reference: `docs/architecture/native-module-startup-shutdown.md`.

Detailed finding: `research/findings/F-VECTOR-106-aelib-staged-native-initialization-reverse-module-teardown.md`.
