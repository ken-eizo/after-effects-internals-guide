---
status: research-backed-classification; ECW host verification pending
last_verified: 2026-10-16
evidence:
  - E0-G: Adobe Effect UI & Events; PF_ParamDef; PF_EventExtra; Custom UI & Drawbot
  - E0-H: local AE SDK 25.6 AE_EffectUI.h and DrawbotSuite.h
  - E2-L/E2-X: earlier GizmoSearchAE findings (shared Drawbot/host boundary only; not ECW feature validation)
---

# Custom ECW UI — PF_Window_EFFECT and Parameter Controls

## What this subsystem is

The **Effect Controls Window (ECW)** contains an effect's parameters, including custom control areas registered with `PF_PUI_CONTROL` and optionally custom parameter topics registered with `PF_PUI_TOPIC`. The plugin receives effect UI events through `PF_Cmd_EVENT`; it can draw within its **AE-host-owned parameter UI area** during `PF_Event_DRAW` using Drawbot.

**This is NOT the Composition/Layer viewer Gizmo subsystem.** Adobe's Effect SDK distinguishes both UI targets. An ECW custom control is a parameter-facing editor (lens profile, vector curve, gradient, tree/list, node-like editor). A Comp/Layer custom UI is a direct-manipulation overlay on video imagery. Sharing an SDK event and Drawbot does not establish equivalent event delivery, clipping, coordinates, size policy or redraw latency.

## Official SDK distinction

| Contract | ECW custom control (this chapter) | Comp/Layer viewer gizmo (separate chapter) |
| --- | --- | --- |
| Window/context | `PF_Window_EFFECT` | `PF_Window_COMP` / `PF_Window_LAYER` |
| Registration | `PF_OutFlag_CUSTOM_UI`, `PF_REGISTER_UI`; parameter `PF_PUI_CONTROL` or `PF_PUI_TOPIC` | `PF_OutFlag_CUSTOM_UI`, `PF_REGISTER_UI`; Comp/Layer UI registration |
| Event area | `PF_EffectWindowInfo`: `index`, `area`, `current_frame`, `param_title_frame`, `horiz_offset` | Comp/Layer-specific event union payload and frame/source coordinates |
| Visibility | ECW twirl/expand, panel width, parameter topic/control geometry | Viewer/selection/tool/zoom/pan and overlay visibility |
| Editing goal | Widget edits a registered parameter/Arbitrary Data; AE owns Undo and project semantics | Point/Bezier/transform handles over the composited image |
| Display/render | Host-owned Drawbot surface during `PF_Event_DRAW`; image preview may use host Async Manager | Host-owned Drawbot surface during `PF_Event_DRAW`; comp-image render is separate |
| Performance validation | **ECW-specific** layout, font, panel resize, nested widgets, scroll, multiple controls and instances | Viewer-specific drag, pan, zoom, pixel aspect, active tool and pointer tracking |

For every event, identify the documented `PF_Context.w_type` and, for ECW, inspect `PF_EffectWindowInfo.area` to distinguish title (`PF_EA_PARAM_TITLE`) and control (`PF_EA_CONTROL`). Never cast or interpret a Comp/Layer event payload as ECW without checking the context and event type.

## This subsystem's documentation

1. [Cross-platform compatibility and release criteria](cross-platform-compatibility.md): Windows x64 vs macOS Intel/Apple Silicon binaries, ECW event contexts, Drawbot lifetime, font, Retina/HiDPI, serialization, accessibility gaps and proof grades.
2. [Composite widget architecture](composite-widget-architecture.md): reusable widget tree and layout, ECW-specific hit tests, input capture, value commits and Undo, rendering batches, async previews, Arb Data and failure handling.
3. [Performance, load and resilience qualification](performance-and-resilience.md): 12 stress classes, 9 reversible optimization tiers, end-to-end measurements, fallbacks, host UI starvation and eligibility rules for host-verified fast paths.

The ECW qualification matrix (`experiments/ui-effect-controls/qualification-matrix-20261016.tsv`) is maintained outside `docs/`, with separate Windows x64 / macOS Intel / macOS ARM evidence cells. **The matrix is not a record of ECW test completion.** The prior GizmoSearchAE portable 6/6 CTest receipt relates to a shared host-independent model, not ECW widget rendering.

## Shared lower-level documentation (cross-references, not the same feature)

- [Drawbot drawing boundaries and resource lifetime](../drawbot-ui-drawing.md): use DRAW callback and release resources correctly; test ECW behavior independently.
- [Effect custom UI event routing](../effect-custom-ui-input-routing.md): host event semantics; ECW `PF_EffectWindowInfo` overlays additional context.
- [Invalidation and redraw](../effect-custom-ui-invalidation.md): invalidation flags are shared; **dirty regions and scheduling must be verified for ECW specifically**.
- [Host-managed asynchronous custom UI rendering](../async-custom-ui-rendering.md): useful for histogram, thumbnail or preview widgets.
- [Gizmo optimization architecture](../gizmo-adaptive-implementation-architecture.md): shared performance methodology only. Viewer drag benchmarks do **not** certify ECW.
- [Native UI and render-state separation](../view-state-and-render-boundary.md): persistent document values vs view-only state.

Do not move Comp/Layer viewer data or findings into ECW's `ValidatedInHost` status merely because the same Drawbot API appears in both.

## ECW-specific questions still requiring experiments

- Which ECW title/control events are delivered and in what order on current Windows and Mac AE builds?
- What are the actual invalidation clipping and retained-region semantics on folded/unfolded, resized, scrolled and moved ECW controls?
- Which host keyboard input, text/IME, pointer buttons and focus transitions are available inside an ECW custom parameter?
- How do typed AE parameter values, Arbitrary Data values, Undo, expressions, multi-instance and MFR intersect with per-widget transient state?
- How does Drawbot performance scale from few controls to dense nested widgets in ECW, and how does host scheduling affect distinct display updates?

**Status:** the SDK contract and proposed implementation architecture are documented. No multi-widget ECW implementation or Mac AE host performance certification was completed by these documentation edits.

## Primary sources

- Adobe [Effect UI & Events](https://ae-plugins.docsforadobe.dev/effect-ui-events/effect-ui-events/): separates ECW and Comp/Layer custom UI and documents `PF_Context` and `PF_EffectWindowInfo`.
- Adobe [PF_ParamDef](https://ae-plugins.docsforadobe.dev/effect-basics/PF_ParamDef/): `PF_PUI_CONTROL`, `PF_PUI_TOPIC`, Arbitrary Data and parameter UI rules.
- Adobe [Custom UI & Drawbot](https://ae-plugins.docsforadobe.dev/effect-ui-events/custom-ui-and-drawbot/): DRAW-only rendering and Drawbot suites.
- Adobe [What's New — CC 2015 UI/render thread split](https://ae-plugins.docsforadobe.dev/intro/whats-new/): per-thread behavior and host-managed async frame results.
