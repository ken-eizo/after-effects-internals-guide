---
date: 2026-10-15
status: PASS strict pinned AE2025/AE2026 TDB native archive error-policy flag differences; not an actual corrupt AEP host test
evidence: E2-L original installed Windows PE export, x64 calling ABI, caller flag and actual U.dll error branch
---

# F-VECTOR-100 — Unknown Stream class during native archive load: Named and Indexed use different error-report flags

## Key finding

Both Adobe native group loaders invoke TDB_StreamFactory::CreateStream(saved child MatchName). However, in both installed releases the **fifth native call argument** differs:

| Group ReadAndStore implementation | AE2025 | AE2026 |
| --- | ---: | ---: |
| TDB_NamedStreamGroup::ReadAndStore | 0 | 0 |
| TDB_IndexedStreamGroup::ReadAndStore | 1 | 1 |

The actual TDB_StreamFactory::CreateStream implementation tests this same argument in its **missing-Creator** branch. With flag 0, a conditional jump skips an error-report block; with flag 1 the branch reaches a call to the Adobe U.dll imported **Up_ReportCoSAErrString** routine. The parameter is also checked when a registered Creator returns a null object.

This is not a guessed proximity of unrelated bytes. The verifier confirms both caller's explicit assignment of [rsp+0x20] just before the factory call and the callee's seven-push Win64 prologue, including lea rbp,[rsp-0xD0]. The callee reads [rbp+0x130], which maps to its entry [rsp+0x28] — exactly the caller's [rsp+0x20] fifth argument under Win64. The imported U.dll target, conditional test and branch address are verified from original code.

## Runtime-independent reconstructed control flow

~~~text
Serialized child's MatchName → virtual ReadAndStore
    Named:   CreateStream(name, report_flag=0, ...)
    Indexed: CreateStream(name, report_flag=1, ...)

Native CreateStream looks up registered Creator:
    FOUND:
        invoke registered native Creator
        if null: also checks missing/failed-Creator report flag
    MISSING:
        if report_flag=0: skip examined Adobe error-report branch
        if report_flag=1: reach Up_ReportCoSAErrString branch
~~~

This does NOT establish that a file always loads successfully when flag 0, or always throws/crashes when flag 1. The return semantics of U.dll's routine, later project-level recovery, preserved archive bytes and any UI dialog require an actual isolated disposable host fixture.

## Exact machine-code anchors

| Evidence | AE2025 RVA | AE2026 RVA |
| --- | --- | --- |
| Factory CreateStream | 0x26710 | 0x27920 |
| Missing-Creator flag comparison | 0x267ED | 0x27B61 |
| Conditional skip when zero | 0x267F4 | 0x27B68 |
| U.dll error-report callsite | 0x26842 | 0x27BB6 |
| Null Creator-result flag comparison | 0x268E2 | 0x27A5B |
| Named loader sets fifth flag to zero | 0x3D7C9 | 0x3E31E |
| Named loader's CreateStream call | 0x3D7DE | 0x3E333 |
| Indexed loader sets fifth flag to one | 0x3D702 | 0x3E277 |
| Indexed loader's CreateStream call | 0x3D717 | 0x3E28C |

## Implementation implications

A foreign native class must have its Creator available at **project load time**, not just during later menu execution. Otherwise a native Indexed parent attempts loading an unknown type with an error-report-enabled path. A named parent suppresses this particular reporting branch but still cannot reconstruct a nonexistent C++ class from nothing.

A standalone custom CNL-type mock, a permissive AEGP_CanAddStream, or a successful TDB factory registration alone does not prove that unsupported foreign data round-trips safely through native AEP save/open or Undo.

## Reproduction / scope

Run: experiments/vector-shape/probe-src/tools/verify_tdb_archive_missing_creator_error_policy.py

JSON proof: datasets/ae-tdb-archive-unregistered-creator-report-gate-2025-2026.json

Result PASS 2/2 (AE2025/AE2026 Windows). No private Adobe runtime function invoked; no project altered. Product status NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM. Companion feature reference: Native Archive Type Compatibility.
