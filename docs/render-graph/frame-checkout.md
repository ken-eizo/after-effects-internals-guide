---
status: active
last_verified: 2026-09-16
evidence: current SmartFX contract + Render Suite lineage + local CheckoutItemFrameAsync/RG trace vocabulary
---
# Frame Checkout and Dependency Materialization

A frame checkout is not just "get me pixels". In AE it is simultaneously a dependency declaration, a request identity/lifetime boundary, and eventually a pixel-materialization operation.

SmartFX exposes the split most clearly:

```text
PF_Cmd_SMART_PRE_RENDER
    -> describe requested input region/state
    -> checkout_layer(..., checkout_id)
    -> receive bounds / dependency result

PF_Cmd_SMART_RENDER
    -> checkout_layer_pixels(checkout_id)
    -> consume materialized input world
    -> checkout output late
    -> render
```

This is a public analogue of the internal distinction between pre-render graph construction/dependency planning and RG execution/materialization.
## Checkout-ID contract

The SmartFX `checkout_id` is chosen by the effect and must be unique within the request. Adobe's current SDK Guide says the ID must be **positive**, while the AE 25.6 public header comment says **`>= 0`**. Portable plug-ins should therefore prefer positive IDs and record the version/source distinction rather than assuming that zero is uniformly forbidden by every published contract.

`checkout_layer_pixels()` may be called at most once for a checkout ID that was declared during PreRender. If the effect needs independently materialized pixels from the same layer more than once, it must issue separate PreRender checkouts with different IDs. The converse is intentionally weaker: a PreRender checkout does **not** have to be materialized later. Adobe explicitly documents that an input checked out during PreRender may go unused in SmartRender and then need never be rendered.

This matters for bounds-first planning. Adobe's SmartFX Guide explicitly permits `checkout_layer` with an empty request rectangle to obtain `ref_width` / `ref_height` and `max_result_rect` without rendering pixels, so an effect may use one request-local ID for a bounds/dependency probe and a different ID for the later pixel ROI derived from that geometry. The checkout ID is therefore best understood as a request-local dependency/materialization slot, not a persistent layer handle.

`checkout_layer_pixels()` returns a world valid for the current command or until checked in. Explicit `checkin_layer_pixels()` is optional for correctness because AE cleans up when SmartRender returns, but early checkin can reduce peak memory.

Adobe also recommends checking out the output as late as possible and keeping as few inputs checked out simultaneously as practical. This is a direct memory-pressure optimization, not merely style.
## Render-request semantics

`PF_RenderRequest` is a semantic request object: layer-space rectangle, field, channel mask and zero-alpha-RGB preservation policy all participate in what must be produced. Reserved/unused fields must remain zeroed; initialize the whole struct before setting fields.

The zero-alpha flag is especially important. `preserve_rgb_of_zero_alpha` requires transparent-pixel RGB to survive the operation, while `PF_OutFlag2_REVEALS_ZERO_ALPHA` describes a different property: whether an effect may later make hidden RGB visible by raising alpha.

PreRender is not guaranteed to imply a matching SmartRender. Host planning can be cancelled or superseded. Therefore `pre_render_data` becomes host-owned after PreRender returns and must have a valid destruction path independent of SmartRender execution.

When MediaCore hosts an effect, Smart PreRender may be invoked more than once while source dimensions/dependencies are discovered. Code that assumes one planning callback per final render is therefore brittle.

## Runtime/internal correlation

Local traces expose `CheckoutItemFrameAsync` and `StaticCheckoutItemFrameAsync`, while RG exposes pre-render/cache-node execution and BEE carries render options/GUID state. These names support a broader architecture in which checkout edges are planned from semantic request state and materialized asynchronously by downstream execution queues.

They do **not** prove that SmartFX checkout IDs map one-to-one to internal RG nodes or work items.
## Failure patterns and experiments

Common errors are reusing a checkout ID for two logical dependencies, retaining a world past its command lifetime, checking out output too early and inflating peak memory, deriving bounds from final pixels instead of PreRender dependency semantics, or assuming PreRender always leads to SmartRender.

For reconstruction, log requested time/rect/channel mask, checkout ID, returned bounds, materialization time, thread ID and receipt/GUID state. Vary only ROI, time, bit depth, GPU choice, zero-alpha preservation or upstream state and observe which checkout edge/receipt changes.

Useful falsification questions:
- Can two equal semantic requests receive different checkout scheduling but the same result identity?
- Does an ROI-only change alter graph/cache placement without changing upstream source identity?
- Can a dependency be planned and then cancelled without pixel materialization?
- Which checkout paths become asynchronous under UI preview versus final render?

Cross-links: `render-context.md`, `render-tasks.md`, `render-graph-model.md`, `../image-pipeline/alpha-zero-rgb.md`, `../cache-system/state-identity.md`, and the SmartFX/Render Suite surfaces in the API atlas.

## Version boundary
Classic Effect API rendering predates SmartFX, but SmartFX makes planning/materialization separation explicit through PreRender and SmartRender. MediaCore hosting can issue multiple PreRender passes while dimensions/dependencies are discovered, so behavior observed in one host/version should not be projected onto every rendering path.

The async AEGP Render Suite introduced in the 13.5 architecture era adds a separate managed checkout lifetime for UI consumers. Similar words such as checkout are used across subsystems, but SmartFX checkout IDs, AEGP async request IDs, frame receipts and internal BEE/RG checkout objects are not assumed interchangeable.

## Reproduction harness
Build one SmartFX effect that logs every PreRender checkout ID, requested rectangle, time, field/channel policy, returned result/bounds, SmartRender materialization and checkin. Run deterministic cases where only ROI, time or zero-alpha preservation differs.

Repeat after cancellation/supersession and under memory pressure to observe whether planned dependencies are abandoned without materialization and whether earlier checkin reduces peak resident memory.

For host-emulator testing, deliberately violate one rule at a time: duplicate checkout ID, retain a world after command return, mutate reserved request fields, or alias request state across concurrent renders. A correct compatibility layer should reject or safely isolate these cases rather than fabricate success.

## Unknown frontier
Unresolved: exact mapping from public checkout slots to internal RG dependency edges; whether repeated equivalent checkouts are canonicalized before graph execution; internal cancellation propagation after PreRender; relationship between checkout result receipts and BEE Render GUID/RG cache-node identity; backend-specific materialization rules for GPU-resident worlds.

Related: `docs/render-graph/render-context.md`, `docs/render-graph/render-tasks.md`, `docs/render-graph/render-request-sufficiency.md`, `docs/cache-system/state-identity.md`, `docs/image-pipeline/alpha-zero-rgb.md`.
