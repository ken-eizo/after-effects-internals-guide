---
status: research
last_verified: 2026-10-14
evidence: AE 25.6 headers and SDK_Invert_ProcAmp, AEIG architecture, local static experiments
---
# Optimal AE Effect Engineering: Evidence-Based Decision System

## Definition and objective
The aim is the Pareto frontier of correct visual/numeric output, low end-to-end latency, high throughput, bounded peak VRAM and RAM, minimum required hardware, stability across MFR/cancellation/device loss, and maintainability. No single GPU API is inherently fastest for all kernels and all host states. An implementation that violates host contracts is rejected even if isolated kernel timings are low.

## Hard host contracts [distributed SDK, inspected locally]
- AE 25.6 recognizes NONE, OPENCL, METAL, CUDA and DIRECTX GPU framework enum values, but not VULKAN in the inspected AE_Effect.h.
- PF_GPUDeviceInfo hands DirectX plugins an ID3D12Device pointer and ID3D12CommandQueue pointer; official SDK_Invert_ProcAmp initializes DXContext with both and dispatches two compute passes to borrowed GPU worlds.
- PF_GPUDeviceSuite1 explicitly requires device allocations through the host suite. A private D3D12 heap or Vulkan allocation is not automatically a host-accounted intermediate.
- GPU World accesses go through the suite: layer CPU data pointers are not pixels in GPU Smart Render.
- GPU Device Setup describes device-level support; Smart PreRender advertises request-specific PF_RenderOutputFlag_GPU_RENDER_POSSIBLE.
- MFR-safe plugins need PF_OutFlag2_SUPPORTS_THREADED_RENDERING and correct const render-state/sequence-data ownership.
- SDK does NOT document initial GPU suite D3D12 intermediate resource state, AE-world exportable shared handle, fence interop, or how GPU queue submission is ordered across foreign APIs. Do not guess.

## Backend selection ladder (priority for establishing baselines, NOT speed ranking)
1. **DirectX12 native GPU SmartFX (Windows)**. Prefer as first evidence-grade baseline because AE provides the D3D12 device, command queue and GPU worlds. Reuse immutable pipelines. Use suite allocations. Avoid redundant transfers.
2. **Metal native GPU SmartFX (macOS)**. Native-platform baseline; Apple devices require separate measurement.
3. **CUDA under AE GPU SmartFX (NVIDIA)**. Compare on kernels benefiting from CUDA or optimized libraries; preserve AE's context/stream/allocator contract.
4. **CPU SmartFX with SIMD**. May win on tiny ROIs or light operations when GPU dispatch overhead exceeds work; mandatory correct fallback and low-end hardware baseline.
5. **D3D12 to Vulkan/CUDA external-memory interop**. Experimental; only promote if AE host-owned resources are proven exportable, the same adapter is used, synchronization is legal and an end-to-end improvement is demonstrated.
6. **CPU SmartFX to privately managed Vulkan**. Not zero-copy at AE GPU boundary; only retain where measured benefit outweighs copies.
7. **Undocumented host binary modification**. Not suitable as default shipping path without independent compatibility, licensing, safety and maintenance evaluation; adding an enum in a header cannot register a host GPU backend.

## Optimization hierarchy
1. Correct output first: float HDR, color space, zero-alpha RGB, alpha premultiplication, ROI/downsample, borders and temporal dependencies.
2. Eliminate redundant computation through correct dependency identity and cache hit; avoid invalidation errors.
3. Reduce asymptotic work: separable convolution, FFT/overlap-save for large kernels, reductions, specialized algorithms.
4. Reduce memory traffic: fuse operations where semantics permit, tile/localize neighborhoods, minimize simultaneously live intermediates, avoid CPU/GPU crossings.
5. Make resource lifetime bounded: reuse only after completion; cap in-flight frames by device budget and host MFR constraints.
6. Tune execution: CPU vectorization, shader workgroups/wave behavior, D3D12 descriptor/command list re-use, queue batching, compiled shader cache.
7. Tune measured end-to-end p95/p99 and constrained machines, not just ideal single-pass GPU timestamps.

## Cost accounting
- Measure CPU pre-render planning, upstream checkout, command construction/submission, queue wait, GPU execution, any copy/synchronization, result handoff and host scheduling gap.
- Stages can overlap; do not just sum unrelated clock domains. Measure critical path and GPU timestamp durations separately.
- Record both allocated and resident physical device bytes where telemetry permits. Imported external-memory objects can reference **the same** physical allocation; do not double-count them.
- Account for 1/2/4/8 concurrent requests where permitted and worst-case output-size multiplication by MFR. Record cold compilation separately from steady-state execution.

## Ownership invariants
| Asset | Recommended lifetime | Prohibitions |
| --- | --- | --- |
| User parameters | AE managed/project serialized | unsynchronized process-global mutation |
| Render sequence state | const semantic snapshot | mutable shared accumulator across MFR |
| PreRender data | one request, independently destructible | assuming SmartRender always follows |
| Derived shared computation | Compute Cache with semantic keys | implicit cross-frame mutable cache |
| GPU compiled shader | device + framework + shader signature | caching raw host pointer as stable cross-version identity |
| GPU temporary | request and host device, completion fenced | recycle before queue completion |
| D3D12 command allocator/list | safe mutable in-flight scope | unguarded concurrent reset/use |
| GPU teardown | device-setdown safe lifetime | use after device loss/setdown |

MFR cancellation stops future admission; previously queued GPU work retains every resource it references until safe completion. Minimize plugin-owned locks; never hold a blocking lock across arbitrary host callbacks without a proven contract.

## Workload decision matrix
| Workload | First algorithm candidates | Likely limit | Important experiment |
| --- | --- | --- | --- |
| pixel arithmetic | fused SIMD CPU vs D3D12 vs CUDA | launch/traffic | tiny ROI crossover |
| Gaussian blur | separable, tiled, fused where possible | memory bandwidth | pass count and scratch |
| large convolution | direct, separable if valid, FFT/overlap-save | compute and workspace | kernel-size crossover |
| PixelSort | segmented bitonic/radix or hierarchical | divergent access/barriers | image-size regimes |
| Temporal effects | frame dependency / cache / bounded admission | cache and scheduling | random order MFR |
| many effect layers | kernel fusion where semantically valid | intermediate traffic | whole-chain AE latency |

## Acceptance gates for a proposed best implementation
A. Official host ownership/queue/resource-state contract confirmed or explicitly marked host-unsupported experimental.
B. Numeric, visual, alpha/color, ROI and temporal parity passes.
C. Repeated cancellation, memory pressure, device reinitialization, MFR concurrency and teardown do not hang, leak or corrupt state.
D. Measured median/p95/p99 wall time, sustained frame throughput and peak RAM/VRAM improve or remain acceptably bounded across target hardware.
E. Results reproduce with recorded driver, AE build, SDK hash, project fixture, cache conditions and shader configuration. Any backend promotion must refer to experiment receipts, not assumptions.

## Measurement protocol
Same rendered pixels, sample count, precision and project across candidates. Record AE build, GPU adapter/LUID, OS, driver, ROI, downsample, frame order, MFR mode, warm/cold cache, shader compile status, GPU/CPU timestamps, transfer bytes and high-water device memory. Randomize run order and report multiple runs, errors and distributions. Do not compare isolated Vulkan compute with whole-pipeline AE DirectX frames.

## Local evidence and remaining gaps (2026-10-14)
- Static source evidence: external research workbench `D:\\Developer\\AEEffectPerformanceLab\\gpu-optimal-archive-20261014\\contract_atlas.py` and recorded JSON SHA256/SDK source lines. The raw working experiment was moved outside AEIG by design.
- Standalone D3D12 shared-resource probe: external workbench `gpu-optimal-archive-20261014/d3d12_share_probe.cpp`; a shareable standalone allocation does **not** prove AE World exportability or Vulkan import.
- Crossed 12-profile RTX 2070 SUPER GPU-resident/readback experiment and C++ host-neutral core are in external `D:\\Developer\\AEEffectPerformanceLab`. Reproduced standalone evidence: F-GPU-007; **not** an AE-render benchmark.
- Hardware: RTX 2070 SUPER, Windows 10 19045, Visual Studio 2022, CUDA 13, Vulkan runtime operational.
- External lab native AE SDK CPU SmartFX `.aex` build and PiPL/entry smoke passed (F-GPU-008; **not installed in AE or host-verified**). Standalone D3D12 crossed GPU-residency/readback 12-profile experiment passed (F-GPU-007); summary CSV under `datasets/ae-gpu-standalone-20261014-fusion-summary.csv`.
- VULKAN_SDK points to C:\VulkanSDK\1.4.321.1 which is absent; SDK compilation currently not verified.
- **Not yet established:** full host plugin benchmark, actual Vulkan import of host resources, host/MFR GPU timing, best backend on any target workload. No claim of world-leading performance is currently justified.

## Related
- [GPU host contract](overview.md)
- [Vulkan host boundary](vulkan-host-backend-feasibility.md)
- [Windows/macOS shared-source native architecture](cross-platform-effect-architecture.md)
- [MFR GPU concurrency](../mfr/gpu-concurrency-experiment.md)
- [MFR state ownership](../mfr/state-ownership.md)
- [Render-graph memory planning](../render-graph/verified-memory-planning.md)
- https://docs.vulkan.org/guide/latest/extensions/external.html
- https://learn.microsoft.com/en-us/windows/win32/direct3d12/shared-heaps

## Official Adobe D3D12 sample: avoid treating reference code as a tuned implementation [local distributed SDK]

Inspected E:/ae25.6_61.64bit.AfterEffectsSDK/Examples/Util/DirectXUtils.cpp:
- lines 38-54: DXContext::Initialize borrows device and command queue, initializes command allocator/list and creates a fence; its comments warn about objects outliving the application.
- lines 60-65: source explicitly says "Sub-optimal: Prefer using a ring buffer style implementation" while creating a fixed 1000-entry shader-visible descriptor heap.
- lines 134-146: submits ExecuteCommandLists and signals a fence, then executes WaitForSingleObject(INFINITE) if the GPU has not completed. This is a synchronous, safe-reference implementation; it is not evidence that arbitrary asynchronous GPU completion is allowed by AE's public SmartRender callback.
- lines 271-296: uses RWByteAddressBuffer-compatible raw typeless UAV buffer views and explicit UAV ResourceBarrier. Do not blindly translate it into an optimal barrier strategy without state/hazard profiling.
- SDK_Invert_ProcAmp.cpp lines 994-1025: official DirectX Smart Render chains two DXShaderExecution passes (Invert, ProcAmp), which is an experimental target for fusion *if the pixel/parameter semantics match*. Comparing fused single-pass with the two-pass reference controls memory traffic and CPU wait overhead.

Experiment plan:
1. Build an exact-output two-pass D3D12 reference using the sample, capture callback/queue/GPU durations.
2. Implement one-pass fused shader with equivalent semantics, same input/output GPU worlds, no intermediate world allocation; compare output and high-water memory.
3. Keep the safe blocking implementation as the initial release profile; experiment separately with bounded frame-in-flight and fence-dependent reuse only after proving AE host callback completion and cross-effect queue ordering.
4. Introduce a ring descriptor allocator only when descriptor reuse hazard tracking and thread safety are verified. Never reset a command allocator still referenced by an executing command list.
5. Reject any "faster" design that returns GPU Smart Render before its output is valid unless Adobe's host dispatch contract explicitly permits it.

This yields a narrower near-term optimization hypothesis: **kernel fusion and removal of unnecessary intermediate GPU Worlds** may improve end-to-end performance with significantly less host-lifecycle risk than Vulkan interop or premature callback asynchrony.
## Latest SDK-shaped effect GPU integration and context ownership (F-GPU-009, F-GPU-010)

Experiment-only source now lives outside AEIG at `D:\Developer\AEEffectPerformanceLab`. A native Windows `AEPerfHostProbe.aex` compiled successfully from the AE SDK 25.6 with both CPU SmartFX and DirectX12 GPU Smart Render commands. It borrows the host-presented D3D12 device/queue and GPU World buffers, embeds precompiled DXIL, and uses one fused BGRA128 pass without a plugin-owned full-frame intermediate.

**Evidence limit:** Its selector handshake (GPU_DEVICE_SETUP -> SMART_PRE_RENDER -> SMART_RENDER_GPU -> GPU_DEVICE_SETDOWN), checks of PiPL out_flags2/version, pixel parity, cancellation and checkout/checkin error behavior were validated through a *mock AE host* that supplies its own real D3D12 GPU resource handles. The real Adobe After Effects runtime is **not** yet verified. The user had AE 2026 open; no attempt was made to inject an unproven effect into that live session.

A reproducible fixed-size command-object context cache improved callback wall median from 0.22090 ms to 0.08065 ms (2.74x) in a 19x13 BGRA128 mock GPU World A/B with six processes per treatment, each executing 48 frames. Caching of at most four command allocator/list/fence/event Context objects avoids repeated CPU allocations. Context lease uses atomic acquire/release; after GPU fence completion, a slot can be reset and released. The simulated class test also passed **12 concurrent GPU render requests** on a shared device (overflow requests used independent transient contexts). This is **not a test of AE MFR**. Individual pooled run p95 outliers reached 0.4957 ms and production worst-case failure retirement remains unresolved.

**Rules for future stable implementation:**
1. Use a **bounded GPU command-object pool** only when host device/queue identity and thread ownership are stable; preserve a correct uncached path for benchmarking and safety.
2. Separate high-level device ownership and immutable pipelines from mutable command allocator/fence state; never reset an allocator while queued GPU work may refer to it.
3. Compare p50/p95 and memory overhead on small and large requests. A warm cache may help tiny requests more than large bandwidth-limited convolution/FFT.
4. In failure or timeout, never recycle an uncertain resource; before production, implement safe deferred retirement for transient overflow submissions and device-setdown states.
5. Do not assume the SDK mock's input/output resource states represent AE's actual states; validate with an in-host, isolated test.
6. Respect GUI/live host safety. Adobe documents `AfterFX.exe -r` scripts targeting an *existing* AE session; do not use this to run risky test scripts in a user's active project.

Evidence: `research/findings/F-GPU-009-native-d3d12-aex-gpu-selector-mock-integration.md`, `research/findings/F-GPU-010-bounded-d3d12-command-context-lease-pool.md`, compact dataset `datasets/ae-gpu-mock-host-context-pool-20261014.csv`. Full JSON, mock host and .aex binaries remain outside AEIG in the external workbench.

## 2026-10-14 evidence promotion: shared GPU interop, CPU SIMD and real-host admission frontier

The latest verified lab facts supersede older notes above that refer to prospective D3D12/Vulkan standalone roundtrips, uncontained post-submit overflow and the smaller regression test count.

1. **Windows native CPU path:** The same AE SDK effect now supports 8/16/32bpc CPU Smart Render, x86_64 AVX2 selected after a cached CPUID/OSXSAVE/XGETBV check, and a scalar path when SIMD is disabled or unsupported. Twenty-four mixed-depth simultaneous mock requests passed. In separately measured 32bpc mock render callbacks after fixing per-frame feature probing, the four-run median of per-process p50 was 0.0004 vs 0.0002ms (19x13), 7.823 vs 6.394ms (1080p), and 26.638 vs 22.949ms (4K), scalar vs AVX2. Tiny-ROI absolute timings are close to clock resolution and should not be generalized. Evidence F-GPU-012/F-GPU-013, dataset ae-cpu-smartfx-simd-selector-20261014.csv.
2. **D3D12 failure lifetime:** Native D3D12 backend now retains in-flight GPU World COM references until known completion, uses four exclusive command contexts plus at most sixteen overflow contexts, and fails closed upon uncertain completion. A deliberate post-submit uncertainty injector passed pooled and nonpooled cases, but quarantining an in-flight resource may leak until process exit and real device-loss/MFR setdown remain unresolved. Evidence F-GPU-014.
3. **Standalone D3D12/Vulkan hardware interop:** A shared D3D12 committed 1MiB buffer was imported into Vulkan using VK_KHR_external_memory_win32 on the same LUID-matched RTX 2070 SUPER. GPU data read/write parity passed in both directions. An imported D3D12 shared fence/timeline semaphore safely ordered D3D12 write -> Vulkan read/write -> D3D12 read with GPU-only queue waits, and a final CPU verification readback. Eight full-process repeats passed eleven output gates each. This does **not** constitute Adobe AE GPU World support. Evidence F-GPU-015/F-GPU-016.
4. **Actual AE World sharing decision:** A read-only diagnostic module inside the compiled AEX classifies the documented D3D12 GPU World resource by heap flags and CreateSharedHandle HRESULT. On synthetic GPU Worlds, 96 ordinary nonshared cases and 96 shared-flag cases were all classified correctly with unchanged pixel parity. **None was allocated by real After Effects.** Real host World sharing flags/queue states/memory accounting remain UNKNOWN. Evidence F-GPU-017. Eleven full Windows CTests passed.
5. **Selection policy enforced in executable tests:** Host-neutral C++17 runtime planner rejects VulkanInterop unless each of seven conditions is explicitly confirmed: actual AE host, shareable AE GPU World, same physical adapter, compatible external memory, cross-API GPU timeline synchronization, legal resource states/host queue ownership, and suite-compliant GPU memory accounting. Every single missing condition was unit tested; a synthetic all-true case does not mean real AE passes.

The optimal near-term default remains **AE-native D3D12 Smart Render on Windows, AE-native Metal Smart Render on macOS, CPU SmartFX for tiny or unavailable-GPU cases**, with CUDA considered only when measured algorithm-specific advantages justify it. Vulkan's kernel may be valuable, but the copy/synchronization and AE ownership contracts must be solved **before** it can be considered a superior host runtime. macOS's native Metal .plugin baseline is source-staged but has not yet been compiled on Mac hardware. See [D3D12/Vulkan Verified Boundaries](cross-api-interop-verified-boundaries.md).

## 2026-10-14 concurrent-admission and true shared-source native GPU milestone

**New evidence F-GPU-018 / F-GPU-019:** The real Windows compiled AEX was called by a synthetic host from 1, 4, 12, 20, 24 and 32 simultaneous GPU requests, with distinct host-like GPU Worlds and one actual D3D12 device/queue. Early overflow admission failures were discovered at 24 workers and corrected with time-bounded, condition-variable GPU lease admission. Six teardown-race runs explicitly invoked GPU Device Setdown while 12 or 32 callback leases were active; callbacks were allowed to finish before the device was destructed. All 42 independent randomized hardware-backed mock runs passed zero-pixel-error checks. Current Windows regression increased to 15/15 tests.

**Counterexample to universal command caching:** Median whole-batch wall time in the 42-run mock study did not always improve with pooling: at 24 callbacks pooled 5.946ms vs uncached 5.497ms; at 32 pooled 6.329ms vs uncached 6.906ms. Tiny serial callback benchmarks in F-GPU-010/F-GPU-011 showed a different fixed-cost benefit. Therefore conditionally enable caching based on measured end-to-end workload/host metrics, not a universal assumption of superiority.

**New evidence F-GPU-020:** A native macOS Metal Smart Render adapter (Objective-C++ + offline MSL one-pass fused kernel), Mac PiPL and Xcode CMake .plugin target have been source-implemented against the same C++17 EffectMain as Windows D3D12. Windows MSVC compiled both D3D12 and Metal-define C++ selector variants using AE 25.6 headers. **The Mac Objective-C++, metallib, Rez, Universal arm64/x86_64 plugin and actual Metal AE host execution have NOT been compiled/tested on Mac**, so not production-grade. Mac uses Metal, not an implicit Vulkan backend.

**Backend decision at present:** Windows native D3D12 baseline; macOS native Metal source candidate, not hardware verified; CPU SIMD/scalar fallback; Vulkan only as an experimental internal Windows compute backend after the actual AE-owned GPU World sharing/state/queue/memory gates pass. Device setdown timeout and unknown GPU fence completion can still quarantine GPU resources until process exit. The source-staged 32-worker results cannot guarantee good p95/p99 or host scheduler interaction.

Full qualification remains: isolated real Adobe AE host GPU World test, actual MFR/host cache/project render correctness, original GPU device reset/lost-device stress, Apple Silicon + Intel Mac where supported, exact HDR/alpha/ROI semantic parity, peak RAM/VRAM and median/p95/p99 under comparable workload. See [MFR experiments](../mfr/gpu-concurrency-experiment.md), [cross-platform architecture](cross-platform-effect-architecture.md) and F-GPU-018–020.

## Actual SDK 25.6 API correction superseding older synthetic host evidence (F-GPU-024)

The original GPU AEX/SDK-shaped mock passed with a raw C++ GPUData pointer from GPU_DEVICE_SETUP. The official SDK_Invert_ProcAmp sample instead uses PF_HandleSuite1.host_new_handle. **Critically, AE_Effect.h explicitly declares gpu_data as an effect-owned void*: raw pointers are NOT thereby forbidden.** We standardized the current adapter on the sample-style PF_Handle to exercise that ownership/cleanup model, not because a PF_Handle is mandated by the API. Historical synthetic tests, whether raw-pointer or handle-style, cannot alone prove actual Adobe host behavior. The current AEX stores ManagedGpuDevice* in a host-allocated PF_Handle and calls host_dispose_handle in setdown. Both GPU mock hosts now enforce a real double-indirection handle lifecycle, balanced allocations/disposals, and fail-closed when the PF_HandleSuite is absent.

A second untested original ABI defect was the hand-transcribed Windows PiPL spec version 13.28, while the actual SDK25.6's Adobe PiPLTool generates 13.29. The Windows AEX and macOS source now consume the same canonical ae-host/AEPerfHostCanonicalPiPL.r. The compiled AEX's actual PiPL bytes are checked against SDK PF_PLUG_IN_VERSION and PF_PLUG_IN_SUBVERS. All 18 current Windows CTests passed (including Handle Suite missing/error-path injection). Forty-two independent hardware-backed synthetic host stress processes were **rerun on the new fixed AEX**, all with handle alloc=dispose=1 and pixel parity PASS; independent new raw JSON and AEIG CSV retained. See research/findings/F-GPU-024-adobe-sdk-gpu-handle-and-canonical-pipl-abi.md. These important fixes **do not** prove that real Adobe AE2026 loads the effect; Mac Objective-C++/Metal and real-host Worlds remain untested.

## Frame-render-time outcome standard update (F-GPU-025)

The current strict optimization target is the actual After Effects Composition Profiler Timeline footer TOTAL "Frame Render Time" for a completely uncached frame. No current synthetic AE/GPU mock data constitute that measurement; all present actual host performance/1ms claims must fail closed. On real RTX 2070 SUPER hardware the 21-test Windows AEX passes, 42/42 MFR-like mock stress cases pass, and 45 randomized shader tiling A/B subprocesses pass but several 4K mocked callback p95 measurements EXCEED 1ms. Native 16x16 dispatch remains default pending genuine AE full-frame benchmarks. Actual Adobe environment, Mac Metal and nontrivial workloads are not performance-certified. See [Sub-1ms AE Total Frame Performance](one-millisecond-total-frame.md) in the GPU system docs; the formal finding is F-GPU-025. Do not treat an isolated GPU microbenchmark as Adobe's frame cache/render time.
