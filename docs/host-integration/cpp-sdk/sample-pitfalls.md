---
status: active
last_verified: 2026-09-16
evidence: AE 25.6 distributed samples + current Guide examples + cross-sample comparison
---
# SDK Sample Pitfalls and Fossilized Defects

Adobe samples are high-value evidence for intended call sequences, suite acquisition and host lifecycle, but **sample code is not the same thing as a normative contract**.

AEIG therefore classifies every surprising sample behavior against four independent surfaces:
1. header comments / ABI contract;
2. Guide prose;
3. another Adobe sample or sibling-host implementation;
4. controlled runtime behavior.

Only after that comparison should sample behavior become developer guidance.

## Compute Cache: `sizeof(pointer)` seed trap
The current Compute Cache example declares a seed as `const char* hash_buffer = "Level2Histo"` and passes `sizeof(hash_buffer)` to `AEGP_CreateHashFromPtr()`.

In C/C++, `sizeof(hash_buffer)` is the size of the pointer object, **not the byte length of the string contents**.

This may still produce a deterministic class seed on a fixed architecture, but it does not hash the complete literal as a reader might assume from the surrounding prose.
Production code that intends to hash the text should pass an explicit byte length (`strlen`, array extent including/excluding NUL by design, or a fixed canonical byte sequence). More importantly, a Compute Cache key must mix **all semantic inputs**, not rely on a recognizable seed alone.

## SmartyPants dynamic-flags bitmask
The retained 25.6 SmartyPants sample uses:

`out_flags2 &= PF_OutFlag2_DOESNT_NEED_EMPTY_PIXELS`

inside dynamic flag handling. That operation retains only the target bit from the existing mask rather than conventionally setting it (`|=`) or clearing it (`&= ~`).

A sibling sample uses the expected clear form, and SmartyPants does not establish the target bit in Global Setup. AEIG therefore treats this as a high-confidence **source-level defect candidate**, not as evidence of some special host bitmask semantics.

The correct lesson is not merely “this line is wrong”; it is that sample code can preserve a fossilized mistake for years and should be mechanically checked against bitmask algebra and header contract.

## SDK_IO auxiliary-data scaffold
The AEIO sample advertises auxiliary-data capability but leaves the corresponding callbacks incomplete/unset. This demonstrates feature scaffolding, not a complete production implementation.

Do not infer that every advertised sample flag has a working end-to-end demonstration.
## Common sample-era traps
Even when logically correct, sample code may encode assumptions that should not be copied blindly:
- single-threaded/pre-MFR ownership patterns;
- fixed pixel depth or row layout;
- legacy suite generation acquisition;
- incomplete error propagation/cleanup for readability;
- UI-thread-only behavior presented without explicit thread qualification;
- platform/resource packaging that predates current signing/loading requirements;
- mutation of sequence/global state that modern render concurrency makes unsafe.

## Production adoption checklist
Before copying a sample pattern:
1. identify the exact SDK/AE generation the sample targets;
2. read the header comment for each suite/function/flag used;
3. check whether a newer suite generation changes ownership or threading;
4. inspect every pointer/size/lifetime calculation independently;
5. test MFR/reentrancy if render code is involved;
6. run 8/16/32-bpc and nontrivial rowbytes where pixels are involved;
7. verify cleanup on every error path;
8. compare behavior in the actual target host/version.

## Evidence discipline
A sample can prove that Adobe expected a call sequence or feature family to exist. It cannot, by itself, prove the sample is bug-free, that an internal algorithm works exactly that way, or that the pattern is current best practice.

AEIG records sample defects as developer hazards while keeping the underlying public API contract separate.

Cross-links: `suite-versioning-and-abi.md`, `host-reimplementation-failure-patterns.md`, `performance-and-escape-hatches.md`, `../../mfr/state-ownership.md`, `../../image-pipeline/pixel-formats.md`.

## Verified corrections and numerical counterexamples

The [source repair study](verified-sample-repairs.md) now provides a pinned-source patch and compiled extracted-code regressions for SmartyPants. It additionally identifies two concrete Alpha blend inconsistencies: the 16-bpc weights sum to 255 before division by 256, and the 32-bpc Alpha path ignores Blend. A common affine expression restores the intended interpolation while preserving the sample's integer quantization.

The dynamic-mask correction preserves unrelated bits, but DOESNT_NEED_EMPTY_PIXELS is obsolete for SmartFX in the current Guide, so no current-host pixel or performance impact is inferred from that flag expression alone. The Compute Cache example correction makes the literal byte length explicit; it does not prove hash uniqueness or a previously observed cache failure.

All corrections live in experiments/sdk-contract-fixes rather than the original SDK. The package distinguishes source-level validation from a completed AE host test.
