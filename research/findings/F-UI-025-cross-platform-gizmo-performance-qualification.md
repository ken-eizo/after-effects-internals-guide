---
status: platform-core-validated-on-windows; macOS host pending
last_verified: 2026-10-14
evidence_grade: E0-G/E0-H on platform API; E2-X Windows Release core tests; H on macOS behavior
scope: GizmoSearchAE AE Effect Custom UI, Windows x64 and macOS Intel/Apple Silicon
confidence: high for contract separation, local tests; no Mac runtime claim
---

# F-UI-025 — Cross-platform gizmo core, platform-qualified backend fingerprints

## Claim and constraints

A common Adobe SDK declaration does not imply a common OS loader, GPU API,
physical display refresh schedule, memory layout or per-host performance.
Native Gizmo selection requires **Windows/macOS + CPU architecture +
fixed/variable refresh + memory topology + view scaling/monitor** in its
environment fingerprint, in addition to AE version, driver, workload and
pixel depth.

Mac Apple Silicon unified memory is NOT an NVIDIA-style separate VRAM pool.
Display policies on multi-monitor and dynamic refresh systems must be
measured, not inferred from one nominal Hz value. Win32 screen pointer
mapping cannot be reused on Cocoa/Retina without controlled validation.

## Sources

- Adobe official Mac ARM64/Intel Universal PiPL:
  https://ae-plugins.docsforadobe.dev/intro/apple-silicon-support/
- Adobe Drawbot compositing/drawing callback:
  https://ae-plugins.docsforadobe.dev/effect-ui-events/custom-ui-and-drawbot/
- Adobe Multi-Frame Rendering:
  https://ae-plugins.docsforadobe.dev/effect-details/multi-frame-rendering-in-ae/
- Apple Instruments System Load/Thread State/GPU/Display:
  https://developer.apple.com/documentation/xcode/analyzing-the-performance-of-your-metal-app/
- AEIG corpus: docs/host-integration/cpp-sdk/platform-header-parity.md
  (AE 25.6 normalized 68 public header matches; not runtime parity)

## Locally executable implementation and tests

- `GizmoSearchAE/ae_plugin/GizmoMeasuredBackendSelector.hpp`
  adds `OperatingSystem`, `CpuArchitecture`, `RefreshBehavior`,
  `MemoryTopology`, `display_scale_milli`, `display_identity` and
  requires complete non-unknown fingerprints for measured candidate selection.
- `GizmoSearchAE/ae_plugin/GizmoImplementationSelectionTests.cpp`
  includes synthetic macOS ARM64/unified/variable-refresh cases as well
  as Windows x64/discrete/fixed-refresh cases. Mac and Windows evidence
  cannot be interchanged even when timing numbers are identical.
- `GizmoSearchAE/portable/CMakeLists.txt`: independent standard C++20
  build, no Adobe SDK, no windows.h; Windows x64 Release build and portable
  CTest **6/6 passed**, including the platform monotonic clock test.
  Mac native build not yet executed.
- The GPU selector verifies that Windows does not select Metal and that
  macOS does not select Windows DirectX/CUDA paths. VerifiedInHost
  evidence must also match the current host before enabling GPU, MFR or
  pixel-independent optimization. These are policy tests, not Mac host data.
- `GizmoSearchAE/ae_plugin/GizmoPlatformClock.hpp`:
  QPC on Windows; monotonic nanosecond clock on macOS; no clock-domain
  arithmetic across platforms. Windows AEX builds pass; Mac compile awaits Xcode.
- `GizmoSearchAE/portable/validate_macos.sh` and
  `capture_gizmo_macos.sh` are handoff scripts, not Mac-executed evidence.

## Discovery during test hardening

The earlier `GizmoImplementationSelectionTests.cpp` used assertions
that were disabled by MSVC Release `NDEBUG`.
The file now explicitly undefines NDEBUG **before** including cassert.
After that, a stale synthetic test-state reset was found and fixed;
all expected assertions actually ran in Release and passed.
This changes the validity of the test evidence, not AE UI timing.

## Contradictions and unknown frontier

- No Mac device/AE/Xcode execution was accessible in this session.
  Universal .plugin packaging, signing, Mac Drawbot event delivery,
  Retina coordinate parity, Instruments data and high-refresh presentation
  are **not yet host-verified**.
- The existing `GizmoInputProbe.cpp` still contains Win32-only APIs,
  Windows RC PiPL and Windows test-only telemetry. A common C++ core
  is **not** a completed Mac effect port.
- Apple Metal / Windows D3D12/CUDA GPU effect renderers are separate
  from the host's Drawbot Custom UI; no GPU API is proven globally optimal.
- A 10us pure model/selection benchmark cannot promise 10us of
  AE host dispatch, OS compositor and monitor photons.

## Reproduce and disprove

Windows:
`cmake -S GizmoSearchAE/portable -B <builddir>`
`cmake --build <builddir> --config Release`
`ctest --test-dir <builddir> -C Release --output-on-failure`

Mac:
`bash GizmoSearchAE/portable/validate_macos.sh`
`bash GizmoSearchAE/portable/capture_gizmo_macos.sh <AE_PID>`
(no claim that these have been run on a Mac).

Disprove current candidate rankings with a controlled A/B/A that
causes even one visual mismatch, crash, ABI or ownership violation,
or p99/deadline/resource regression at the claimed device key.

## Guide pages

- docs/ui-system/gizmo-cross-platform-contracts.md
- docs/ui-system/gizmo-cross-platform-profiling.md
- docs/ui-system/gizmo-macos-porting-certification.md
- docs/ui-system/gizmo-adaptive-implementation-architecture.md
