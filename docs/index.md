---
status: active
last_verified: 2026-10-14
evidence: public Adobe SDK Guide + SDK25.6 headers + AEIG native research
---

# After Effects Internals Guide

AEIG is an **unofficial technical companion to the [After Effects C++ SDK Guide](https://ae-plugins.docsforadobe.dev/)**. It preserves the SDK's familiar module, type, suite and function terminology while documenting the implementation boundaries **behind** public APIs: host-owned property systems, native evaluation, rendering, storage, cache, media, memory, UI and more.

It is organized as a technical encyclopedia, not a timeline of research activity. Every subsystem has its own section and pages, with reproducible evidence kept separately from normative guidance.

**Naming contract:** navigate by the actual Adobe SDK feature and **host context**, not merely a shared drawing/renderer API. Adobe calls the two Effect Custom UI purposes **Custom ECW UI** (Effect Controls Window, `PF_Window_EFFECT`) and **Custom Comp UI** (Composition/Layer Windows, `PF_Window_COMP` / `PF_Window_LAYER`). Both may use Drawbot, but they are distinct interfaces. Public AEGP suites are likewise separate from the observed internal TDB/BEE stream implementation. See [Official SDK names, host ownership and terminology](foundations/sdk-nomenclature-and-context.md) and the [whole-site taxonomy audit](reference/sdk-taxonomy-coverage.md).

## Start with an SDK feature

The primary navigation follows the official SDK Guide's main chapters. If you already know Adobe's public API categories, begin with the corresponding AEIG topic:

| SDK area | AEIG documentation | Main subject |
| --- | --- | --- |
| Introduction | [SDK architecture and compatibility](host-integration/cpp-sdk/index.md) | Supported extensions, ABI and versions |
| Effect Basics | [Effect Basics](host-integration/cpp-sdk/effect-basics/index.md) | PF entrypoint, commands, parameters |
| Effect Details | [Effect Details](host-integration/cpp-sdk/effect-details/index.md) | Suites, memory, value and render contracts |
| SmartFX | [SmartFX](host-integration/cpp-sdk/smartfx/index.md) | ROI, 32-bit float and render execution |
| Effect UI & Events | [Effect UI](host-integration/cpp-sdk/effect-ui-events/index.md) | Drawbot, custom UI, input/event routing |
| Audio | [Audio](host-integration/cpp-sdk/audio/index.md) | Host audio data and runtime |
| AEGPs | [AEGP API](host-integration/cpp-sdk/aegps/index.md) | Streams, dynamic groups, keyframes, registrations |
| Artisans | [Artisans](host-integration/cpp-sdk/artisans/index.md) | Native 3D renderer extension |
| AEIOs | [AEIOs](host-integration/cpp-sdk/aeios/index.md) | Native file import/export |
| Premiere Pro | [Other hosts](host-integration/cpp-sdk/premiere-other-hosts/index.md) | Shared effect ABI and host differences |

### Public AEGP type references

- [`AEGP_StreamSuite6`](host-integration/cpp-sdk/aegps/stream-suite.md)
- [`AEGP_DynamicStreamSuite4`](host-integration/cpp-sdk/aegps/dynamic-stream-suite.md)
- [`AEGP_KeyframeSuite5`](host-integration/cpp-sdk/aegps/keyframe-suite.md)
- [`AEGP_RegisterSuite5`](host-integration/cpp-sdk/aegps/register-suite.md)

## Inside After Effects

Where the official SDK stops at supported interfaces, AEIG follows the actual implementation **without presenting private C++ symbols as public contracts**.

The first complete feature-specific reconstruction is the [Native Property System](state-model/native-property-system/index.md), covering the following separately documented concerns:

- [Startup, type registration and shutdown](state-model/native-property-system/startup-to-shutdown.md)
- [Native `TDB_StreamBase`, Group and value model](state-model/native-property-system/stream-object-model.md)
- [`TDB_StreamFactory` and object lifetime](state-model/native-property-system/factory-registration-lifetime.md)
- [Canonical UILayout and child admission](state-model/native-property-system/canonical-groups-admission.md)
- [Paint, Text Animator and Shape Contents](state-model/native-property-system/paint-text-shape-hierarchies.md)
- [Native property operations](state-model/native-property-system/property-operations.md)
- [Layer ownership, Timeline editor and renderer](state-model/native-property-system/owner-editor-renderer.md)
- [Public and internal API atlas](state-model/native-property-system/api-atlas.md)
- [Verification and version matrix](state-model/native-property-system/verification-and-version-matrix.md)

Additional sections independently cover render graphs, GPU, cache, media, persistence, expressions, UI and native animation.

## Evidence and uncertainty

The documentation distinguishes **official SDK contracts** (E0-G/H/S), **installed Adobe binary observations** (E2-L), **controlled host experiments** (E2-X) and **unproven hypotheses** (H). See [Evidence Model](foundations/evidence-model.md) for the formal rules.

AEIG does not claim access to Adobe's private source. A native symbol found in an export table is not a supported third-party API, and a separately implemented typed timeline is not the standard AE Timeline. Every internal finding is tied to version-scoped evidence.

## Research is a separate resource

Individual research reports, scripts, test receipts, uncertain hypotheses and release qualification live under the **Research & Evidence** and **Reference** sections, rather than interrupting feature documentation. The full unedited experimental record is preserved in the repository's `research/`, `experiments/` and `datasets/` directories.

To regenerate the feature-organized navigation, run `python probes/process-tools/generate_site_config.py`. Use `mkdocs build --strict` to verify the published guide.

This project is unofficial and is not affiliated with or endorsed by Adobe.
