---
status: experimentally verified on isolated Windows GPU; real Adobe host and macOS not verified
last_verified: 2026-10-14
evidence: F-GPU-015, F-GPU-016, F-GPU-017 and local AE SDK 25.6
---
# Native Effect Backend Selection: D3D12, Vulkan Interop, Metal and MFR

## Architecture in one sentence

Keep one semantic C++17 graph/effect core and one mostly shared Adobe EffectMain callback adapter. Select an **Adobe-supported GPU framework** on each OS, and treat Vulkan as an internal, conditional compute implementation only if the real host's device/world/queue ownership and memory-budget rules permit it. On the tested Windows machine, D3D12 is the production-oriented baseline. macOS needs a separate Metal adapter, not a generic assumption of Vulkan equivalence.

## Three independent claims that must never be conflated

| Gate | Evidence | Current verdict |
| --- | --- | --- |
| Physical Windows interop of independently created shared GPU memory | Local D3D12 + Vulkan 1MiB resource, 262144 deterministic uint32 samples each direction | **PASS on RTX 2070 SUPER** |
| Cross-API GPU-only execution ordering of that shared memory | D3D12 GPU Signal(3), Vulkan GPU wait(3), Vulkan write/signal(4), D3D12 GPU wait(4), single final CPU test readback | **PASS on RTX 2070 SUPER** |
| Actual After Effects GPU World export, documented state/queue/memory ownership | 25.6 SDK surface + diagnostic built but executed against only SDK-shaped mock Worlds | **UNKNOWN, not AE host verified** |

The first two gates do not imply the third. Adobe's public GPU enum includes NONE, OPENCL, METAL, CUDA and DIRECTX; it does NOT define a Vulkan host framework value in the inspected 25.6 headers. Merely appending a Vulkan enum or header cannot make AE allocate native Vulkan GPU Worlds or schedule Vulkan commands.

## Verified stand-alone chain (Windows)

1. Create DEFAULT-heap D3D12 buffer with D3D12_HEAP_FLAG_SHARED. Nonshared buffers fail CreateSharedHandle (HRESULT 0x80070057 in the test); shared buffers export an NT handle.
2. Match actual D3D12 adapter LUID to Vulkan VkPhysicalDeviceIDProperties.deviceLUID. Do not match by device marketing name alone.
3. Use VK_KHR_external_memory_win32 + VK_EXTERNAL_MEMORY_HANDLE_TYPE_D3D12_RESOURCE_BIT to import into VkDeviceMemory. Intersect external handle memoryTypeBits with Vulkan buffer memory requirements and bind the imported memory to VkBuffer.
4. Create D3D12_FENCE_FLAG_SHARED, export its Win32 handle, and import that handle into Vulkan as a timeline semaphore (VK_EXTERNAL_SEMAPHORE_HANDLE_TYPE_D3D12_FENCE_BIT).
5. Execute GPU copies and writes with explicit D3D12 transitions and Vulkan external queue-family release/acquire barriers. Use GPU wait/signal on both API queues; avoid intermediate CPU waits and copies at the interop boundary.
6. Verify final output after a terminal fence wait. Run under a controlled driver and GPU fault injection, without releasing borrowed worlds while any GPU work might still reference them.

**Observed:** 1MiB transferred conceptually between APIs by shared allocation, *not* host-side pixel memcpy; 262144 32-bit samples matched in both directions. Eight independently launched test executions passed eleven output gates each. Source, binary SHA256, and verbatim receipts: D:/Developer/AEEffectPerformanceLab/results/win-d3d12-vulkan-bidirectional-gpu-sync-20261014.json.

**Clarification:** a GPU-local D3D12 upload and Vulkan/D3D12 diagnostic readbacks still occurred to seed and inspect the pattern; “zero-copy” refers to the *API boundary sharing the same physical memory*, not an end-to-end effect with literally zero copies.

## Actual host diagnostic: negative and positive controls

An opt-in read-only D3D12 COM inspector is linked into D:/Developer/AEEffectPerformanceLab/ae-host/AEPerfHostProbe.cpp as gpu_world_diagnostic.cpp. It consumes actual EffectMain GPU Smart Render's suite-retrieved resources, but currently the driver tests supply SDK-shaped **mock host** buffers.

| World allocation | Readings | Export success | Render parity |
| --- | ---: | ---: | --- |
| Ordinary mock D3D12 committed buffer | 96 | 0 | PASS |
| Mock buffer explicitly created with shared flag | 96 | 96 | PASS |

CTest isolated_ae_gpu_world_exportability_positive_negative confirms both modes. The inspector only activates when AEPERF_GPU_WORLD_DIAGNOSTIC_LOG specifies an absolute local log path. It logs metadata, HRESULT and exportability, and always closes the temporarily created handle. No diagnostics or plugin installation were performed against Adobe After Effects itself. **The real AE verdict is still UNKNOWN.**

## Host-safe Vulkan admission policy (implementation, not aspirational prose)

The host-neutral decision model in D:/Developer/AEEffectPerformanceLab/core/effect_core.cpp only admits VulkanInterop when every one of these seven independent runtime gates is positively established:

1. Real Adobe AE host verified using a disposable project and isolated instance.
2. AE-owned source/output GPU World resources proven exportable *on that device/request*.
3. The same physical D3D12/Vulkan adapter verified by LUID.
4. Vulkan external memory import parameters, buffer layouts and memory-type requirements compatible.
5. External GPU timeline sync proven for the exact device/queues.
6. Current GPU resource states, inter-queue memory barriers and host queue ownership proved legal.
7. Host GPU memory allocation/accounting and teardown rules met.

Unknown is treated as false. Unit tests reject every single missing gate and reject VulkanInterop on macOS. The successful all-true decision-model fixture is a **hypothetical unit test**, not a claim that current AE fulfills these conditions.

Do not privately allocate full-frame device intermediates in Vulkan merely to circumvent the GPU Device Suite's explicit “All device memory must be allocated through this suite” contract. A hypothetical D3D12 GPU copy to a shared buffer may be technically possible but adds another device allocation, transfer bandwidth and synchronization; it cannot be called zero-copy relative to AE-owned GPU Worlds and must be qualified as a separate pipeline.

## Windows native baseline vs Mac native baseline

| Situation | Preferred first implementation to measure | Why |
| --- | --- | --- |
| Windows, GPU input/output already in AE-owned D3D12 memory, ordinary pixel/neighborhood processing | **AE-native D3D12 GPU Smart Render** | Host supplies device, queue and GPU Worlds. No Vulkan import/setup/synchronization tax. |
| Windows, GPU already resident and specialized NVIDIA compute libraries outperform identical D3D12 workload | **AE-native CUDA** after full parity/host-cost test | Algorithm-specific library and hardware benefit may outweigh additional constraints. |
| macOS (Intel or Apple Silicon) | **AE-native Metal GPU Smart Render** and shared C++17 core | Supported macOS host path; Mac hardware/Xcode validation still pending. |
| Tiny ROI or GPU unavailable | **CPU SmartFX scalar/SIMD**, with cached CPU capability detection | No GPU dispatch setup and mandatory correct low-end fallback. |
| Windows, AE-shared source/destination and all seven gates **demonstrated** | **Conditional internal Vulkan execution** | Only then do measured Vulkan kernel gains justify API boundary cost. |
| Windows with unknown/nonshared AE memory and unproven interop state | **Never automatically use direct Vulkan import** | Invalid shared-handle assumptions or race risks outweigh isolated speed claims. |

“Preferred first” is not the same as a universal fastest backend. Results must be measured per algorithm, frame size, residency, MFR concurrency, device/driver, peak VRAM and wall-time tail distribution.

## Failure and MFR discipline

- A render request owns its writable scratch, command allocator, command list, fence/event, and any retained shared-handle lifetime. Immutable compiled pipeline objects may be device-scoped.
- Completion, cancellation, timeout and device teardown are distinct states. A post-submission timeout must not destroy a resource still in use by GPU. An implementation that quarantines unknown-completion resources may avoid use-after-free but can still cause bounded **per-device memory leakage**; this is a recovery gap, not perfect stability.
- Four cached D3D12 command-context slots and an admission-limited transient overflow path are implemented in the Windows laboratory. Simulated unknown completion after GPU submission correctly closes GPU admission in pooled and nonpooled cases. This does not establish recovery from real device loss or in-host MFR teardown races.
- Never promise GPU queue submission from a CPU callback may outlive the callback until Adobe host world lifetime guarantees have been explicitly verified. A native D3D12 reference that waits for completion is safer as a starting point.
- Pixel-format constraints, full vs cropped ROI geometry, host World row stride, alpha, HDR and numeric tolerances must be held constant in every performance comparison.

## Evidence requirements before a production promotion

Run an actual AE 2026 GPU selector, World and logging probe in a separate disposable session. Then test cancellation, render order and MFR (1/2/4/8 requests), low-memory pressure, host cache invalidation, device reset, per-device state queues and real output comparisons. Record Adobe build, SDK version/hash, GPU/driver, project fixture, GPU and CPU p50/p95/p99, peak device/host memory, and command completion/order.

If the AE host World is nonshareable, direct Vulkan zero-copy is not presently an SDK-aligned option for that World; continue optimizing the AE-native D3D12/Metal/CUDA backends. No simulated or isolated GPU success can promote an unverified Adobe host contract.

## Source links

- Local AEIG primary evidence: F-GPU-013, F-GPU-014, F-GPU-015, F-GPU-016 and F-GPU-017 under research/findings/.
- [GPU Effect Engineering](optimal-effect-engineering.md)
- [Cross-platform effect architecture](cross-platform-effect-architecture.md)
- [Vulkan host framework boundary](vulkan-host-backend-feasibility.md)
- [MFR ownership](../mfr/gpu-concurrency-experiment.md)
- https://docs.vulkan.org/guide/latest/extensions/external.html
- https://learn.microsoft.com/en-us/windows/win32/api/d3d12/nf-d3d12-id3d12device-createsharedhandle
- https://docs.vulkan.org/spec/latest/chapters/synchronization.html

## Actual SDK 25.6 API correction superseding older synthetic host evidence (F-GPU-024)

The original GPU AEX/SDK-shaped mock passed with a raw C++ GPUData pointer from GPU_DEVICE_SETUP. The official SDK_Invert_ProcAmp sample instead uses PF_HandleSuite1.host_new_handle. **Critically, AE_Effect.h explicitly declares gpu_data as an effect-owned void*: raw pointers are NOT thereby forbidden.** We standardized the current adapter on the sample-style PF_Handle to exercise that ownership/cleanup model, not because a PF_Handle is mandated by the API. Historical synthetic tests, whether raw-pointer or handle-style, cannot alone prove actual Adobe host behavior. The current AEX stores ManagedGpuDevice* in a host-allocated PF_Handle and calls host_dispose_handle in setdown. Both GPU mock hosts now enforce a real double-indirection handle lifecycle, balanced allocations/disposals, and fail-closed when the PF_HandleSuite is absent.

A second untested original ABI defect was the hand-transcribed Windows PiPL spec version 13.28, while the actual SDK25.6's Adobe PiPLTool generates 13.29. The Windows AEX and macOS source now consume the same canonical ae-host/AEPerfHostCanonicalPiPL.r. The compiled AEX's actual PiPL bytes are checked against SDK PF_PLUG_IN_VERSION and PF_PLUG_IN_SUBVERS. All 18 current Windows CTests passed (including Handle Suite missing/error-path injection). Forty-two independent hardware-backed synthetic host stress processes were **rerun on the new fixed AEX**, all with handle alloc=dispose=1 and pixel parity PASS; independent new raw JSON and AEIG CSV retained. See research/findings/F-GPU-024-adobe-sdk-gpu-handle-and-canonical-pipl-abi.md. These important fixes **do not** prove that real Adobe AE2026 loads the effect; Mac Objective-C++/Metal and real-host Worlds remain untested.

## Frame-render-time outcome standard update (F-GPU-025)

The current strict optimization target is the actual After Effects Composition Profiler Timeline footer TOTAL "Frame Render Time" for a completely uncached frame. No current synthetic AE/GPU mock data constitute that measurement; all present actual host performance/1ms claims must fail closed. On real RTX 2070 SUPER hardware the 21-test Windows AEX passes, 42/42 MFR-like mock stress cases pass, and 45 randomized shader tiling A/B subprocesses pass but several 4K mocked callback p95 measurements EXCEED 1ms. Native 16x16 dispatch remains default pending genuine AE full-frame benchmarks. Actual Adobe environment, Mac Metal and nontrivial workloads are not performance-certified. See [Sub-1ms AE Total Frame Performance](one-millisecond-total-frame.md) in the GPU system docs; the formal finding is F-GPU-025. Do not treat an isolated GPU microbenchmark as Adobe's frame cache/render time.
