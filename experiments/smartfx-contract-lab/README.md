# SmartFX dependency and metadata publication repair

F-SMARTFX-002 / BQ-0035. The pinned AE 25.6 SmartyPants PreRender function
discards failures while constructing a GUID dependency, and consumes a checkout
result even when parameter or layer checkout failed. This package repairs the
complete dependency chain and gates output rectangle publication on success.

Source identity: SmartyPants.cpp raw SHA-256
4865f3d8db8de37f5109cb34fdf04b7ae8f5b5582f12f490baa67f7f179104c2.
The original is never modified. The generated C++ copy uses LF newlines, whose
different SHA-256 is recorded separately. Prior Alpha, MFR and HDR repairs are
not bundled into this isolated patch; use the integrated overlay for composition.

## Concrete defect

Original PreRender lines 359-363 discard errors from GetEffectLayer,
GetLayerParentComp, GetCompBGColor and GuidMixInPtr. A failed operation can still
be followed by dependent work and an apparent successful return. Lines 335 and
396-397 additionally combine uninitialized or unsuccessful in_result metadata
after a parameter or layer checkout error.

The repair initializes local outputs, retains the first failure through the SDK
ERR macro, stops all subsequent service calls on that path, and performs the two
rectangle unions only if the entire enabled chain succeeded. Successful requests
and rectangle arithmetic retain the original behavior.

For the four single-service failures in the GUID path, the original returns
success in the harness. The corrected function returns the original injected
error. For parameter and layer checkout errors, the corrected function leaves
PF_PreRenderOutput unchanged and does not attempt to consume checkout metadata.

## Contract proof

Define stages 1-6 as effect-layer lookup, parent-comp lookup, background-color
lookup, GUID mixing, channel checkout and input checkout. Stages 1-4 are disabled
when the host does not supply GuidMixInPtr. All enabled stages form an ordered
dependency chain.

Initially err is zero. Each stage executes through ERR, which evaluates its
operation only when err is zero and retains that operation's return value.
Induction shows that after the first nonzero result no later stage executes,
and err remains that first result. Consequently a zero return implies all
enabled stages succeeded.

The two output unions are dominated by if (!err). Hence a failed invocation
does not publish rectangles or access in_result fields. If the invocation
succeeds, checkout_layer supplied its result and the same source rectangle
helper is applied as before. Initialization is additional protection; it alone
would not repair falsely accepting a failed dependency.

This is success-gated publication, not an atomic transaction across the host.
Successful earlier host calls are not rolled back. Suite acquisition exceptions,
host internals, concurrency and cache internals are outside the finite callback
model. The existing automatic Smart PreRender parameter lifetime is unchanged.

## Reproduction and integration API

From the repository root:

    rtk proxy python -B experiments/smartfx-contract-lab/lab.py
    rtk proxy python -B experiments/smartfx-contract-lab/test_lab.py

lab.py accepts --sdk-root and --compiler. It hash-checks the original source and
supporting contracts, generates a minimal patch, compiles original/fixed harnesses,
runs every callback scenario, and syntax-checks both whole source files against
the installed SDK headers. Unknown edits to managed source artifacts are refused.

For the combined overlay, import lab.py and call:

    repair(source: str) -> str
    harness_for_source(source: str, sdk: Path = SDK_DEFAULT) -> str

These functions do not write files. repair expects LF-normalized source and
changes only the PreRender function. Each old expression must occur exactly
once. A second application or unexpected source change is rejected. The harness
can be compiled for the combined source using build_command in the results.

## Validation

The C++ harness includes actual SDK types, the actual ERR and parameter-checkout
macros, and the complete extracted PreRender function. It uses the original
Smart_Utils rectangle-union implementation. Host callbacks and suite acquisition
are explicitly mocked.

1,792 scenarios cover all 64 combinations of six failing callbacks, GUID callback
present/absent, Alpha/RGB channel selection and seven rectangle configurations
(including empty input, empty request, disjoint input, negative origin and a
nonempty initial output).

| Measured violation | Original | Fixed |
|---|---:|---:|
| Wrong first-error return | 840 | 0 |
| Calls after first error | 840 | 0 |
| Incorrect publication under the contract | 1554 | 0 |
| Attempted invalid result consumption | 2688 | 0 |
| False successful return | 210 | 0 |
| Output modified on a failing invocation | 628 | 0 |
| Changed successful request semantics | 0 | 0 |

The invalid-result counter is an **instrumented attempted use**, not a claim that
the test intentionally executed an undefined read. The UnionLRect wrapper checks
result availability before dereferencing. For skipped checkout it refuses the
read; for a failing checkout the mock writes a defined sentinel before returning
failure. Lookup outputs are also initialized by the mock on failure. Thus the
original's bad control flow is observable without relying on arbitrary stack
contents. The synthetic error codes 101-106 are test labels, not observed host
errors.

Original and fixed complete SmartyPants.cpp pass clang 20.1.2 syntax checking
against actual SDK headers. Both retain 42 SDK include/packing warnings. Harness
builds suppress only those warning categories. Results contain source hashes,
harness hashes, exact commands and a final recheck that the original SDK is
unchanged. No AE host, installed plug-in, performance benchmark or release
promotion is involved.

## Open bounds hypothesis

A separate possible problem remains: the Alpha kernel maps zero alpha to
nonzero alpha, while successful PreRender forwards input result/max rectangles.
If the effect's logical domain contains zero-RGBA pixels excluded by input
bounds, forwarding those bounds can exclude newly generated opacity.

This package does not silently replace bounds with in_data width/height.
The correct domain must account for collapsed compositions, upstream expansion,
mask clipping, downsampling and the REVEALS_ZERO_ALPHA contract.
preserve_rgb_of_zero_alpha requests hidden color; it does not by itself prove
that every zero-RGBA position needed for alpha generation is included.
An empty-input callback scenario alone cannot prove the real host supplies that
same geometry under all of these settings. This remains an integration
hypothesis, not a completed spatial-boundary repair.

Primary contract: [SmartFX Guide](https://ae-plugins.docsforadobe.dev/smartfx/smartfx/),
particularly Rectangles, The Size Of A Layer, and Flag On The Play, checked
2026-09-22. The SDK's AE_Effect.h:2512-2514 separately requires the maximum
rectangle to be independent of the requested output size.
