---
status: active
last_verified: 2026-09-16
---
# AE Editor/View State — Observed UI and Render Synchronization

After Effects UI state is not one state graph. AEIG separates at least **persistent document state**, **render/evaluation state**, **per-view/editor presentation state**, and **transient UI request state**. Bugs often arise when code assumes those layers are synchronously interchangeable.

```text
project/document state -----> evaluation/render identity -----> pixels/results
        |                              |
        |                              +--> host-managed async UI result
        v                                         |
view/editor state --------> UI purpose/current request <-------+
```

## Document state vs view state

Public Guide/ItemView APIs provide a clean example. Guide geometry/color/pinning is attached to document-semantic items/layers, while visibility, snapping and locking are exposed as view behavior. Similar separation applies to zoom, overlays, panel focus, selection and editor presentation: visible UI changes do not automatically imply render invalidation.

For developer tooling this means "the UI changed" is not a sufficient cache key. Ask whether the change modifies persisted project data, render-relevant state, only one view, or only the outstanding request for a preview surface.

## Post-13.5 UI/render synchronization boundary

The 13.5-era architecture explicitly separates UI-side access from authoritative render-side state. `PF_GetCurrentState()` returns randomized state in `PF_Cmd_UPDATE_PARAMS_UI` rather than crossing an unsafe synchronization boundary. That behavior is valuable architectural evidence: a UI callback cannot be modelled as an unrestricted read of the render graph.
## Host-managed asynchronous UI rendering

Custom effect UI can request rendering through a `PF_AsyncManagerP`/AEGP-managed path. A caller-chosen `purpose_id` represents a stable semantic use of the result; when render options change, AE can cancel stale work for that purpose and redraw when the current result becomes available.

This produces a safer model than owning a worker/render lifetime from the panel:

`draw -> request current semantic result -> use cached/blank state -> host renders/cancels -> redraw -> request again`

Receipt availability is multi-state. The HistoGrid sample demonstrates that a receipt can exist while its world is not yet consumable, so "request succeeded" and "pixels are available" must not be collapsed into one boolean.

## UI invalidation is not render invalidation

Trace vocabulary such as `AE.UI_Invalidate` and `AE.UI_Draw` gives observation points for editor activity. It does not prove that a UI invalidation invalidates a render cache, or vice versa. A project edit can invalidate render identity while a view remains unchanged; a zoom/overlay change can redraw a view while final render identity remains stable.

This distinction is especially useful when diagnosing apparent redraw bugs, stale custom controls and expensive refresh loops.

## Failure patterns

- synchronously checking out/rendering pixels from a UI callback that should use the host async path;
- persisting view-only state as project/render state and creating unnecessary invalidation;
- assuming selection/focus/zoom is safe to read from render-thread code;
- retaining receipts, UI-context pointers or public handles beyond their documented lifetime;
- using a task number instead of a semantic `purpose_id`, preventing clean stale-request cancellation;
- treating an unavailable async world as a hard render failure instead of a pending/empty state.
## Extension/panel plane

CEP/UXP panel technology is a separate layer from the underlying AE operation. CEP crosses from web/native contexts into ExtendScript; first-party UXP runtime presence does not by itself establish a third-party AE Host DOM. Keep UI technology, transport and AE state mutation as separable layers so an operation can move between panel technologies without changing its semantic contract.

## Experiments and observability

Useful controlled tests vary one axis at a time: project property vs view visibility, selection vs render state, zoom/overlay vs output hash, rapid async-purpose changes, panel closure while work is pending, and undo/redo while UI caches are populated. Correlate UI traces with render/BEE/RG traces rather than inferring causality from timing alone.

## Open boundaries

Exact ownership of many editor caches, selection models and internal panel objects remains private. The evidence is strongest at public API boundaries and trace vocabulary. AEIG therefore models the synchronization/invalidation rules that developers can rely on without pretending to reconstruct every private widget class.

Related pages:

- `docs/ui-system/view-state-and-render-boundary.md`
- `docs/ui-system/async-custom-ui-rendering.md`
- `docs/capability-recipes/cep-vs-uxp-extension-plane.md`
- `docs/threading-system/overview.md`

A useful implementation rule is: **for every visible UI property, identify separately what is persisted, what affects render identity, what belongs only to a view, and who owns cancellation/lifetime of any asynchronous result.**
