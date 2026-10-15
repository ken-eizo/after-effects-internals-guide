---
status: research
last_verified: 2026-10-14
evidence: AEIG MFR ownership analysis and AE 25.6 GPU suite contract
---
# MFR × GPU Backend: Concurrent Render Admission and Ownership

## Research question
Can frame-parallel AE rendering be combined with a single bounded GPU execution plan, without incorrect cross-frame state, redundant VRAM allocations or host stalls?

## Evidence boundary
- **Distributed SDK / documented behavior:** `PF_OutFlag2_SUPPORTS_THREADED_RENDERING` opts into concurrent frame rendering; GPU suite exposes framework-specific context/queue and host-accounted device allocation.
- **AEIG established model:** serialized instance state, const render snapshots, shared Compute Cache-derived data, request-local scratch, GPU residency and cache validity are distinct ownership domains.
- **Hypothesis:** GPU submission arbitration and bounded in-flight frame admission can improve some MFR cases. It cannot be assumed to override AE's private MFR scheduler or to improve all workloads.

## Required trace
For every frame/request: stable request ID, requested frame time, thread ID, device index, framework, pre-render start/end, GPU render start/end, queue submit/complete timestamp, checkout count, cache receipt, allocation/free bytes, cancellation and error codes. Do not persist raw process pointers as identities.

## Controlled experiment matrix
- Worker count: 1, 2, 4, 8 (where host supports); repeated shuffled frame orders.
- Render workload: memory-bandwidth bound, compute-bound, transfer-bound, temporal input with checkout fanout.
- Cache: cold/warm, changed parameters, forced invalidation, low-memory/device recreation.
- Cancellation during pre-render, queued submission and device completion.
- Compare distinct designs: per-frame transient resources, bounded shared pool, immutable pipeline cache, Compute Cache-backed derived results.

## Acceptance criteria
1. Same-frame deterministic semantic output across frame order, worker count, rerender and project reload, subject to explicit numeric tolerances.
2. Peak VRAM and RAM bounded by an explicit budget; no allocation lifetime crosses device setdown.
3. No host suite calls under a plugin-owned blocking lock unless documented safe; no GPU queue usage after teardown.
4. No deadlocks, use-after-free or stale outputs under cancellation; pre-render data destruction does not assume Smart Render occurs.
5. Report median/p95/p99 wall time, GPU active time, queue wait, peak memory, cache hits, dropped GPU feasibility requests and CPU fallback.
6. Verify that any proposed improvement wins against host-native D3D12/CUDA, not just against single-thread CPU.

## Next steps
Instrument an unmodified SDK effect baseline first; only then add a bounded device-scoped GPU scheduler with explicit per-request ownership. Distinguish host scheduling gaps from plugin overhead using ETW/WPR and GPU telemetry. Do not claim MFR has been modified at the host level.
## Cross references
- [MFR Overview](overview.md)
- [State Ownership](state-ownership.md)
- [Vulkan Host Backend Feasibility](../gpu-system/vulkan-host-backend-feasibility.md)

## Verified synthetic GPU MFR stresses and limits (F-GPU-018 / F-GPU-019)

External lab source: D:/Developer/AEEffectPerformanceLab/ae-host/tests/mock_gpu_parallel_host.cpp. The **compiled native AE 25.6 AEX** is invoked concurrently through mock SDK PICA/GPU suites and real Windows D3D12 buffers and a **single shared** D3D12 queue/device. Input/output GPU Worlds are distinct for each frame; this is not the Adobe MFR scheduler.

**Earlier failure discovered:** an implementation that returned failure when all 4 cached and 16 overflow GPU command contexts were occupied rejected healthy 24-way renders. A busy-spin readiness barrier also caused synthetic starvation. The fixed admission path sleeps cooperatively on a condition variable with bounded retry/deadline, instead of failing immediately. 24-way and 32-way requests now preserve output parity, with no invalid pixels reported. These results matter for scheduler robustness; they are not a proof of an Adobe host throughput advantage.

**Device ownership:** the effect GPUData wrapper maintains an atomic count of admitted active callbacks; setdown atomically closes admission and waits for the callbacks to drain before deleting the GPU backend. The mock host explicitly pauses 12 and 32 callbacks during PF_ABORT, calls Device Setdown concurrently, verifies that setdown waits, then resumes all callbacks. Unknown post-submit GPU completion quarantines command contexts and referenced GPU Worlds; the memory-safety fallback can retain memory until process exit.

**Repeat evidence:** 42 randomized mock A/B processes (six concurrency configurations × cached/uncached × 3 + six setdown stress runs) all passed. Compact CSV: datasets/ae-gpu-mock-mfr-admission-20261014.csv at repository root; raw JSON and binary hashes under the external lab results/native-aex-gpu-mfr-admission-20261014.json. Latest checked Windows regression includes full 32-way saturation + setdown tests, 15/15 passing. All numeric batch times are **CPU whole-batch wall** and show that command pooling is not consistently superior at high concurrency.

**MFR host qualification still missing:** Adobe AE actual PreRender scheduling, cache, random temporal order, host world lifetime and frame validity, device reset, VRAM peak, p95/p99 and across-effect D3D12 state tracking. The 15s lab wait is not an AE-documented deadline; it is a safe but experimental bound. Be prepared to choose a host-compatible cancellation or CPU fallback. Never allow unverified host World pointers to outlive the legal checkout window.

Related findings F-GPU-018 and F-GPU-019 and [cross-platform GPU architecture](../gpu-system/cross-platform-effect-architecture.md).

## Actual SDK 25.6 API correction superseding older synthetic host evidence (F-GPU-024)

The original GPU AEX/SDK-shaped mock passed with a raw C++ GPUData pointer from GPU_DEVICE_SETUP. The official SDK_Invert_ProcAmp sample instead uses PF_HandleSuite1.host_new_handle. **Critically, AE_Effect.h explicitly declares gpu_data as an effect-owned void*: raw pointers are NOT thereby forbidden.** We standardized the current adapter on the sample-style PF_Handle to exercise that ownership/cleanup model, not because a PF_Handle is mandated by the API. Historical synthetic tests, whether raw-pointer or handle-style, cannot alone prove actual Adobe host behavior. The current AEX stores ManagedGpuDevice* in a host-allocated PF_Handle and calls host_dispose_handle in setdown. Both GPU mock hosts now enforce a real double-indirection handle lifecycle, balanced allocations/disposals, and fail-closed when the PF_HandleSuite is absent.

A second untested original ABI defect was the hand-transcribed Windows PiPL spec version 13.28, while the actual SDK25.6's Adobe PiPLTool generates 13.29. The Windows AEX and macOS source now consume the same canonical ae-host/AEPerfHostCanonicalPiPL.r. The compiled AEX's actual PiPL bytes are checked against SDK PF_PLUG_IN_VERSION and PF_PLUG_IN_SUBVERS. All 18 current Windows CTests passed (including Handle Suite missing/error-path injection). Forty-two independent hardware-backed synthetic host stress processes were **rerun on the new fixed AEX**, all with handle alloc=dispose=1 and pixel parity PASS; independent new raw JSON and AEIG CSV retained. See research/findings/F-GPU-024-adobe-sdk-gpu-handle-and-canonical-pipl-abi.md. These important fixes **do not** prove that real Adobe AE2026 loads the effect; Mac Objective-C++/Metal and real-host Worlds remain untested.

## Frame-render-time outcome standard update (F-GPU-025)

The current strict optimization target is the actual After Effects Composition Profiler Timeline footer TOTAL "Frame Render Time" for a completely uncached frame. No current synthetic AE/GPU mock data constitute that measurement; all present actual host performance/1ms claims must fail closed. On real RTX 2070 SUPER hardware the 21-test Windows AEX passes, 42/42 MFR-like mock stress cases pass, and 45 randomized shader tiling A/B subprocesses pass but several 4K mocked callback p95 measurements EXCEED 1ms. Native 16x16 dispatch remains default pending genuine AE full-frame benchmarks. Actual Adobe environment, Mac Metal and nontrivial workloads are not performance-certified. See [Sub-1ms AE Total Frame Performance](../gpu-system/one-millisecond-total-frame.md) in the GPU system docs; the formal finding is F-GPU-025. Do not treat an isolated GPU microbenchmark as Adobe's frame cache/render time.
