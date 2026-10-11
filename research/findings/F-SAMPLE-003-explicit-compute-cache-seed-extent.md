---
status: source-policy-verified
evidence_grade: E0-G + E2-X
confidence: high-for-byte-extent-only
versions: "Pinned public Compute Cache Guide example"
last_verified: 2026-09-22
---
# F-SAMPLE-003 — Define the Compute Cache seed's byte extent explicitly

## Statement

The Guide example declares a pointer to "Level2Histo" and passes sizeof(pointer) to AEGP_CreateHashFromPtr. This hashes eight bytes on the tested 64-bit target rather than the literal's eleven non-terminator bytes.

## Repair and verification

Declare a char array and pass sizeof(array)-1. experiments/sdk-contract-fixes checks the original pointer-size behavior and the corrected exact byte sequence. The correction implements an explicit full-literal seed policy.

## Boundary

A truncated constant seed can still be deterministic and adequate as one domain separator. This evidence does not establish a hash collision, stale cache hit, architecture-independent serialized key requirement, or internal Adobe hash defect. Changing the seed also changes cache identity; consumers must handle this intentionally.

[Compute Cache Guide](https://ae-plugins.docsforadobe.dev/effect-details/compute-cache-api/) and [scoped repair](../../docs/host-integration/cpp-sdk/verified-sample-repairs.md).
