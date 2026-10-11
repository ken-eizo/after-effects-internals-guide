---
status: active
last_verified: 2026-09-22
evidence: pinned SDK source; header contracts; compiled extracted code; composed translation-unit syntax
---
# Verified Render Contract Repairs

AEIG now tests three interacting boundaries in the distributed AE 25.6 SmartyPants sample: dependency validity during PreRender, ownership during render, and the numerical domain of float color conversion. Each repair is tied to the exact source bytes and a reproducible counterexample. These are source repairs and explicit behavior policies; Adobe's installed production implementation has not been changed.

The integration package is experiments/aeig-integrated-repairs. Its generated workbench contains the combined corrected source. Each individual laboratory retains the original/corrected comparison. The combined runner checks patch ordering, compiles the complete translation unit against actual SDK headers, then re-extracts and executes the regression harnesses from that same combined source.

## Findings and exact scope

| Finding / registry | Defect demonstrated | Source correction | Remaining boundary |
|---|---|---|---|
| F-SMARTFX-002 / BQ-0035 | PreRender ignores dependency errors and attempts to publish failed checkout data. | Preserve the first error; stop dependent calls; publish rectangles only on success. | Host callback failure frequency, exceptions during suite acquisition, and geometric support completeness. |
| F-THREAD-004 / BQ-0036 | A threaded effect rejects the header-defined null render sequence handle. | Keep channel/blend state inside each render invocation. | Real MFR scheduling and linked plug-in behavior. |
| F-COLOR-002 / BQ-0037 | Float HLS/YIQ branches convert extended/negative RGB into an unrepresentable unsigned integer. | Float-native YIQ arithmetic; explicit input/error policy before unsafe conversion. | HDR HLS remains unsupported, and YIQ compatibility requires an intentional policy. |
| F-SAMPLE-002 / BQ-0033, BQ-0034 | 16-bpc Alpha uses an incorrect weight; float Alpha ignores Blend. | Use one affine blend equation with depth-specific rounding. | Alpha test domain is finite and normalized. |
| F-SAMPLE-001 / BQ-0029 | Clearing one dynamic flag erases unrelated bits. | AND with the complemented target mask. | The current SmartFX Guide calls this flag obsolete; current-host effect is unproved. |
| F-SAMPLE-003 / BQ-0020 | The Guide hashes pointer-size bytes of a textual seed. | Use the explicit eleven-byte literal extent. | Policy correction, not proof of an actual cache collision or stale hit. |

The last three entries are documented in [Verified SDK Sample Repairs](verified-sample-repairs.md). Compute Cache belongs to a separate example and is checked alongside the combined SmartyPants source; it is not represented as code inside SmartyPants.

## Dependency validity as a transaction

Let callback D_i produce a value needed by D_(i+1). Its output is a partial value: it is valid only if D_i succeeds. Treating failure as merely an extra integer while consuming the output breaks that dependency.

The corrected protocol evaluates a prefix of D_1,...,D_n. If D_k is the first failure, it returns that error and does not execute later dependent calls. Output rectangles are committed only if every prerequisite succeeds. A simple induction proves the trace property: ERR evaluates its argument only while err is zero, so after the first nonzero return no subsequent guarded callback runs. The final success guard then proves no failed result can reach rectangle publication.

This is a local transaction over the sample's published metadata. It does not undo successful host calls or guarantee that all host side effects are atomic.

The PreRender laboratory enumerates 1792 cases: all 64 masks of six callback failures, with/without the optional GUID callback, Alpha/RGB modes and seven input/output rectangle shapes. The original returns success incorrectly in 210 cases. The corrected code has zero violations of the measured error, callback-order, request and publication properties. A spy detects invalid result-consumption attempts before reading uninitialized storage, so the original control-flow counterexample is tested without deliberately executing that undefined read.

## Ownership as noninterference

The SDK header contract for threaded render makes in_data->sequence_data null; read-only persistent state is accessed through the sequence-data suite. SmartyPants advertises threaded rendering but its rendering function requires this handle and writes its channel/blend fields. The contract-valid null input alone establishes a mismatch.

The kernels need only the current invocation's channel and blend. Allocate these in invocation-local storage and pass its address through synchronous iteration. For distinct live invocations i and j, their storage locations are disjoint. Assignments to i's parameters cannot change j's parameters. This gives a structural noninterference argument without a mutex, thread identifier, or shared mutable cache.

The lifecycle laboratory exercises the actual rendering function with mocked suites. It covers null input, sequential cases and deterministic nested invocation. The nested nonnull case is a conditional sharing model; it does not assert that current AE exposes such a handle, and it does not deliberately run a C++ data race.

The local lifetime argument depends on synchronous iteration. Retaining the pointer in an asynchronous task would invalidate it. The currently unused persistent cache table remains an opportunity for a separate layout cleanup; this repair keeps the existing struct ABI.

## Numerical domains as part of the function signature

A_u_short represents an integer domain; PF_FpShort represents a floating domain. The expression cast(32768*x) is defined only when the truncated product is representable. An HDR red value of 2 maps to 65536, and -0.25 maps to -8192: neither is representable as an unsigned 16-bit integer. This is undefined conversion behavior, not a specified wrap or clamp. See the [C++ conversion rule](https://eel.is/c++draft/conv.fpint) and [Adobe's description of extended 32-bpc values](https://helpx.adobe.com/after-effects/desktop/adjust-colors/color-basics/color-basics.html).

The HDR laboratory defines a bounded finite float-native YIQ policy, using double intermediates and an explicit range check before output conversion. Its matrix and inverse are a chosen coherent transform. The old rounded integer route and approximate inverse are not preserved bit for bit. Migration requires an explicit compatibility decision for existing projects.

HLS is different: a lightness formula constrained by normalized white does not automatically acquire an agreed meaning above white or below black. The patch rejects unsupported HLS inputs before casting. This removes the demonstrated unsafe conversion within the stated policy but does not solve general HDR HLS behavior. Returning a pixel error also does not roll back pixels already processed; the host must treat the failed render as unsuccessful.

## Composition is checked separately

A repair that passes alone can fail when another repair changes the same function or helper. The integration runner starts from the locked original, applies the four SmartyPants patch groups in every order, and requires identical final bytes. It refuses source/hash drift and ambiguous preimages rather than guessing where a patch belongs.

This is a finite proof of order independence for this exact set of textual transformations and this source revision. It does not prove semantic commutativity for arbitrary future changes. The runner then checks the whole combined translation unit and reruns the property harnesses using code extracted from that exact combined file. Code hashes and compiler commands are retained with the results.

## Reproduce

From the repository root, run:

~~~powershell
rtk proxy python experiments/aeig-integrated-repairs/run.py
~~~

The installed AE 25.6 SDK and a compatible clang++ toolchain are required. The runner reads the SDK and writes only its own laboratory directory; it neither installs nor launches an effect. For individual original-versus-repaired tests, use the laboratory READMEs:

- experiments/smartfx-contract-lab/README.md
- experiments/sdk-lifecycle-lab/README.md
- experiments/sdk-hdr-lab/README.md
- experiments/sdk-contract-fixes/README.md

## Remaining unknowns

- A linked binary must still be tested in real AE with supported deployment/toolchain settings, MFR enabled/disabled, depth switches, cancel/error paths and representative projects.
- The Alpha transform maps zero alpha to nonzero for most blends. Its complete spatial support cannot be derived merely by forwarding input content bounds. A fix needs a defined logical output extent, sampling resolution and expanded/collapsed-transform behavior; simply substituting width and height is not established as correct.
- Full HDR HLS semantics and legacy YIQ bit compatibility are not resolved by the safety policy.
- The harnesses mock host suites and model selected errors. They do not test every suite-acquisition exception, every callback implementation, full frame rollback, or all C++ undefined behavior in the sample.
- None of these findings establishes a universal Adobe-product defect, a private-host root cause, a new mathematical open-problem solution, or completion of every AEIG frontier.

The [resolution register](../../reference/radical-resolution-register.md) keeps these scope distinctions visible. [ROI bounds](../../image-pipeline/roi-bounds.md), [state ownership](../../mfr/state-ownership.md), and [numerical behavior](../../image-pipeline/numerical-behavior.md) retain their independent host-validation obligations.
