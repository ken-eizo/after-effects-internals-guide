# EXP-SHAPE-096 — TDB Native Factory Creator/Canonical Prototype Ownership and Unregister Order

**Status: PASS strict static x64 both installed AE 2025/2026; no in-host registry mutation.**

## Native ownership pipeline

The real factory owns **Creator** and **canonical prototype** under two distinct MatchName-indexed native lookup structures:

```text
RegisterFactoryFunc()
  → insert Creator under factory+0x28
  → CreateStream() immediately constructs canonical prototype
  → insert canonical under factory+0x38
  → canonical virtual methods and SetupCanonicalLayout()
UnregisterFactoryFunc()
  → remove canonical entry at +0x38
  → remove Creator entry at +0x28
  → call canonical prototype virtual deleting destructor
```

The verifier separately traces the exact native MatchName equality search, relevant map-member address register transfers, ordered CALLs, saved prototype pointer and guarded vtable deleting destructor with the Windows x64 scalar delete `edx=1` convention.

## Reproduce

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_tdb_native_creator_canonical_lifetime.py"
```

Cross-version exact native instruction RVAs and pinned source DLL SHA in `datasets/ae-tdb-native-creator-canonical-lifetime-2025-2026.json`. Full report: `research/findings/F-VECTOR-096-tdb-factory-canonical-prototype-lifetime.md`.

The key practical warning is that the host mutates the callback registry **before** constructing a canonical instance. A constructor failure could leave partial state; a complete exception rollback mechanism is **not** demonstrated by the success-path code. Furthermore even successful unregistration is not proof all project-owned foreign instances, undo/history, or virtual callbacks have been destroyed. No safe general external AEX native-type SDK identified, no ChapeLayer native Timeline type delivered.
