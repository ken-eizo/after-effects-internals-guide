---
status: source-repair-verified
evidence_grade: E0-H + E0-S + E2-X
confidence: high-for-null-contract-and-local-state
versions: "AE 25.6 distributed SmartyPants and AE_Effect.h"
last_verified: 2026-09-22
---
# F-THREAD-004 — Threaded SmartyPants rejects a contract-valid null sequence handle

## Statement

GlobalSetup advertises SUPPORTS_THREADED_RENDERING. The distributed AE_Effect.h contract says render-time in_data->sequence_data is NULL and read-only sequence state is available through PF_EffectSequenceDataSuite. ActuallyRender nevertheless treats a null sequence handle as PF_Err_INTERNAL_STRUCT_DAMAGED and uses that handle as mutable kernel parameter storage.

The null-handle contradiction is sufficient to establish the source defect. No assumption about actual host sharing of a nonnull handle is required.

## Repair and argument

Allocate the parameter state within each ActuallyRender invocation and initialize channel/blend from checked-out parameters. These kernels do not require the persistent table/cache members. Synchronous iteration ends before the local state lifetime ends. Therefore nested or concurrent invocations have disjoint parameter storage; one invocation's assignments cannot modify another invocation's channel or blend.

This avoids a lock around host callbacks and avoids requesting mutable per-thread sequence replicas for data that does not require them.

## Verification

experiments/sdk-lifecycle-lab extracts the actual ActuallyRender body and SDK struct definitions. Tests cover contract-valid null input, deterministic nested invocation with a shared nonnull handle, channel interference and sequential behavior. Nested nonnull tests are a conditional ownership model, not evidence that current AE supplies such handles or that a real host race was observed. Full translation-unit syntax is checked against SDK headers.

No plug-in binary is linked/installed, and no actual MFR session is claimed. See F-THREAD-003 and [render contract repairs](../../docs/host-integration/cpp-sdk/verified-render-contracts.md).
