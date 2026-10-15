---
status: verified-windows-lab-unverified-adobe-host-and-macos-runtime
last_verified: 2026-10-14
evidence: F-GPU-015 through F-GPU-025
---
# Native AE Effect Engineering — Qualification Matrix and Selection Standard

This chapter is the **gate between technical research and an actual production effect plugin**. Do not call an independently compiled AEX "After Effects compatible" merely because it exports EffectMain and passes an SDK-shaped synthetic host. Never silently promote an unsafe/unmeasured pipeline as a performance "optimum".

## What has been demonstrated

| Capability | Evidence grade | Status |
| --- | --- | --- |
| Windows C++17 AE SDK PiPL/EffectMain/CPU SmartFX 8/16/32bpc | Real compiled AEX + SDK-shaped test host | PASS; **real AE host not checked** |
| Native Windows DirectX12 32-bit float BGRA World and one-pass HDR/alpha-preserving fused shader | RTX 2070 SUPER + compiled AEX + test suite | PASS on mock Worlds |
| D3D12 debug validation | Hardware debug layer + 12 concurrent GPU World callbacks | PASS, zero error-severity messages, not Adobe host |
| Healthy GPU MFR-style saturation | 4 cached + 16 overflow contexts with admission wait, up to 32 simultaneous callbacks | PASS on SDK-shaped mock |
| Concurrent GPU Device Setdown and unknown post-submit completion | Active callback lease + 12/32-way teardown race + quarantined submitted GPU references | PASS synthetic race; actual device-loss recovery incomplete |
| Independent Windows D3D12/Vulkan shared memory | Shared Win32 D3D12_RESOURCE handle import, same LUID and 1MiB, 262144 uint32 samples both ways | PASS on standalone RTX |
| Cross-API GPU synchronization | D3D12 shared fence imported as Vulkan timeline semaphore, GPU-only waits/signals | PASS on standalone RTX |
| Actual AE host GPU World exportability/queue state/accounting | Read-only D3D12 world diagnostic built, positive/negative mock proven | **UNKNOWN**: Adobe did not allocate tested Worlds |
| AE2025 per-user plugin discovery | Started isolated AE2025 with temporary user-local AEX | **NO module observed**; underlying cause unproven; test copy removed |
| Windows CTest suite | Current JUnit report + SHA-256-bounded plugin binary | **21/21 PASS** |
| macOS universal native Metal GPU AEX-equivalent | Common EffectMain Metal-variant C++ syntax tested with MSVC, Objective-C++/MSL/CMake/Rez/codesign staged | **UNBUILT ON MAC; UNVERIFIED** |
| Whole-product most efficient backend on any PC | Actual AE CPU/GPU timing and VRAM peak across devices and workloads | **NOT DETERMINED** |

The current AEX follows the official SDK sample's PF_HandleSuite1 GPUData ownership *pattern* (the SDK API itself declares effect-owned void* and does not mandate PF_Handle) and a canonical shared Windows/Mac PiPL source generated with Adobe PiPLTool. The actual PiPL specification version is read from the AEX and verified against SDK 25.6 (13.29). The SDK-shaped host verifies balanced handle allocation/disposition, missing suite graceful failure, and the 42-run post-fix full-device stress dataset. See F-GPU-024. All Windows lab evidence and SHA-256 receipts reside in D:/Developer/AEEffectPerformanceLab/results/. The 42-run parallel stress dataset is stored under AEIG datasets/ae-gpu-mock-mfr-admission-20261014.csv. New findings are F-GPU-018 through F-GPU-025. Historical 42-run GPU data predates the SDK handle/PiPL correction; corrected experiments are separately retained under datasets/ae-gpu-mock-mfr-admission-canonical-pipl-handle-20261014.csv.

## Core decision architecture

Treat the Adobe plugin framework as an externally owned, non-overridable contract. A vendor GPU compute API is an **implementation choice below** the host's supported callback:
- Windows: host-native PF_GPU_Framework_DIRECTX using the supplied ID3D12Device, ID3D12CommandQueue, and GPU World ID3D12Resource, with GPU device state stored in a host PF_Handle; CPU SmartFX always provides the low-end and GPU-unavailable fallback.
- macOS: host-native PF_GPU_Framework_METAL using supplied MTLDevice/queue/World buffers; CPU SmartFX fallback. Shared C++17 EffectMain, canonical PiPL, PF_HandleSuite1 GPUData lifecycle, math, parameters, request lifecycle, 24-byte GPU constant ABI; native Objective-C++/MSL vs native C++/HLSL backend implementation.
- NVIDIA-specific compute: CUDA can be independently competitive for specialized algorithms; first prove supported host framework, exact input/output format, host device residency and quantified end-to-end benefits, not kernel-only speed.
- Windows internal Vulkan execution: only when actual AE-owned World sharing, compatible external memory, same GPU LUID, GPU-only semaphore synchronization, resource-state/queue ownership and host GPU-memory allocation/accounting have *all* been established. Otherwise reject direct zero-copy. A D3D12 staging copy to plugin-shared Vulkan memory is a separate candidate with explicit copy/storage/sync costs.

## Optimization objective and comparability

For a concrete effect algorithm, target frame/ROI, host AE build, hardware/driver, bpc/pixel encoding, cache/MFR settings and current residency, compare

  whole_frame_wall = host_dispatch + device_setup_amortized + required_upload +
                     GPU_or_CPU_work + GPU_queue_and_sync + required_readback +
                     host_completion_and_cache_overhead.

Prioritize **correct pixels (including negative and >1 HDR), memory lifetime and no crashes**. An implementation that saves 0.2ms but corrupts even a rare frame, exhausts memory or races GPU setdown must be rejected. Measure CPU callback p50/p95/p99, GPU timestamp work where supported, render queue wait, peak device/host memory, repeated cold/warm execution, device removal and cancellation.

When comparing candidates with different residency, record real CPU↔GPU transfer overhead inside AE. Include transfer costs for any pipeline conversion induced by selecting a particular backend. The C++17 eligible_production_candidates policy refuses:
1. missing actual Adobe host measurement;
2. missing/nonmatching benchmark fixture key;
3. GPU/CPU residency conversion not measured in the candidate's whole-frame timing;
4. any of the existing parity, stability, sanctioned-host-path, memory budget and OS eligibility constraints;
5. Vulkan unless its seven host interop gates are all verified.

The Pareto frontier only compares candidates from **identical benchmark fixture keys**, not unrelated hardware/algorithms. **No candidate currently passes production host admission**, because actual host measurement has not occurred. The specialized full-frame sub-1ms selector additionally requires AE Composition Profiler uncached total Frame Render Time, 120+ frames, and p95/p99/maximum observed below 1ms. The current official goal result is NOT VERIFIED, not the same as mock host callback p95. See [Sub-1ms AE Total Frame Performance](one-millisecond-total-frame.md). This is deliberate fail-closed behavior. See F-GPU-023.

## Workload-dependent starting candidates (not universal winners)

| AE workload | First host-sanctioned path to benchmark | Measure competing path |
| --- | --- | --- |
| 1–2 tiny CPU-side ROI tiles, low-end PC | Scalar/SIMD CPU SmartFX | Native GPU only if upload+submit+readback end-to-end wins |
| Large GPU-resident 32bpc pixel-wise/small neighborhood | Native D3D12 (Win) or Metal (Mac) fused dispatch | Host-supported CUDA (Windows/NVIDIA) or qualified Vulkan internal compute |
| Long kernels / transforms / convolution / FFT | GPU-native optimized libraries and algorithm-specific convolution method | Direct vs separable vs FFT tiled/GPU and CPU for very small kernels |
| MFR with many simultaneous frames | Bounded command contexts, immutable pipeline cache and request-local scratch | Cached vs uncached contexts and different admission limits **on actual AE** |
| Tight VRAM / heavy sustained frames | CPU SIMD or tile-based native GPU with explicit budget | Intra-GPU recomputation vs memory reuse; account for host GPU allocation suite |
| Cross-platform commercial effect | Shared C++17 semantics, separate D3D12/Metal native adapters | Optional shared shader generator only after native parity |

## Ownership rules that cannot be traded away for speed

1. AE's input/output GPU Worlds are **borrowed** and may only be accessed within documented checkout/lifetime. Maintain explicit callback-local checkin and GPU-fence retirement; never dereference an AE World after host checkout validity.
2. No GPU command list allocator reset before completion of its previous submitted work. Each concurrent request owns an exclusive Context until fence completion. The immutable shader PSO may be device-scoped.
3. The current Windows host SDK does not expose Vulkan as a PF_GPU_Framework option. A local enum/header addition never changes the Adobe host allocation model or render scheduler.
4. Unknown device completion after submission is **not** proof that it is safe to free resources. Quarantine to prevent use-after-free; track the leak and mark device unhealthy. Shipping needs defined recovery, not permanent memory growth.
5. A plugin-owned mutex must never be held while calling arbitrary AE host callbacks. Device setdown should not destroy state with active render leases; host must still guarantee GPUData pointer validity when callback admission begins.
6. Instrumentation must be off by default. The shared-handle probe adds COM calls, Win32 HANDLE acquisition and file writes; benchmark runs must be uninstrumented unless explicitly testing diagnostic cost.

## Exact final Windows reproduction

From D:/Developer/AEEffectPerformanceLab using VS2022 x64, DXC, SDK 25.6:
- cmake -S . -B build -G "Visual Studio 17 2022" -A x64 -DAEPERF_BUILD_AE_HOST=ON
- cmake --build build --config Release --parallel 4
- ctest --test-dir build -C Release --output-on-failure --output-junit results/ctest-final-windows-20261014.xml
- python tools/write_backend_admission_receipt.py
- python tools/verify_cross_platform_gpu_contract.py
- python tools/record_gpu_mock_mfr_admission.py  (42 independent real GPU processes, current corrected AEX; saves an immutable separate receipt)

The machine receipt results/ae-backend-admission-20261014.json includes the current compiled AEX SHA256, CTest JUnit hash, the 42 historical parallel load runs, and each true/false production admission condition. The original 42-run stress data predates later source fixes and has its **own historical binary hash**; do not conflate the two binaries.

## Mac build and final admission

On an actual Mac with Xcode/Metal tools, an extracted licensed Adobe AE SDK and suitable host installation, run AE_SDK_ROOT=/absolute/SDK/Examples bash tools/check_macos_bundle.sh. This checks the Universal arm64/x86_64 .plugin, offline MSL .metallib, PiPL .rsrc, ad-hoc codesign and package plist. **This has not been executed on Mac hardware.** Only then install in a disposable test environment; prove an actual AE Metal callback and GPU World 32bpc pixel parity, MFR, device reset and residency/timing. Source-stage verification is not a substitute for deployment.

## Last mandatory blockers

The world's most robust native AE effect system cannot be certified without:
- Disposable **actual** AE2026 host executable loading the research AEX, 8/16/32bpc CPU parity, actual 32bpc GPU render and input/output host-owned GPU World/queue-state evidence.
- Real AE MFR cancellation, project close, device setdown and driver GPU reset; bounded resource retirement without uncontrolled leaks.
- Real Mac Xcode/Metal/Rez/codesign/Universal build and native AE callback/pixel/driver testing.
- Comparable workload/hardware/driver/host benchmarks reporting CPU/GPU p50/p95/p99, peak VRAM/RAM and end-to-end total time for CPU, native D3D12/Metal, supported CUDA and qualified Vulkan as appropriate.

**Provisional architecture has been implemented; universal "best in world" production proof has not.** This chapter's purpose is to prevent premature claims and to make each future promotion reproducible and falsifiable.

## 2026-10-14: Composition Profiler 1ms research target (F-GPU-025)

The newly requested outcome metric is **After Effects's Timeline footer TOTAL Frame Render Time**, as reported by its Composition Profiler. This is a separate performance domain from the 48-callback D3D12 AEX mock suite: the latter does not include real AE's other layers, source/comp cache, frame scheduling, render queue, and source load. Adobe documents that partially cached frames have an asterisk and do not report the full cold-frame render. See [Sub-1ms AE Total Frame Performance](one-millisecond-total-frame.md).

The latest 21/21 Windows CTests cover correct SmartFX invariant max_result_rect across changing ROI requests and 3 native D3D12 wave mappings with padded pitches; 42/42 fresh full-process mock-MFR stress tests cover the exact current AEX. A shuffled 45-run D3D12 kernel-layout A/B benchmark (48 GPU-resident effect callbacks/process, 5 repetitions/mode/size) shows that some 4K p95 values EXCEED 1ms on the same GPU despite GPU single-pass fusion. Default 16x16 4K median-of-run-p95=1.2463ms; 256x1=1.2416ms; 64x4=1.3141ms. Those are mocked callback timings, **not** AE Frame Render Time. We have no grounds for claiming any of the modes will make actual Adobe cache/render <1ms. Do not automatically replace the default based on noisy five-repetition per-mode evidence.

CPU AVX2 synthetic SmartFX measured 1920x1080 p50=7.7676ms/p95=10.6689ms and 3840x2160 p50=29.5483ms/p95=44.0611ms (48 callbacks per resolution, single process). The tested simple fused effect is much faster on a **GPU-resident** mock input, but CPU/GPU end-to-end costs are not comparable unless Adobe host pipeline residency is matched.

Most importantly, RTX 2070 SUPER's NVIDIA-documented VRAM bandwidth is 448GB/s. Simply reading and writing a full 8K RGBA32F frame once demands 1.06168GB and has an ideal lower bound of 2.37ms; therefore a universal full-frame <1ms on this card is physically impossible. Even 4K's 0.592ms ideal bandwidth floor leaves little room for actual AE overhead. The new strict C++ function eligible_sub_ms_ae_frame_candidates() rejects kernel-only, cached, mock, non-host or insufficient-sample evidence. Its positive test uses a **synthetic injected candidate only** to test the gate, not an actual qualifying backend.

Current evidence and reproducibility are in D:/Developer/AEEffectPerformanceLab/results/ae-composition-profiler-1ms-gate-20261014.json, native-d3d12-threadgroup-ab-sdk-roi-20261014.json, native-aex-gpu-mfr-admission-frame1ms-lab-20261014.json and deliverables/AEPerfHostProbe-Frame1ms-RESEARCH-v2-20261014.zip. Full captured Adobe Timeline footer data and actual macOS GPU execution are still missing. Source finding F-GPU-025.

## 2026-10-15: User-only Adobe host restriction and cross-device resource validation (F-GPU-028)

**Only the user may operate the real Adobe After Effects application.** The research assistant must not install or remove native effects from the actual scanner, launch/quit AE, run JSX against the app, control the UI, modify a project, change preferences or trigger a render. The Skeleton's automated host helper has been converted to strictly READ-ONLY preflight, with opt-in installation permanently disabled. A separate JSX source is available only for optional user-invoked read-only effect-catalog inspection, and cannot start a render or quit the app. Python and PowerShell static CI checks enforce this bound. No true Adobe host MFR/GPU/render admission has been established.

The portable D3D12 resource adapter now verifies the owning ID3D12Device identity for **both** borrowed GPU input/output Worlds before any command submission, using ID3D12DeviceChild::GetDevice. A real-WARP-versus-NVIDIA synthetic-host negative test rejected both foreign input and foreign output, then 12-way normal GPU concurrent parity still passed. Windows CTest 16/16 PASS. The 30-run GPU callback benchmark recorded 4K median process p95 1.8375ms / 1.8102ms / 2.1848ms for 16x16 / 256x1 / 64x4; all 4K process-p95 values exceeded 1ms. These results are mock callbacks, *not* actual Adobe Frame Render Time; uncontrolled cross-run GPU variability prevents crediting or blaming the device-check overhead. See F-GPU-028.

Primary Windows D3D12 resource identity reference: https://learn.microsoft.com/en-us/windows/win32/api/d3d12/nf-d3d12-id3d12devicechild-getdevice

## 2026-10-15 GPU device-removal and cancellation qualification update (F-GPU-029)

The separately maintained public Skeleton has corrected a material D3D12 device-loss lifetime defect: `ID3D12Fence::GetCompletedValue()` returns `UINT64_MAX` when the device is removed. A raw `>= fenceValue` comparison could mistake that sentinel for successful GPU completion. The current D3D12 adapter rejects the sentinel in both render completion and device destructor/quarantine paths. A hardware-linked native unit test checks the sentinel numerically; it does not physically remove the GPU.

MFR context-pool admission now checks an optional request-local `PF_ABORT` callback while waiting and exits without poisoning a healthy GPU if cancellation happens before dispatch. Cancellation after submission is still subject to proof of GPU completion and the existing conservative 15-second fence wait; no speculative early release is allowed. A cross-platform source-only CI check rejects regressions to the unsafe D3D12 fence comparison. Windows compiled AEX with SDK-shaped mock host: 16/16 CTests pass. Actual Adobe host/device-lost and Mac Metal tests still remain unverified.

Post-change performance experiment: 180 independent physical D3D12 GPU mock processes, 180/180 numerical parity PASS, 30 process replicates per GPU layout/resolution, 48 GPU callbacks/process. Median process p95 at 4K: 16x16 1.3044ms, 256x1 1.3509ms, 64x4 1.2595ms. Extremely large outliers occurred in all shapes, with unknown cause; no alternative meets the stable improvement promotion gate. Default remains 16x16. This is NOT Adobe's actual Composition Profiler whole-frame render time.

Complete source/hashes and evidence: research/findings/F-GPU-029-d3d12-fence-removal-and-mfr-cancel-admission.md. Source-only Skeleton Git commits 4d83c70 and 9cfcf6e; current testing AEX SHA-256 114ae63021474cf67aa99e89ae687b05f76a7a697ca6d2efd723fe1901016882. The user-only actual Adobe After Effects host-operation restriction remains in force.
