---
status: pass-static-not-host-registered
last_verified: 2026-10-12
evidence: E2-L
versions: pinned AE2025 and AE2026 TDB.dll and BEE.dll
---

# EXP-SHAPE-025 — Native clone/serialization/owner and BEE evaluator lifetime contracts

## Objective

Reconstruct the actual native host contracts needed for a new plugin-owned Contents type to clone, serialize, preserve stream identity and bind vector evaluation. Does NOT create a Mask, Shape Layer or native plugin-owned object. Does NOT call private functions.

## Read-only procedure

Analyze both locally installed TDB.dll files with export symbols and .pdata-bounded disassembly for Clone/CloneStream, Read/Write (group and leaf), SetParent, SetupCanonicalLayout and IndexedGroup AppendStream. Resolve imported SLU and native helper calls. Independently decode BEE native vector registry registrar, lookup, startup and global accessor functions in both pinned BEE.dll versions. Cross-validate the two datasets through a separate script.

Sources:
- probe-src/tools/audit_tdb_clone_serialization_owner.py
- probe-src/tools/audit_bee_evaluator_registration_teardown.py
- probe-src/tools/verify_native_vector_clone_io_bee_abi.py

All stored in experiments/vector-shape/probe-src/tools; exact source DLL hashes and native RVA call edges are in corresponding datasets.

## Observations (both versions independently)

- TDB_StreamBase Clone uses the native clone virtual mechanism, TDB_Stream CloneStream uses a tracked allocator and clone-params constructor. TDB_ParamPathStream has its own path-like derived cloning logic.
- Group Read uses ReadUniqueStreamID and MatchName, and Group Write uses native SLU chunks, canonical lookup, unique IDs and end-of-group markers.
- Leaf Read/Write handles native stream value/cache/key data, HasKeys and expression state, plus stream IDs.
- SetParent has host parent-notification and rescale semantics; creating a hierarchy by assigning a raw C++ parent pointer is not equivalent to native ownership.
- Separate BEE vector evaluator registry has a MatchName-keyed registrar and lookup, stores native operator objects through polymorphic calls and has a BEE-module-owned singleton. No safe public third-party callback or unregister ABI was established.
- Direct cross-validation script PASSED for both versions.

## Pass/fail

| Required claim | Result |
| --- | --- |
| Native Stream cloning uses real derived class constructors | PASS static |
| Native Group persistence has canonical MatchName + stream-ID contract | PASS static |
| Native leaf persistence includes keyframe/expression machinery | PASS static |
| Native parent ownership has notification/rescale semantics | PASS static |
| BEE native evaluator registration separate from TDB | PASS static |
| New third-party native type actually registered in running AE | NOT TESTED |
| Own editable AE Contents inside ordinary Effect | NOT TESTED |
| Own BEE_VectorArt and host RG native rendering | NOT TESTED |

## Falsification and next gate

Public AEGP property or mask editing is insufficient. Before a live isolated host experiment, a valid private Stream class needs its native CloneStream/Read/Write/Canonical semantics plus unregister, ref-counting and owner. Even if TDB registration succeeds, effect-owned Contents and BEE vector rendering remain separate unproven gates.

Finding F-VECTOR-027, F-VECTOR-028. Datasets:
- ae-tdb-native-clone-serialization-parent-callgraph-2025-2026.json
- ae-bee-evaluator-register-shutdown-callback-abi-2025-2026.json
- ae-native-vector-owner-serialization-gates-2025-2026.json
