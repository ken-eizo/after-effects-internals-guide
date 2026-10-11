---
status: source-repair-partial-policy
evidence_grade: E0-S + E2-X
confidence: high-for-conversion-domain-defect
versions: "AE 25.6 distributed SmartyPants float pixel path"
last_verified: 2026-09-22
---
# F-COLOR-002 — Float color branches cross an invalid integer domain

## Statement

InvertPixelFloat routes HLS and YIQ through casts of 32768 times each RGB component to A_u_short. Negative and extended HDR components can leave the representable integer range. For example R = 2 yields 65536 and R = -0.25 yields -8192. C++ floating-to-integer conversion has undefined behavior when the truncated value is unrepresentable. Such a cast is not a clipping policy.

## Repair policy

experiments/sdk-hdr-lab replaces the YIQ integer detour with a documented float-native matrix policy and bounded finite arithmetic. For HLS it explicitly rejects unsupported out-of-range input before conversion. HLS rejection is a safety boundary, not a solution to HDR hue/lightness semantics. The experiment records exact accepted domains, nonfinite handling and numerical error tests.

## Compatibility and remaining work

The new YIQ result can differ from the old quantized/inexact inverse path, including SDR. Preserving all legacy bits is not claimed. A legacy mode or versioned effect identity may be required for existing projects. General HDR HLS semantics, extreme finite values, whole-frame atomic output, other sample channels/depths and host behavior remain separate obligations.

[C++ conversion rule](https://eel.is/c++draft/conv.fpint), [Adobe color basics](https://helpx.adobe.com/after-effects/desktop/adjust-colors/color-basics/color-basics.html), and [render contract repairs](../../docs/host-integration/cpp-sdk/verified-render-contracts.md).
