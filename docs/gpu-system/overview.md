---
status: active
last_verified: 2026-09-23
---
# GPU System

Local modules and Debug Database expose GPUFoundation, GPUKernels, RendererGPU and GF/DS controls. Map CPU/GPU backend selection, memory pools, device caches, precision differences and synchronization.

## Cross-host GPU substrate evidence
The AE 25.6 `PF_SmartRenderInput`, `PF_GPUDeviceSetupInput`, and `PF_GPUDeviceSetdownInput` all carry a `device_index` whose Header comment explicitly says it is for use with `PrSDKGPUDeviceSuite`.

That is direct distributed-header evidence that the AE Effect GPU path is wired to the Premiere/MediaCore GPU-device abstraction rather than merely resembling it by convention.

The shared design includes device enumeration, exclusive device access, device memory, pinned host memory and GPU-resident frame/world handles. AE wraps rendered images as GPU worlds; Premiere exposes GPU PPix, but both sit above the same style of device substrate.

### Research consequence
When AE's GPU behavior is underdocumented, Premiere GPU Suite revisions can reveal backend/device-memory contracts that are likely shared below the host-specific image container. Any such inference must still be verified against AE runtime behavior.
## Runtime frame/device bridge
Installed AE 2025 `PF.dll` exposes the bridge implied by the public GPU-effect contract. GPU effect worlds can be created against `GF::Device`, uploaded through `MF::IVideoFrame`, converted back to `PF_World`, queried for GPU residency, and mapped to host image containers.

Useful internal surfaces include `CreateGPUEffectWorld`, `GPUFrameUpload`, `GPUFrameToWorld`, `GetCurrentDevice`, `IsRendererGPU`, renderer GUID accessors, and allocation checks. BEE render scheduling also contains a VRAM-aware thread-count decision.

Model the path as `PF world <-> shared video frame <-> GPU device/queue`, not as a self-contained effect-owned buffer. Resource lifetime, device completion, frame identity and cache residency remain separate concepts.

Reproducible inventory: `datasets/ae-2025-gpu-execution-surface.csv`. Finding: `F-GPU-005`.

## Two-stage GPU capability negotiation
The public Effect GPU contract has two distinct decisions.

1. **Device/framework capability** — `PF_Cmd_GPU_DEVICE_SETUP` is called for a concrete `what_gpu`/`device_index`. The effect reports which GPU render capabilities it supports for that device and may allocate device-specific `gpu_data` that lives until `PF_Cmd_GPU_DEVICE_SETDOWN`.
2. **Request-specific feasibility** — during `PF_Cmd_SMART_PRE_RENDER`, the effect sees the actual request, parameters, bit depth, GPU framework and device. It sets `PF_RenderOutputFlag_GPU_RENDER_POSSIBLE` only if this particular request can be rendered there.

If feasibility is rejected, AE may ask PreRender again with another GPU or `PF_GPU_Framework_None`. Therefore `effect supports GPU` does not imply `every render request uses GPU`.

`what_gpu` and `device_index` remain consistent between a selected GPU PreRender and `PF_Cmd_SMART_RENDER_GPU`.

## GPU worlds are not CPU pointers
During `PF_Cmd_SMART_RENDER_GPU`, `PF_LayerDef` metadata is populated but `data == NULL`. Pixel storage resides on the device/framework and must be accessed through GPU-device/world mechanisms.

Code that branches only on pixel format and blindly dereferences `data` is architecturally wrong even if its CPU path is correct.

The device setup/render/setdown lifecycle also means compiled kernels, command queues and device allocations must be scoped to the exact device/framework identity rather than treated as one application-global GPU context.

## Host-managed GPU memory is part of the Effect API contract
`PF_GPUDeviceSuite1` is not merely an optional convenience allocator. The public AE 25.6 header states that GPU effects must allocate device memory through the suite and provides paired `AllocateDeviceMemory` / `FreeDeviceMemory` and `AllocateHostMemory` / `FreeHostMemory` entry points. For DirectX, the returned opaque value is an `ID3D12Resource*`; for CUDA it is a device pointer; Metal exposes its own framework object.

This has an architectural consequence for D3D12 backends: an effect-owned `ID3D12Device::CreateCommittedResource` pool is not a drop-in substitute for AE-accounted GPU memory, even if rendering appears to work. A portable design should separate **semantic/schedule identity** from **physical realization** so the same compiled graph can have a standalone/native D3D12 realization and an AE-specific host-managed realization.

A practical AE DirectX realization can use the suite-backed row-pitched linear GPU buffers together with borrowed GPU worlds at the graph boundary. Keep the AE allocator request-scoped or otherwise tied to the exact effect/device lifetime; do not cache a PICA suite pointer as a process-global allocator.

The public header does **not** document the initial D3D12 resource state of the `ID3D12Resource*` returned by `AllocateDeviceMemory`. Do not silently assume `COMMON`, `COPY_DEST`, `UNORDERED_ACCESS`, or another state for a multi-pass intermediate without runtime evidence. If an implementation cannot establish that contract, reject GPU feasibility for that realization and fall back to a proven path rather than issuing an unverified barrier.

This distinction matters especially for multi-pass FFT/convolution/reduction. Single-pass kernels can often operate entirely on borrowed host worlds plus suite-backed upload constants, while multi-pass algorithms require intermediate storage whose state/lifetime contract must be proven separately.

## GPU residency, validity and synchronization
A GPU-resident frame can be semantically valid yet unavailable after device loss/purge, and a resident allocation can be semantically obsolete after upstream state changes. Keep device residency separate from render identity and cache validity.

Local `GPUFoundation::AssetCache` and adapter-budget callbacks indicate that device-memory pressure has its own eviction path. BEE's VRAM-aware scheduling surfaces further suggest resource admission can respond to device budget before work is launched.

## CPU/GPU parity is a semantic test, not a bitwise assumption
Floating-point contraction, transcendental implementations, texture sampling, denormal handling and color-transform backends can create small differences. The correctness question should be specified explicitly: bit-identical, bounded numeric error, or visually/semantically equivalent.

Never weaken an effect's documented semantics simply to make CPU and GPU hashes match.

## Failure modes
- advertise GPU globally and fail only at render time for unsupported parameter combinations instead of clearing request feasibility;
- store one device pointer and reuse it on another device/framework;
- dereference `PF_LayerDef.data` in GPU Smart Render;
- release device resources before `GPU_DEVICE_SETDOWN` or retain them after device teardown;
- assume a GPU dispatch proves correct dependency identity or cache reuse;
- benchmark warm compiled-kernel/device caches against cold CPU startup and call it algorithmic speedup.

## Controlled parity and fallback matrix
Run deterministic fixtures across CPU and every available GPU framework/device while varying bit depth, ROI, downsample, color management, zero-alpha RGB and negative/over-range float values. Record which PreRender requests advertise GPU feasibility, fallback sequence, device index, upload/download events, numeric error and output/cache identities.

Also force low VRAM/budget pressure and device reinitialization to distinguish semantic recomputation from residency loss.

## Unknown frontier
Still unresolved: exact BEE/RG policy for choosing devices and concurrency under VRAM pressure, relation between GPU asset-cache keys and render GUIDs, cross-device reuse policy, device-loss recovery, and which built-in AE effects share the public PF GPU infrastructure versus private renderer-specific paths.

Related: `docs/image-pipeline/pixel-formats.md`, `docs/memory-system/runtime-architecture.md`, `docs/observability/gpu-tracing.md`, `F-GPU-005`.
