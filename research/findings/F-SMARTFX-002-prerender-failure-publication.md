---
status: source-repair-verified
evidence_grade: E0-H + E0-S + E2-X
confidence: high-for-extracted-control-flow
versions: "AE 25.6 distributed SmartyPants; SHA-256 locked"
last_verified: 2026-09-22
---
# F-SMARTFX-002 — PreRender publishes invalid dependency results after failure

## Statement

SmartyPants PreRender ignores errors from effect-to-layer, layer-to-comp, background-color and GuidMixInPtr callbacks. It also unconditionally unions checkout rectangles after an error even though checkout results need not be initialized. Failure can be reported as success, an invalid handle can flow to a dependent callback, and failed checkout results can be consumed.

## Repair

Initialize handles/results; use the SDK ERR first-error gate for each dependency; gate parameter-dependent work and rectangle publication on success. This implements a prefix of the dependency chain and commits output metadata only after the complete chain succeeds. It does not roll back side effects performed inside successful host callbacks.

## Verification

experiments/smartfx-contract-lab extracts the complete original/corrected PreRender and compiles it against SDK callback types and ERR semantics. Its 1792 cases combine 64 failure masks, optional GUID availability, Alpha/RGB mode, and seven rectangle shapes. The original reports 210 false successes; corrected return, trace, publication, request and invalid-result-consumption checks all pass. Results record overlapping failure classes, which must not be summed as unique failures.

A Union spy catches attempts to consume invalid results before reading fields: these are deterministic control-flow observations, not execution of undefined uninitialized reads. Suite acquisition is mocked; AE scheduling and the host's failure frequency remain unmeasured.

## Related boundary

This repair establishes validity of metadata publication. It does not prove the rectangles are geometrically complete for an Alpha transform that maps zero to nonzero. F-SMARTFX-001 remains applicable.

See [render contract repairs](../../docs/host-integration/cpp-sdk/verified-render-contracts.md).
