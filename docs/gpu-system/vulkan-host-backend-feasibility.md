---
status: research
last_verified: 2026-10-14
evidence: AE 25.6 local distributed headers; Vulkan and NVIDIA external-memory public contracts
---
# Vulkan as an AE Host-Integrated GPU Backend: Feasibility Boundary

## Claim classification
- **Distributed implementation artifact / official SDK surface:** AE 25.6 `AE_Effect.h` defines `PF_GPU_Framework_NONE`, `OPENCL`, `METAL`, `CUDA`, `DIRECTX`; no Vulkan framework enum is exposed. See `Examples/Headers/AE_Effect.h`, around line 2475.
- **Official SDK surface:** `PF_GPUDeviceInfo` provides a framework-specific context, device, and command queue. `PF_GPUDeviceSuite1` states that all device memory must be allocated through the suite. See `Examples/Headers/AE_EffectGPUSuites.h`.
- **Third-party public API contract:** Vulkan supports cross-API memory and semaphore interchange using external-handle extensions; NVIDIA CUDA supports external memory/semaphore import. This does not establish compatibility of **AE-owned** allocations with Vulkan.
- **Hypothesis, not verified:** an AE host-supplied D3D12 allocation may be usable from Vulkan only if exportable handle, allocation/layout compatibility, synchronization and host ownership contracts are established.
- **Boundary:** implementing Vulkan inside a native `.aex` is distinct from registering Vulkan as a first-class AE GPU framework. The latter is not an SDK-exposed extension point in the inspected headers.

## Integration tiers
| Tier | Proposed realization | Contract status | Principal obstacle |
| --- | --- | --- | --- |
| A | AE CPU SmartFX boundary, Vulkan internal compute | feasible in principle, not host-GPU zero-copy | transfers and synchronization |
| B | AE GPU SmartFX through a supported framework, Vulkan internal compute | experiment required | exportability of host memory/world and synchronization |
| C | AE recognizes Vulkan as `what_gpu` with native host allocation, world and queue | not provided by inspected public SDK | host runtime framework negotiation and ownership |
| D | Native supported backend (D3D12/CUDA) with Vulkan-equivalent algorithm and scheduling | SDK-aligned comparison baseline | optimization without unsupported assumptions |

## Hard acceptance gates before claiming tier B
1. Enumerate actual framework/device and retrieve `PF_GPUDeviceInfo`; ensure same physical adapter identity.
2. Identify host GPU world storage type, pixel packing, row pitch and resource ownership using supported APIs, without interpreting opaque pointers as undocumented objects.
3. Establish whether the host allocation can be legally exported/imported by Vulkan; **an ordinary CUDA device pointer is not an external memory handle**.
4. Prove resource state/layout transition, cross-API producer/consumer ordering and completion before host reuse. Host-provided queue ownership must be respected.
5. Verify resource lifetime across PreRender cancellation, Smart Render, device setdown, MFR simultaneous frames, and device loss.
6. Prove that all required device allocations obey the AE suite contract. If not, treat the path as unsupported rather than advertising native host compatibility.
7. Compare outputs against the same native D3D12/CUDA baseline, measuring GPU timestamps, total wall time, transfer bytes, peak VRAM, and synchronization stalls.

## Experiment status and unresolved gates (updated 2026-10-14)
- EXP-GPU-VK-001: SDK compile-time contract atlas for framework enums, GPU suite resource types, render selector and framework negotiation.
- EXP-GPU-VK-002: **COMPLETE for D3D12/Vulkan on RTX 2070 SUPER**, not CUDA. Shared Windows D3D12 resource imports into Vulkan; 1MiB GPU read/write parity in both directions (262144 uint32 samples each), and GPU-only external timeline-fence ordering 3->4. Eight independent full-process runs passed. See F-GPU-015/F-GPU-016 and cross-api-interop-verified-boundaries.md.
- EXP-GPU-VK-003: **DIAGNOSTIC BUILT and MOCK-HOST VERIFIED**, **ACTUAL ADOBE HOST STILL UNKNOWN**. Official GPU Suite interfaces feed a read-only D3D12 shared-handle/export flag inspector. Simulated nonshared Worlds: 0/96 exportable; explicitly shared Worlds: 96/96 exportable; same compiled AEX output parity passes in both. Production AE resources have not been probed. See F-GPU-017.
- EXP-GPU-VK-004: parity and performance matrix of pure D3D12, pure CUDA, CPU SmartFX+Vulkan, and only demonstrated host-safe Vulkan interop.
- EXP-GPU-VK-005: MFR load test with cancellation, multiple simultaneous frame tasks and device recreation.

## Falsification
Tier B fails the supported-contract criterion if AE owns a non-exportable allocation or gives insufficient state/queue synchronization guarantees. Standalone Vulkan/CUDA interoperability success alone cannot promote tier B. Tier C remains unsupported unless the host itself explicitly exposes a documented Vulkan framework registration interface.

## References
- Local SDK 25.6: `Examples/Headers/AE_Effect.h`, `AE_EffectGPUSuites.h`, `Examples/Effect/SDK_Invert_ProcAmp/SDK_Invert_ProcAmp.cpp`
- NVIDIA CUDA Programming Guide: https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/graphics-interop.html
- Vulkan Guide: https://docs.vulkan.org/guide/latest/extensions/external.html
- Related AEIG: [GPU System](overview.md), [MFR](../mfr/overview.md), [MFR State Ownership](../mfr/state-ownership.md)

## 2026-10-14 deeper boundary: headers, GPU world access and host modification

**Local SDK verification:** `AE_Effect.h` exposes the five framework values NONE/OPENCL/METAL/CUDA/DIRECTX. Adding a new enum in a plugin-local header changes compile-time spelling only; it does not cause the host to enumerate, allocate or dispatch a new framework. `AE_EffectGPUSuites.h` provides `GetGPUWorldData`, `GetGPUWorldSize`, `GetGPUWorldDeviceIndex` and `GetDeviceInfo`. A GPU buffer address is **not** necessarily an exportable Win32 shared resource handle.

**D3D12-to-Vulkan path:** Vulkan specifies `VK_EXTERNAL_MEMORY_HANDLE_TYPE_D3D12_RESOURCE_BIT` and `VK_EXTERNAL_SEMAPHORE_HANDLE_TYPE_D3D12_FENCE_BIT`, but successful import requires matching physical adapter, compatible allocation properties, actual shared handle, explicit queue synchronization and host permission/lifetime. `ID3D12Resource*` alone is insufficient; a non-shareable resource cannot be made shareable merely by editing a header.

**Host-internal research frontier (hypotheses only):** locate the runtime device-framework selection, GPU World creation and D3D12 allocation, render queue and frame-cache identity paths using existing AEIG symbol datasets. Distinguish evidence of implementation from supported extension points. Do not claim that binary patching or replacement of AE internals constitutes a supported native SDK backend.

**Decision experiment:** before writing a Vulkan GPU effect, build a read-only diagnostic effect using official GPU suite calls that reports device framework, world metadata, device index and the documented pointer type. Separately validate a standalone D3D12 shared-resource + Vulkan external-memory roundtrip. Compare these two results to determine which missing handle/synchronization contracts require Adobe cooperation or an unsupported host change.

**Primary public references:**
- https://docs.vulkan.org/guide/latest/extensions/external.html
- https://docs.vulkan.org/spec/latest/chapters/memory.html
- https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/graphics-interop.html
