---
status: active
last_verified: 2026-09-22
evidence: pinned AE 25.6 sample source and Guide example; algebraic counterexamples; compiled extracted-code regression
---
# Verified SDK Sample Repairs

This work repairs concrete source behavior in the distributed AE 25.6 SmartyPants example and makes the byte extent of a public Compute Cache example explicit. It is separate from changes to Adobe's installed production effects. The package retains source fingerprints, reviewable diffs, original counterexamples and corrected regression tests.

The primary deliverable is experiments/sdk-contract-fixes. Its runner produces corrected copies and evidence without modifying the original SDK or installing a plug-in into After Effects.

## What was found

| Scope | Original behavior | Correction and evidence boundary |
|---|---|---|
| SmartyPants 16-bpc Alpha | The two blend weights sum to 255 although the divisor is 256. | Use weights summing to 256; this restores the declared blend family. |
| SmartyPants 32-bpc Alpha | Alpha is inverted without using the Blend parameter; the later blend step excludes Alpha. | Apply the same affine blend as the integer-depth Alpha paths. |
| SmartyPants dynamic flags | A mask AND retains only the target bit and erases unrelated bits. | Clear only the intended bit, preserving every unrelated flag. |
| Guide Compute Cache seed | The call uses the pointer's size as the text length. | Use the string array's explicit extent, excluding the terminator by design. This alone is not proof of a current wrong-cache result. |

The original sample evidence is SmartyPants.cpp in the AE 25.6 distribution: Alpha equations near lines 427, 553 and 695; the post-channel blend near line 800; the Blend conversion and full-copy branch near lines 859–873; dynamic flags near line 1100. The package records the exact source SHA-256 so line numbers cannot silently substitute for version identity.

The Compute Cache example is a Guide code example, not a discovered implementation of Adobe's internal hash function. The [current public example](https://ae-plugins.docsforadobe.dev/effect-details/compute-cache-api/) still exhibits the pointer-size pattern. A full fixed-architecture seed can be deterministic even if truncated, so the correction's scope is the intended byte sequence.

## Numerical derivation: one meaning of Blend at every depth

The sample's UI Blend value is converted to an integer b by truncating 2.56 times the percentage. Therefore the relevant kernel parameter is b in [0, 256], not a continuous percentage. This repair preserves that existing quantization.

For a channel with maximum M and alpha a, define the ideal alpha as

    H(a, b; M) = (b*a + (256-b)*(M-a)) / 256.

This blends from inversion at b = 0 to the original at b = 256. At b = 128 it equals M/2 for every input alpha. The coefficients are nonnegative and sum to one after normalization, so for 0 <= a <= M the result stays in [0, M].

For 8-bpc and 16-bpc integer channels the implementation takes the floor of H. The resulting error relative to the real expression is less than one channel unit. The SDK uses M = 255 and M = 32768 respectively; AE's 16-bpc convention must not be replaced with 65535.

For 32-bpc alpha, M = 1 and floating-point rounding applies. This is a common real-valued expression with depth-specific quantization, not a claim of bitwise identity between arbitrary depth conversions. Finite normalized alpha is the stated numerical test domain. NaN, infinities, out-of-range data and unrelated HDR color conversions are outside this repair.

### A reachable 16-bpc counterexample

At a = 0 and b = 0, the original expression gives

    (255 * 32768) >> 8 = 32640.

The correctly inverted alpha is 32768. The 128-unit discrepancy is not an unavoidable 8-to-16-bit quantization difference: it comes from the coefficient sum being one too small. Changing the coefficient to 256 gives 32768 exactly.

The corrected numerator is nonnegative and at most 256 * 32768 = 8,388,608, which fits in a signed 32-bit integer under the SDK's ordinary integer promotions. Thus the right shift implements division by 256 without a negative-shift interpretation or an arithmetic overflow for the stated domain.

### A reachable 32-bpc counterexample

At a = 0.25 and b = 128 (50% UI Blend), the original alpha path returns 0.75. The common equation gives 0.5. The later blend block excludes the Alpha channel, so it does not repair this difference.

This counterexample uses an interior blend value. ActuallyRender copies the original image when b = 256 and bypasses the inversion kernels. A failure demonstrated only by calling a kernel at b = 256 would not, by itself, show the same visible failure through the wrapper. The package preserves this distinction.

### What the repair preserves

The Alpha branch copies the incoming pixel first and changes alpha only. The repair therefore preserves the sample's existing RGB behavior and quantization policy. It does not redefine premultiplication conventions, all channel modes, image iteration, ROI behavior, render sequence ownership or the sample's MFR compatibility.

This is a source-level repair to a precisely specified branch. Claiming that every path in SmartyPants is now correct would require substantially broader analysis.

## Finite-mask derivation: change only the named flag

Let x be a fixed-width unsigned flag vector and m the mask to clear. Define

    clear(x, m) = x AND (NOT m).

Then

    clear(x, m) AND m = 0
    clear(x, m) AND (NOT m) = x AND (NOT m).

These identities prove both the intended change and preservation of unrelated flags. In contrast, x AND m generally erases every bit outside m. If x contains an unrelated flag while the target bit is absent, the original expression collapses x to zero.

The Alpha rendering path can turn zero alpha into nonzero alpha, so treating empty input pixels as irrelevant is not appropriate for that operation. The repair clears the target bit in that branch and does not introduce an optimization in other branches.

There is a critical version/context limitation: the current [PF_OutData Guide](https://ae-plugins.docsforadobe.dev/effect-basics/PF_OutData/) marks DOESNT_NEED_EMPTY_PIXELS obsolete for SmartFX, and SmartyPants is a SmartFX sample. The algebraic defect and unrelated-bit destruction are demonstrable; a current-host rendering or speed impact from that callback requires a host experiment. The sample also does not advertise the target flag at Global Setup, so the patch must not silently start toggling it on.

The proof is finite Boolean algebra applied to C++ mask semantics, not a newly solved mathematical conjecture.

## Explicit byte extents: before the hash

A pointer's sizeof is the storage occupied by that pointer type, not the length of its pointed-to text. For a char array initialized by a literal, sizeof(array) minus one describes that literal's bytes excluding the terminating NUL. [C++ sizeof specification](https://eel.is/c++draft/expr.sizeof).

The repair makes this choice explicit. It removes architecture-dependent truncation of the intended seed. It does not prove that the hash is collision-free, that every semantic computation input has been included, or that cached entries across classes are interchangeable. The SDK's all-inputs contract still has to be satisfied by each plug-in.

The existing literal is long enough for the observed pointer-size read. It would be misleading to call that specific example an observed out-of-bounds read. Shorter strings copied into the same general pattern would require a separate analysis.

## Verification and provenance

The source repair package:

1. validates expected source hashes and exact replacement counts;
2. retains minimal diffs and corrected copies outside the SDK;
3. extracts the relevant expressions from actual original and corrected source;
4. compiles the test harness and checks original counterexamples;
5. compares corrected behavior against independently stated mathematical invariants;
6. records compiler information, tested domains and the absence of an AE host run.

Finite exhaustive tests apply only to the enumerated integer domains and parameter values. Floating-point tests are numerical tests over recorded inputs and tolerances, not exhaustive proofs over every possible float. Algebraic arguments explain the repair beyond examples; they do not formally verify the compiler, host callbacks or allocation behavior.

Follow the package README to reproduce the evidence on the pinned corpus. Original source hashes and tested copied-source hashes are required before reusing a patch on another SDK release. A hash mismatch is a review requirement, not a reason to apply a fuzzy replacement to an unknown file.

## Relation to the wider resolution program

[The resolution register](../../reference/radical-resolution-register.md) retains all rows of the three existing issue/frontier/capability registries and explicitly labelled boundary sections. It distinguishes source fixes from host verification, corpus gaps, historical behavior and supported contracts.

[Certified memory planning](../../render-graph/verified-memory-planning.md) addresses a separate algorithmic bottleneck in a finite model. Its optimality certificate does not certify these C++ callbacks, and these source fixes do not establish the host's private render-graph policy.

The investigation did not establish a “world's hardest” ranking or solve all After Effects implementation problems. Its concrete advancement is a set of reproducible source repairs plus better independently checkable algorithms. New host claims require new host evidence.

## Remaining verification boundary

After Effects has not been used to execute the corrected plug-in in this experiment. No installed Adobe binary or active project was modified. A source-level counterexample is strong evidence about the source expression and its reachable wrapper conditions; it is not a substitute for testing the compiled effect under the intended host version.

Before production use, run a disposable host fixture covering 8/16/32-bpc output, multiple Blend values, transparent inputs, rowbytes, ROI and receipt lifetime. Preserve reference images and verify unrelated channels. These requirements remain open rather than being labelled complete by this document.
