---
status: reproduced-local-windows-portable; macOS/AE-host-not-tested
last_verified: 2026-10-16
evidence_grade: E2-X (host-independent tests only); E0-G for SDK premises
scope: GizmoSearchAE portable model, Windows x64 MSVC Release
---

# 2026-10-16 — Effect Custom UI cross-platform core: local Windows receipt

## Purpose

AEIGの新しい複合ECWウィジェット・Windows/macOS認定文書を記述する際、既存のGizmoSearchAEの「共通CPUコアがWindowsでビルドでき、host-independent testsを通過する」という根拠を**同日再現**する。実際のAfter Effectsプラグイン、ECW上の多widget Drawbot、Mac版のロード、物理画面遅延を証明しない。

## Source and test commands

- Source: `D:\Developer\GizmoSearchAE\portable\CMakeLists.txt`
- Build directory: `D:\Developer\GizmoSearchAE\scratch\aeig-ui-portable-20261016`（既存ソースを変更せず別ディレクトリ生成）
- CMake generator: Visual Studio 17 2022
- C++ compiler: MSVC 19.44.35215.0
- Windows SDK selected: 10.0.26100.0
- CMake test config: Release

```powershell
cmake -S "D:\Developer\GizmoSearchAE\portable" -B "D:\Developer\GizmoSearchAE\scratch\aeig-ui-portable-20261016"
cmake --build "D:\Developer\GizmoSearchAE\scratch\aeig-ui-portable-20261016" --config Release --parallel 4
ctest --test-dir "D:\Developer\GizmoSearchAE\scratch\aeig-ui-portable-20261016" -C Release --output-on-failure
```

## Observed result

| Test | Outcome |
| --- | --- |
| GizmoImplementationSelectionTests | Passed |
| GizmoCoreTests | Passed |
| GizmoPropertyTests | Passed |
| GizmoPixelTransferTests | Passed |
| GizmoRedrawSuppressionBench | Passed |
| GizmoPlatformClockTests | Passed |

CTest summary: **6/6 passed, 0 failed; reported total 0.32s**. This is the test-run duration, **not** an After Effects redraw, click-to-photon or GPU render benchmark.

## Claims supported and unsupported

**Supported within this fixture:** C++ source compiled in MSVC Release for the chosen target; the six registered tests completed without failures. The tests include host-independent implementation selection, model, property checks, pixel transfer, redraw suppression and clock.

**Not supported:** Mac `x86_64` or `arm64` native execution, Universal `.plugin` packaging, PiPL/loader, Mac Retina/Drawbot drawing, AE event delivery, 1000-widget ECW stress, MFR+Drawbot concurrency under actual AE, sustained input-to-display p99, fault recovery under memory pressure.

## Admission/falsification

Do not promote this fixture to `ValidatedInHost`. Run the new platform and stress qualification documents' AE-host tests separately; Mac requires a Mac with a supported AE version and Instruments. For one missing `PF_Cmd_EVENT` or load failure, the corresponding host gate remains `unknown/rejected`, independent of this green pure-unit suite.

## Related AEIG chapters

- `docs/ui-system/gizmo-cross-platform-release-contract.md`
- `docs/ui-system/gizmo-composite-widget-framework.md`
- `docs/ui-system/gizmo-adversarial-performance-qualification.md`
- `research/findings/F-UI-025-cross-platform-gizmo-performance-qualification.md`
