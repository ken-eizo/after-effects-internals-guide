---
status: editorial contract; public API names checked against Adobe SDK Guide
last_verified: 2026-10-16
evidence: E0-G official Guide; E0-H SDK25.6 headers; E2-L version-scoped native symbols
---

# AEIG Nomenclature — Official API, UI Purpose, Host Context and Private Runtime

## Naming policy

AEIG classifies by **functional purpose, host ownership, SDK context and evidence provenance**. An API shared by multiple features is NOT a feature category. Official Adobe SDK terms are used when published; a private symbol recovered from an installed binary is always labeled *Observed Native Implementation (Private)*, and an invented architecture description is labeled *AEIG research model*, never presented as an Adobe product/API name.

Canonical page identity: (1) official public API family or user-facing purpose, (2) exact suite, selector or `PF_Window_*` context, (3) public/private/research classification, and (4) evidence and supported-version scope.

## Official names and distinct application

| Adobe SDK purpose / API | Identifying boundary | NOT equivalent to |
| --- | --- | --- |
| **Custom ECW UI** | `PF_Window_EFFECT`, `PF_PUI_CONTROL`, `PF_PUI_TOPIC` and `PF_Cmd_EVENT` | Custom Comp UI, a new native property Stream provider |
| **Custom Comp UI** | `PF_Window_COMP` or `PF_Window_LAYER` and `PF_Cmd_EVENT` | Effect Controls Window parameter widgets |
| **Drawbot** | `PF_EffectCustomUISuite1` and DRAWBOT Drawbot/Supplier/Surface/Path suites | A separately owned panel, UI context or rendering scheduler |
| **UI Callbacks / PF_EventExtra** | Context-specific event payloads, `PF_InvalidateRect` | Guaranteed UI presentation cadence or pixel-frame render |
| **Effect Preview Media (Effects Panel)** | **Premiere Pro Beta 27.0+ only** in the Adobe Guide (August 19, 2026); explicitly **not available in After Effects** | Effect Controls Window / Custom ECW UI |
| **AEGP Suites** | `AEGP_StreamSuite6`, `AEGP_DynamicStreamSuite4`, `AEGP_KeyframeSuite5` | Private `TDB_StreamFactory` class registration |
| **Observed TDB/BEE implementation** | `TDB_StreamBase`, `TDB_StreamFactory`, `BEE_*` internal symbols | Public AEGP API |
| **SmartFX / GPU Effect Rendering** | `PF_Cmd_SMART_PRE_RENDER`, `PF_Cmd_SMART_RENDER_GPU`, `PF_GPUDeviceSuite1` | GPU direct drawing inside Effect Controls |
| **Multi-Frame Rendering** | `PF_OutFlag2_SUPPORTS_THREADED_RENDERING` and render-selector state | Concurrent mutation of UI drag state |
| **CEP panels / ExtendScript** | HTML/JavaScript extension host bridge and scripting APIs | Native PF Effect Custom UI |
| **UXP runtime observation** | Version-scoped observed runtime only | Automatically supported public AE UXP host extension API |
| **Artisans** | Adobe Artisan interface | Effect parameter controls |
| **AEIOs** | AEIO import/export SDK | Layer rendering UI |

The **Effect Controls Window** phrase itself is used by Adobe's Guide, but it is a *window name*. The professional name of the feature being implemented is **Custom ECW UI**. The separate video manipulation feature is **Custom Comp UI**. The popular shorthand *Gizmo* may be retained as explanatory language, never as an owner or SDK feature name.

## Provenance tags for the entire encyclopedia

- **`official`** — an Adobe Guide/header-defined feature, suite, enum, selector or public extension contract. This is a *name origin*, not proof that every benchmark on the page passed.
- **`observed`** — an actual installed native symbol, first-party internal subsystem or host behavior established by version-scoped evidence. Do not imply an Adobe-supported third-party ABI.
- **`research`** — an AEIG analytical grouping or architectural hypothesis. Name it as such; identify the falsifiable assumption.

Individual claims still require AEIG's `E0-G/E0-H/E2-L/E2-X/H` evidence grades. A header name, a binary export and a measured host capability are not interchangeable sources.

## Frequent false equivalences to prevent

1. **Custom ECW UI vs Custom Comp UI.** Both may use `PF_Cmd_EVENT` and Drawbot; their UI contexts, registration, geometry and host delivery must be tested separately.
2. **Effects Panel vs Effect Controls Window.** Adobe describes Effect Preview Media (Effects Panel) independently and currently **limits that new feature to Premiere Pro Beta 27.0+** (not After Effects); do not treat the Guide navigation's Effect Details category as proof the feature is available in AE.
3. **Public AEGP Stream Suite vs private TDB/BEE.** The public suite can access supported existing property streams; it does not automatically authorize registration of new host-native C++ stream classes.
4. **Drawbot vs a widget framework.** Drawbot draws paths/text/images but supplies neither a complete independent widget tree nor ownership of a standalone native window.
5. **SmartFX GPU renderer vs UI rendering.** GPU render-world lifetimes and image-processing selectors do not grant ownership of Drawbot's display surface.
6. **CEP, UXP, AEGP Panels, PF Custom UI.** Different entry points and supported lifecycle contracts. Runtime presence is not a public plug-in API.
7. **FLT/PIN private module operations vs PF SDK.** `FLT_FCSpec` and `PIN_LockDownModules` are observed private host symbols, not public Effect SDK selectors.

## Classification in AEIG

The site navigation is generated from `probes/process-tools/sdk_taxonomy.py` via `probes/process-tools/generate_site_config.py`. The classifier assigns **one owner/context and one public/private/research classification** to each Markdown page.

An auditable per-page inventory and its static checks are generated with `probes/process-tools/audit_sdk_taxonomy.py`. New pages which have no recognized owner must fail classification rather than silently being placed under a generic Drawbot/Gizmo/GPU bucket. Internal section names are explicitly prefixed *Observed* or *AEIG Research*, because no single official SDK category exists for all private renderer or property subsystems.

## Primary Adobe references

- [Effect UI & Events](https://ae-plugins.docsforadobe.dev/effect-ui-events/effect-ui-events/)
- [PF_EventExtra](https://ae-plugins.docsforadobe.dev/effect-ui-events/PF_EventExtra/)
- [Custom UI & Drawbot](https://ae-plugins.docsforadobe.dev/effect-ui-events/custom-ui-and-drawbot/)
- [Effect Preview Media (Effects Panel)](https://ae-plugins.docsforadobe.dev/effect-details/effect-preview-media/)
- [AEGP Suites](https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/)
- [SmartFX](https://ae-plugins.docsforadobe.dev/smartfx/smartfx/)
- [Multi-Frame Rendering in AE](https://ae-plugins.docsforadobe.dev/effect-details/multi-frame-rendering-in-ae/)
