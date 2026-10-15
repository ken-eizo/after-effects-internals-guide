---
status: research
last_verified: 2026-10-14
evidence: AE 25.6 local distributed headers and SDK_Invert_ProcAmp sample; published Adobe, Apple and Microsoft API contracts; reproducible standalone D3D12 Windows experiment
---
# Cross-Platform Native GPU Effects: Shared C++ Core, Specialized Execution Backends

## Research question
How can an AE effect share the maximum semantic, architectural and shader source between Windows and macOS *without degrading* runtime performance, correctness, hardware support, memory usage or host lifecycle compatibility? This is an architecture and qualification guide, **not** a declaration of final fastest implementation.

The sandbox/workbench is `D:\Developer\AEEffectPerformanceLab` (outside AEIG). Only evidence-graded findings, stable rules and independently reproducible, promoted fixtures belong in AEIG. The earlier temporary experiment code was moved out of AEIG to `D:\Developer\AEEffectPerformanceLab\gpu-optimal-archive-20261014`.

## Supported host-native references (distributed Adobe SDK)

| Host/platform | Official GPU suite framework | SDK-exposed device / submission | Initial default |
| --- | --- | --- | --- |
| Windows Intel/AMD/NVIDIA, supported x64 host | DIRECTX | `ID3D12Device*`, `ID3D12CommandQueue*`, `ID3D12Resource*` for GPU world/buffer access | D3D12 GPU Smart Render + CPU SIMD fallback |
| Windows NVIDIA, supported host | CUDA | `CUdevice`, `CUcontext`, `CUstream` by framework | candidate for measured algorithm/library advantage |
| macOS Intel/Apple Silicon, supported host | METAL | `id<MTLDevice>`, `id<MTLCommandQueue>`, GPU `id<MTLBuffer>` | Metal GPU Smart Render + CPU SIMD fallback |
| Windows on Arm, where Adobe host supports native effect plugins | host-specific device support requires runtime test | ARM64 PiPL `CodeWinARM64` exists | portable CPU baseline, GPU only after actual host admission |
| macOS Apple Silicon and Intel | universal plugin requires both `CodeMacARM64` and `CodeMacIntel64` in PiPL | Xcode x86_64 + arm64 builds | same source, architecture-specific binary slices |

Official setup/render contracts include `PF_Cmd_GPU_DEVICE_SETUP`, `PF_Cmd_SMART_PRE_RENDER`, `PF_Cmd_SMART_RENDER_GPU`, `PF_Cmd_GPU_DEVICE_SETDOWN`; GPU feasibility is **per request**. Public SDK does not expose host Vulkan framework registration, so Vulkan is optional experimental interop, not a foundational requirement.

**Important distributed-sample difference:** official `SDK_Invert_ProcAmp.cpp` uses the AE-provided D3D12 queue, and helper `DirectXUtils.cpp` synchronously waits on a fence. Its Metal sample encodes two compute dispatches and commits a command buffer without an analogous explicit blocking wait in the shown path. This is an observed sample difference, not a universal guarantee that arbitrary cross-API nonblocking submissions are allowed.

## Logical modules and share ratio

- **Common C++17 core (target 100% shared):** evaluation semantics, parameter snapshots, ROI/bounds/halo, graph planner, kernel fusion, liveness/scratch accounting, resource ownership state machine, MFR admission rules, CPU reference and test fixtures, feature detection, benchmark decisions. Only standard C++ types at boundaries.
- **Common AE SDK adapter (mostly shared C++):** selector dispatch, host suite acquisition, pre-render checkout and cleanup, CPU pixel format interpretation, state serialization, callback exception firewall, GPU feasibility, logging. Guard Windows/Mac-only host flags and PiPL resource slices.
- **GPU execution adapters (intentionally platform-specific):** D3D12 COM resources/barriers/descriptors/queues and Metal device/buffers/encoder/command buffer/residency; CUDA an optional NVIDIA specialization.
- **Shader math (shared if provably equivalent):** a verified intermediate shader math contract, with HLSL→DXIL native Windows; HLSL→DXIL→Apple Metal Shader Converter candidate for recent macOS; separately compiled native MSL fallback. Slang and SPIRV-Cross remain optional compiler experiments.
- **Packaging/signing (platform-specific):** Windows .aex/PiPL and Mac Universal .plugin bundle/PiPL/signing.

A multi-target shader compiler should not be required to run the CPU fallback. Shader conversion must take place at build/package time when possible, not on every frame or device request.

## Apple Metal Shader Converter: qualified common HLSL route [Apple public API]

Apple provides a converter from DXIL to Metal `metallib`, including a Windows converter. Its published requirements include macOS 14 and Argument Buffers Tier 2 support for converted libraries; older operating systems/devices may be excluded. DXIL root binding/descriptor tables require converter-specific argument-buffer layout and runtime binding. Therefore **a converted HLSL shader cannot be bound as if it were ordinary hand-authored MSL with fixed `[[buffer(0)]]` slots**.

Accept as shared-source production backend only after: compiler version pin, converted shader compilation, reflection and binding ABI validation, GPU output parity, buffer residency correctness, MFR stress, cold-start and end-to-end performance tests on Apple Silicon and Intel Mac. Native MSL path remains a competing, potentially faster and more compatible baseline.

Slang's official target matrix includes D3D12, CUDA and Vulkan; its Metal code generation is presently marked experimental. SPIRV-Cross officially maps SPIR-V to MSL but requires resource remapping/ABI tests. Treat both as alternatives rather than unquestioned defaults.

Apple Metal-cpp is a C++17 Metal binding published as having no measurable wrapper overhead versus Objective-C; it is suitable for exploration of an all-C++ host adapter. However Cocoa lifetime/autorelease semantics and bridging of AE-owned Objective-C Metal objects still require real Mac verification.

## Apple Silicon vs Intel Mac memory model

Apple Silicon unified physical RAM means fewer mandatory PCIe crossings for appropriate storage modes, but CPU/GPU cache, visibility, format conversion, queue synchronization and ownership still have costs. macOS discrete Intel/AMD Macs may require explicit CPU/GPU copies or managed resource synchronization.

Apple now marks `MTLStorageModeManaged` deprecated, without effect on Apple Silicon, and recommends Shared there. The distributed Adobe Metal sample creates parameter buffers with Managed mode: this is a modernization target only after host-specific tests, not a proven failure.

Use `MTLDevice.recommendedMaxWorkingSetSize` and `currentAllocatedSize` as measured budgeting hints; never assume they alone represent AE's complete memory allocation/eviction policy or a hard guaranteed capacity.

## Windows memory and GPU scheduling

Use `IDXGIAdapter3::QueryVideoMemoryInfo` for local/nonlocal dynamic process budgets and usage, not advertised VRAM capacity as a plugin scratch budget. AE may itself reserve/cache substantial memory. Never treat DXGI budget as an entitlement to allocate directly outside host GPU Suite.

D3D12 per-in-flight command allocator/list, descriptor suballocation, queue lifetime, resource barriers and GPU completion must be explicit and race-free under MFR. Official `DirectXUtils.cpp` describes its descriptor heap as suboptimal and performs a CPU fence wait in its reference implementation. Removing waits or resetting an allocator before GPU completion is not an optimization: it is a correctness hazard.

## Cross-platform memory and MFR rules

1. Preserve host input/output GPU residency whenever a supported GPU World is available.
2. First eliminate redundant intermediate images and passes when semantic equivalence is established; then tune workgroup/wave, dispatch and launch overhead.
3. Bound plugin scratch by `per_frame_scratch × admitted_inflight + persistent_gpu_resources`; account separately for host-owned input/output worlds and physical cache residency.
4. Use AE Compute Cache only for reconstructable derived state with stable semantic keys; render sequence remains read-only by default. Never simulate sharing with `PF_OutFlag2_MUTABLE_RENDER_SEQUENCE_DATA_SLOWER`.
5. Guarantee clean pre-render data destruction even if there is no matching render; do not hold host-suite pointers beyond legal callback scope.
6. Ensure GPU submitted work finishes before referenced host worlds or transient resources may be reused; cancellation and device teardown cannot invalidate work in-flight.
7. Treat device loss, GPU API negotiation/fallback and GPU queue failure as eligibility changes, not partial valid output.
8. Capture format, ROI, floating-point precision, alpha and negative/HDR behavior as part of each cache/performance fixture.

## Local experimental result and evidence boundary

Windows RTX 2070 SUPER isolated D3D12: 1920×1080 32-bit float RGBA invert + gain/bias 2 passes vs fused 1 pass. In a 40-repetition GPU-resident run, p50 GPU compute changed 0.33363 ms → 0.16618 ms, submit-to-GPU-completion p50 0.46960 → 0.26190 ms. In separate output-readback runs, submit-to-completion p50 3.72940 → 2.99180 ms. CPU reference image parity passed (max abs error 2.38419e-7); one 33,177,600-byte intermediate buffer eliminated. **Independent D3D12 process, not AE effect/MFR/macOS**; figures are not portable performance constants. Raw conditions under the external workbench.

## Evidence promotion gates

- RESEARCH IDEA: theoretical benefit, document counterexamples and assumptions.
- BUILD-VERIFIED: compiler + shader, pinned source/compiler hashes.
- STANDALONE VERIFIED: numerics, GPU synchronization, memory, hardware/driver, isolated workload receipt.
- HOST VERIFIED: actual AE callback selectors, GPU Worlds, host resource ownership, MFR and measured CPU+GPU critical path.
- CROSS-PLATFORM VERIFIED: Windows and macOS, Apple Silicon and Intel Mac (where supported), supported versions, fallback and low-memory behavior.
- PRODUCTION RULE: repeatable p95/p99, throughput, peak memory, device loss/cancellation stability and accuracy advantage within explicit hardware/workload envelope.

No global “world's fastest” or universal backend selection can be declared before the host and cross-platform gates pass.

## References
- [Optimal Effect Engineering](optimal-effect-engineering.md)
- [Vulkan Feasibility Boundary](vulkan-host-backend-feasibility.md)
- [MFR GPU Concurrency](../mfr/gpu-concurrency-experiment.md)
- Reproduced Windows D3D12 standalone fusion/residency receipt: F-GPU-007; stable summary at `datasets/ae-gpu-standalone-20261014-fusion-summary.csv`.
- Native Windows AE SDK build and entry smoke (not in-host): F-GPU-008. External workbench `D:\\Developer\\AEEffectPerformanceLab\\ae-host`.
- Adobe: https://ae-plugins.docsforadobe.dev/intro/gpu-build-instructions/
- Adobe: https://ae-plugins.docsforadobe.dev/intro/apple-silicon-support/
- Adobe: https://ae-plugins.docsforadobe.dev/intro/windows-on-arm-support/
- Apple: https://developer.apple.com/metal/shader-converter/
- Apple: https://developer.apple.com/metal/cpp/
- Apple: https://developer.apple.com/documentation/metal/mtlstoragemode/managed
- Apple: https://developer.apple.com/documentation/metal/mtldevice/recommendedmaxworkingsetsize
- Microsoft: https://learn.microsoft.com/en-us/windows/win32/api/dxgi1_4/nf-dxgi1_4-idxgiadapter3-queryvideomemoryinfo
- Slang: https://github.com/shader-slang/slang
- SPIRV-Cross: https://github.com/KhronosGroup/SPIRV-Cross
## Windows host adapter status update: native D3D12 selector mock and bounded reuse (2026-10-14)

The external workspace `D:\Developer\AEEffectPerformanceLab` now builds one native Windows GPU-capable AE SDK effect `AEPerfHostProbe.aex`: its C++17 common semantic core is linked to a D3D12 execution adapter and a compiled DXIL BGRA128 shader. PiPL OutFlags2 (0x2A001400) and encoded version (524289) are extracted from the actual Win32 resource and verified against C++ GlobalSetup. GPU_DEVICE_SETUP / SMART_PRE_RENDER / SMART_RENDER_GPU / GPU_DEVICE_SETDOWN invoke the real linked EffectMain using SDK-shaped mock PICA/World/GPU suites. This is **not** the real Adobe AE host.

Real D3D12 device simulation validated GPU output parity with padded BGRA float worlds, 12 concurrent independent requests, no full-frame intermediate; 5/5 build/tests passed. Separate 12-run randomized A/B of reusable D3D12 command contexts vs rebuilding every callback (48 frames per run, tiny 19x13) yielded callback wall median 0.22090 vs 0.08065 ms (approximately 2.74x speedup). Extreme p95 tails occurred. This is an *isolated mock-host measurement*, not AE MFR or actual host callback latency. See F-GPU-009/F-GPU-010 and dataset `datasets/ae-gpu-mock-host-context-pool-20261014.csv`.

The Windows-specific GPU adapter is isolated from the shared pixel math and from a future native macOS Metal adapter. No Mac host connected, so macOS converter ABI/runtime and universal .plugin remain untested. Maintain OS- and framework-specialized execution but share the canonical math/ROI/planner, verified test vectors and memory-budget rules.

**Updated lifetime gate:** Previously the overflow transient could be destroyed with unknown GPU completion; this was corrected in F-GPU-014. Contexts and D3D12 World COM references now remain quarantined on post-submit failure; an unhealthy device refuses new admissions. The emergency quarantine may leak until process exit, so bounded deferred retirement under *real* device loss, and a genuine AE MFR/setdown concurrency test, remain shipping gates. Keep a strict test-host vs Adobe-host evidence boundary. Adobe's `-r` script invocation can route to an existing AE process, so avoid commandeering active user projects for test execution.

## Interop experimental verification and macOS architecture boundary (2026-10-14)

F-GPU-015 and F-GPU-016 verified a full shared buffer and external GPU timeline fence roundtrip on a Windows RTX 2070 SUPER: same physical D3D12/Vulkan adapter, 1 MiB of shared GPU memory, 262144 checked uint32 values in both directions, GPU-only interop ordering with a single final CPU verification wait. The executable, full raw receipt and 8-run SHA256-pinned recurrence live in the external workbench. This is **not actual Adobe AE GPU World interchange**. F-GPU-017 implements an opt-in native EffectMain diagnostic with 96/96 correct classifications for ordinary mock Worlds and 96/96 for explicitly shared mock Worlds; no real AE host GPU World was tested.

The Windows build now has a 7-gate runtime backend planner for VulkanInterop and 11 passing CTests. It never auto-selects the Vulkan backend on the basis of the independent GPU experiment alone. Native D3D12 + CPU SIMD remains the usable Windows laboratory baseline. The Mac CPU SmartFX .plugin bundle CMake/Rez target is source-staged and conditionally compiled from the very same C++ EffectMain source; the Metal host path, universal Xcode builds, Metal library shader compilation and actual Apple GPU parity are not tested on macOS.

Future Mac GPU execution must preserve the same semantic kernel tests and shared request-scoped state model but have its **own** device/queue/MTLBuffer/Metal encoder implementations. “Same effect source” means no duplicated policy, metadata, or pixel math; it does **not** imply forcing D3D12/Vulkan ABI onto Apple hardware. See [Cross-API Interop Verified Boundaries](cross-api-interop-verified-boundaries.md).

## October 14 final source-stage: same C++ EffectMain on Windows D3D12 and macOS Metal

An additional native Metal Smart Render path has now been **implemented in source**, not only planned. The Windows lab contains gpu/metal/native_effect.hpp, native_effect.mm and ae_world_fused.metal, plus a CMake Xcode .plugin target with offline Metal library generation and a Mac PiPL declaring GPU_RENDER_F32, Intel x86_64 and ARM64 entry points. The shared ae-host/AEPerfHostProbe.cpp dispatches native host GPU selectors to D3D12 on Windows and Metal on macOS. Metal uses AE-supplied MTLDevice / MTLCommandQueue and MTLBuffer Worlds, one fused BGRA128 shader pass and a conservative completion wait. The pixel semantics, CPU SmartFX fallback, host checkout/checkin policy and GPUData active-call lease are intended to stay common.

**Verification grade:** MSVC/Windows compiled the same C++17 AE EffectMain source both as a real Windows DX12 AEX and independently with Metal selector defines, using official AE SDK headers. This checks shared C++ source-compatibility only; the Objective-C++ Metal implementation, metallib, Apple PiPL Rez and Universal .plugin are **NOT compiled or tested on a Mac**. No Apple Metal end-to-end timing or even Apple runtime plugin loading is verified. See F-GPU-020 and D:/Developer/AEEffectPerformanceLab/ae-host/mac/README.md.

On Windows, independent GPU/interop experimental proof in F-GPU-015/F-GPU-016 is separate from the real Adobe host GPU World gate in F-GPU-017. The Windows native AEX mock-host Smart Render ran 32 requests sharing one D3D12 device and queue, and 42 randomized stress processes passed. A saturated context pool now queues rather than rejecting healthy frames; setdown waits for active render leases. The current regression includes 15 tests. See F-GPU-018 and F-GPU-019 and the MFR concurrency page.

**Best portable design is shared semantic source and host adapter policy, not forcing a cross-API backend.** Specialized D3D12 and Metal ABI/execution code is essential. Avoid claims of universal fastest performance until real AE runtime timing and true Mac hardware measurements exist.

## Shared parameter ABI, compile-time checks (2026-10-14)

The Windows D3D12 HLSL compute shader and source-staged macOS MSL compute shader now use the same 24-byte, six-word input constant contract. The canonical C++17 GpuFrameConstants in the external lab core/gpu_frame_constants.hpp is defined as unsigned 32-bit width/height/inputPitchBytes/outputPitchBytes followed by float gain/bias; C++ compile-time size/offset and runtime serialized-word tests are included in the core regression. D3D12 passes these 24 bytes directly as six 32-bit root constants. Metal passes the same six words to the compute encoder, and its shader converts byte pitches into float4 offsets. No shader path may silently use pixels in place of bytes.

This is a concrete source-sharing and numerical-correctness measure, not a claim that MSVC's verification proves MSL's binary ABI. The latter still requires Mac metal compiler and AE Metal GPU World parity with noncontiguous row pitches. See F-GPU-020. Hardware-specific compilation/execution stays separate by design.

## Actual SDK 25.6 API correction superseding older synthetic host evidence (F-GPU-024)

The original GPU AEX/SDK-shaped mock passed with a raw C++ GPUData pointer from GPU_DEVICE_SETUP. The official SDK_Invert_ProcAmp sample instead uses PF_HandleSuite1.host_new_handle. **Critically, AE_Effect.h explicitly declares gpu_data as an effect-owned void*: raw pointers are NOT thereby forbidden.** We standardized the current adapter on the sample-style PF_Handle to exercise that ownership/cleanup model, not because a PF_Handle is mandated by the API. Historical synthetic tests, whether raw-pointer or handle-style, cannot alone prove actual Adobe host behavior. The current AEX stores ManagedGpuDevice* in a host-allocated PF_Handle and calls host_dispose_handle in setdown. Both GPU mock hosts now enforce a real double-indirection handle lifecycle, balanced allocations/disposals, and fail-closed when the PF_HandleSuite is absent.

A second untested original ABI defect was the hand-transcribed Windows PiPL spec version 13.28, while the actual SDK25.6's Adobe PiPLTool generates 13.29. The Windows AEX and macOS source now consume the same canonical ae-host/AEPerfHostCanonicalPiPL.r. The compiled AEX's actual PiPL bytes are checked against SDK PF_PLUG_IN_VERSION and PF_PLUG_IN_SUBVERS. All 18 current Windows CTests passed (including Handle Suite missing/error-path injection). Forty-two independent hardware-backed synthetic host stress processes were **rerun on the new fixed AEX**, all with handle alloc=dispose=1 and pixel parity PASS; independent new raw JSON and AEIG CSV retained. See research/findings/F-GPU-024-adobe-sdk-gpu-handle-and-canonical-pipl-abi.md. These important fixes **do not** prove that real Adobe AE2026 loads the effect; Mac Objective-C++/Metal and real-host Worlds remain untested.

## Frame-render-time outcome standard update (F-GPU-025)

The current strict optimization target is the actual After Effects Composition Profiler Timeline footer TOTAL "Frame Render Time" for a completely uncached frame. No current synthetic AE/GPU mock data constitute that measurement; all present actual host performance/1ms claims must fail closed. On real RTX 2070 SUPER hardware the 21-test Windows AEX passes, 42/42 MFR-like mock stress cases pass, and 45 randomized shader tiling A/B subprocesses pass but several 4K mocked callback p95 measurements EXCEED 1ms. Native 16x16 dispatch remains default pending genuine AE full-frame benchmarks. Actual Adobe environment, Mac Metal and nontrivial workloads are not performance-certified. See [Sub-1ms AE Total Frame Performance](one-millisecond-total-frame.md) in the GPU system docs; the formal finding is F-GPU-025. Do not treat an isolated GPU microbenchmark as Adobe's frame cache/render time.
