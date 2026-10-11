# SDK render-state ownership lab

This package investigates **F-THREAD-004 / BQ-0036** in the pinned AE 25.6 SmartyPants sample. It does not modify the original SDK, install a plug-in, or run After Effects.

The sample advertises threaded rendering. AE_Effect.h:926-927 specifies that render-time sequence data is read-only, accessed through a suite, and the direct in_data->sequence_data field is NULL. The original ActuallyRender treats that valid NULL input as structural damage and copies the input instead of rendering the requested operation.

The repair builds SmartyPantsData in the current render invocation and initializes channel and blend from its checked-out parameters. The kernels only consume those two fields. It preserves the existing state layout and sequence callbacks while removing render-time access to the sequence handle. This deliberately retains the existing roughly 9 KiB structure on the stack; it does not claim a measured memory or speed improvement.

## Reproduce

From the repository root:

    rtk proxy python -B experiments/sdk-lifecycle-lab/repair.py
    rtk proxy python -B experiments/sdk-lifecycle-lab/test_repair.py

The runner validates pinned original hashes, rejects unexpected edits in copied sources, writes a minimal patch and corrected copies within this package, compiles the generated regression harness, and syntax-checks both complete translation units against the actual SDK headers. It checks the original SDK hashes again afterward.

Use --sdk-root to select an identical SDK corpus and --compiler to select clang++. A changed source hash requires review; it is not silently accepted.

## Two distinct experiments

1. **Normative NULL sequence input.** The full original ActuallyRender function is extracted into a mock SDK backend. With valid one-pixel input, Alpha mode and zero Blend, the original returns a structural-damage error and copies alpha 64. The corrected function succeeds and produces the independently expected alpha 191.

2. **Conditional shared-handle model.** A mock iterator pauses invocation A and calls invocation B synchronously with the same non-NULL sequence handle. No threads execute and no C++ data race is invoked. The original A consumes B's blend/channel after B returns; the correction keeps separate parameter storage and preserves the shared bytes. This is a deterministic aliasing stress model, not a claim that current AE supplies a shared non-NULL handle or makes these nested calls. Current MFR's documented NULL input is already the primary counterexample.

The harness inserts the whole ActuallyRender function from each exact source. Its 8-bit Alpha expression, state structures, channel enumeration and channel maximum are also extracted. Suite acquisition, iteration, copy, pixel worlds and error values are test adapters, not an SDK ABI implementation. The full-source syntax checks are separate evidence that the corrected SDK translation unit compiles; they do not link or execute a plug-in.

## Ownership argument

Each corrected invocation owns its render_data object. Its idp refers to that object only during the synchronous iterator call, just as the original code already used invocation-local idp during iteration. Different active invocations have distinct objects. Their parameter writes cannot alias, and the kernels do not modify those fields. No mutex or shared cache is needed for values determined entirely by current parameters.

This argument covers render parameter storage. It does not certify every sample callback, suite lifetime, pixel layout, ROI, arbitrary host behavior or the whole plug-in's MFR compatibility.

## Composition API

repair.py exposes:

- repair_smarty(source: bytes, *, reverse=False) -> bytes: exact function-scoped transformation, preserving independent edits elsewhere.
- extracted_harness(source: bytes, header: bytes, effect: bytes) -> bytes: generate the ownership harness from supplied SmartyPants.cpp, SmartyPants.h and AE_Effect.h.
- extract_function(source: str, name: str) -> str: source extractor used by the tests.

Composition callers must validate their own base hashes and record other transformations. The pure transformation intentionally accepts an independently patched file when its three ownership preimages are still exact.

Generated source copies and binaries are local workbench artifacts. Reviewable patches and reports are in patches/ and results/.
