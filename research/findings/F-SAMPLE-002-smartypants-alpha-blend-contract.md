---
status: source-repair-verified
evidence_grade: E0-S + E2-X
confidence: high-within-stated-domain
versions: "AE 25.6 distributed SmartyPants sample; pinned source"
last_verified: 2026-09-22
---
# F-SAMPLE-002 — Alpha blend disagrees across pixel depths

## Statement

The 16-bpc Alpha branch uses weights summing to 255 while dividing by 256. The 32-bpc Alpha branch ignores Blend entirely; its subsequent blend block excludes Alpha. At a = 0, b = 0, the 16-bpc branch returns 32640 instead of 32768. At a = 0.25, b = 128, the float branch returns 0.75 instead of 0.5. Both are reachable interior/wrapper-compatible counterexamples.

## Repair and proof

For normalized alpha, use H(a,b;M) = (b*a + (256-b)*(M-a))/256, with b in [0,256]. Convexity preserves [0,M]. Integer flooring introduces less than one channel unit of error. The 16-bpc numerator never exceeds 8388608, so it fits a signed 32-bit intermediate. Preserve the sample's existing UI quantization.

The source-locked repair and compiled extracted-code regression are in experiments/sdk-contract-fixes. Exhaustive integer and selected float tests are recorded in its results/regression.json. The independent integration runner re-extracts these branches after all newer repairs are composed.

## Boundary

This verifies the source equation under finite normalized alpha, not arbitrary HDR alpha or every color mode. ActuallyRender bypasses kernels at b = 256. No AE host or installed production effect was tested or changed.

See [Verified SDK Sample Repairs](../../docs/host-integration/cpp-sdk/verified-sample-repairs.md) and [render contract repairs](../../docs/host-integration/cpp-sdk/verified-render-contracts.md).
