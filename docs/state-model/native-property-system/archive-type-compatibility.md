---
status: internal-implementation-reference
last_verified: 2026-10-15
evidence: E2-L + H
versions: Windows AE2025 / AE2026 TDB archives; no unknown custom AEP executed in host
---

# Native Archive Type Compatibility — Missing Stream Creators

Native After Effects StreamGroup archive loading is **type-aware**. A saved child MatchName is used to locate an existing registered C++ Creator, build a new TDB_StreamBase and read its archived data. This internal implementation is not a supported API for authoring or migrating arbitrary new native properties.

## Built-in type reconstruction

~~~text
TDB_StreamGroup::Read
  → read the saved child's TDB_MatchName
  → dispatch virtual ReadAndStore for parent grouping type
  → TDB_StreamFactory::CreateStream(saved child MatchName)
  → if an object is created: group-specific attach/read operations
~~~

Indexed groups call GetNumStreams and InsertStream, which enforces CanStore and native parent ownership, before invoking the child's Read method. Named groups have different logic for already present canonical child entries and may call UpgradeChildStream. See [Native Property Serialization](document-stream-serialization.md).

## Missing-Creator error-report policy varies with parent kind

Both AE2025 and AE2026 pass **different values for the same native CreateStream argument** during archive reconstruction.

| Parent grouping type | Fifth native argument passed by ReadAndStore | Effect in examined CreateStream error branch |
| --- | ---: | --- |
| TDB_NamedStreamGroup | 0 | Bypasses the checked U.dll report branch |
| TDB_IndexedStreamGroup | 1 | Enables the checked U.dll report branch |

This result is based on actual Win64 calling convention and disassembled instructions: caller [rsp+0x20] is callee fifth argument [rsp-on-entry+0x28], which matches CreateStream's local [rbp+0x130] after its seven-push setup.

For an unknown MatchName, the factory's code tests that argument. The enabled path calls Adobe's private **U.dll!Up_ReportCoSAErrString**. When the Creator is present but returns null, the same flag is consulted elsewhere.

**Do not interpret this as an automatic safe fallback.** We have not executed malformed AEP archive loads or the U.dll error routine in a disposable host, so the effect on user dialogs, thrown errors, project load abort, data preservation or Undo is unknown.

## Versioned code markers

| Native instruction | AE2025 TDB RVA | AE2026 TDB RVA |
| --- | --- | --- |
| CreateStream entry | 0x26710 | 0x27920 |
| Flag branch for absent Creator | 0x267ED | 0x27B61 |
| Jump to bypass report when flag zero | 0x267F4 | 0x27B68 |
| Up_ReportCoSAErrString callsite | 0x26842 | 0x27BB6 |
| Named loader passes flag zero | 0x3D7C9 | 0x3E31E |
| Indexed loader passes flag one | 0x3D702 | 0x3E277 |

Source proof F-VECTOR-100; independently executable, original-DLL SHA-pinned verifier at experiments/vector-shape/probe-src/tools/verify_tdb_archive_missing_creator_error_policy.py. Dataset: datasets/ae-tdb-archive-unregistered-creator-report-gate-2025-2026.json.

## Practical consequences for a new native type provider

A truly native plugin-defined property would require all of the following: (a) registered Creator at the correct **project-load phase**, (b) the owning group's CanStore and canonical admission, (c) a serialized type/keyframe/expression/archive format that can be read back, and (d) valid project and Undo object lifetimes until all affected objects have been released.

Public AEGP effect parameters and external panels are different supported mechanisms; they do **not** automatically satisfy private TDB archive registration requirements.

## Safe acceptance criteria

An actual unknown/foreign type experiment should be run only on a **disposable isolated installation** with scratch AEP fixtures, digest-logged before/after archive contents, an automatic revert plan and crash capture. First establish whether U.dll error-reporting returns, throws, or displays a host-level error and whether other saved group children survive reopening.

**Current result is E2-L static only**, not a real AEP roundtrip or proof that arbitrary foreign C++ Stream classes can be registered. The user project and Adobe binaries are unchanged.

Related: [Document Serialization](document-stream-serialization.md), [Native Instance Creation](stream-instance-creation.md), [Factory Registration Lifetime](factory-registration-lifetime.md), [Indexed Group Insertion](indexed-group-insertion.md), [Evidence & Version Matrix](verification-and-version-matrix.md).
