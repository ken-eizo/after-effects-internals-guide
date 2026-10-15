---
status: index
last_verified: 2026-09-14
---
# Effect UI & Events — Custom ECW UI, Custom Comp UI and Drawbot

Mirror the public surface for navigation, then link each contract inward to the internal subsystem pages. This section is intentionally surface-oriented and should not become the primary architecture taxonomy.

## Effect Controls Window custom UI (ECW) — separate from Comp/Layer Gizmos

[ECW Custom UI overview](../../../ui-system/effect-controls-custom-ui/index.md) — PF_Window_EFFECT and PF_PUI_CONTROL / PF_PUI_TOPIC; this is not the Comp/Layer viewer overlay subsystem.

### ECW implementation architecture

- [Windows/macOS compatibility and release gates](../../../ui-system/effect-controls-custom-ui/cross-platform-compatibility.md) — universal binary, loader, host Drawbot, DPI, text, gestures, project persistence and per-platform qualification.
- [Composite widget framework contract](../../../ui-system/effect-controls-custom-ui/composite-widget-architecture.md) — reusable widget tree, hit-testing, capture/focus, layout, Drawbot rendering, arbitrary data, Undo and async previews.
- [Adversarial performance qualification](../../../ui-system/effect-controls-custom-ui/performance-and-resilience.md) — CPU/GPU/host scheduler/memory stress conditions, reversible optimization tiers, latency measurement and fail-closed release criteria.

These are evidence-graded engineering contracts and research protocols; they do not claim an already-shipped macOS effect or a measured universal performance guarantee.
