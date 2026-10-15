---
status: active
last_verified: 2026-09-15
---
# Subsystem Boundaries

AEIG treats After Effects as cooperating subsystems rather than one renderer with incidental utilities.

## Strongly evidenced boundaries
- **TDB**: persistent/evaluated stream and property state; stream GUID/time-mixing surfaces.
- **BEE**: layer/item evaluation, render options/GUID formation, work queues, media bridges, text/vector/3D evaluated state.
- **RG**: pre-render traversal, cache-node validation and render-graph execution.
- **PF/FLT**: effect plug-in hosting and effect-node projection into RG.
- **MediaFoundation / ImporterHost / VideoFrame**: source import, decode scheduling, frame residency and PF_World/PPix bridging.
- **GPUFoundation / PF GPU bridge**: device selection, GPU worlds/frame transfer and GPU execution support.
- **TXT / AGM**: text semantic state/glyph rendering and vector rasterization/materialization.
- **dvacore diagnostics**: Debug/Trace configuration and cross-product infrastructure.

## Native lifecycle is stage-based, not derived from import-order adjacency

For Windows AE2025/2026, the first-party `aelib.dll` lifecycle state machine initializes its property-related subsystems in ascending numbered stages **TDB 15 → OM 25 → FLT 27 → BEE 29**, and executes the corresponding normal native teardown in descending order. AEGP/general plugin setdown occurs at a separate **stage 32** before BEE's stage 29 in reverse termination. These claims are original compiled stage-dispatch observations (F-VECTOR-106), **not evidence that all external plugin DLLs are physically unloaded at that stage**. See [aelib Native Module Lifecycle](native-module-startup-shutdown.md).

## Scheduling is also layered
Trace/runtime vocabulary separates `BEE_WorkQueue`, `RenderTaskManager`, `RenderThreadExecutor`, media async executors and GPU submission. AEIG therefore avoids a single global-scheduler model.

## Boundary rule
An import/export edge establishes architectural adjacency, not object ownership or call order. For example, BEE imports RG and TDB surfaces, but that does not mean every BEE object owns an RG node or every TDB stream becomes a graph node.

Likewise, public PF/AEGP contracts are observation/integration surfaces around these internals; they should not be mapped 1:1 onto private classes without experiment.

## Practical benefit
Subsystem boundaries tell plug-in authors where a limitation actually lives: persistent state, dependency registration, render-request identity, graph execution, media decode, GPU transfer, extension/UI hosting or cache residency. Choosing the wrong boundary leads to brittle workarounds.

Machine evidence is distributed across the runtime export/import datasets and domain-specific symbol inventories.

## Boundary crossings transform representation
A subsystem boundary is most useful when it explains **what changes representation**. Examples supported by current evidence include:

- persistent project/property state -> evaluated stream values and render-relevant GUID mix-ins;
- BEE render options/identity -> RG request/node planning;
- PF layer/effect state -> FLT/effect-node checkout projected into RG;
- media `ContentState`/decode request -> host frame/PF-world representation;
- PF CPU world -> shared video-frame/GPU-resident world;
- TXT document/font/layout state -> text render GUID -> BEE layer identity;
- project/view state -> preview request/display transformation rather than final project pixels.

The representation on each side can have different identity and lifetime even when it refers to the same user-visible layer or frame.

## Public API boundary versus implementation boundary
AEGP/PF/AEIO/CEP/Scripting APIs are integration contracts. They may aggregate several private modules or intentionally hide them. Conversely, one private module can support several public APIs.

Therefore an API-to-DLL table is a research index, not an ownership proof. Ownership requires stronger evidence such as import/export edges, call stacks, traces, controlled toggles or public lifecycle semantics.

## Version boundary is part of subsystem boundary
Subsystem boundaries move. 13.5 split UI/editable project state from render-local project copies; MFR changed render-time sequence ownership; modern MediaCore/GPU infrastructure sits underneath legacy AEIO/PF surfaces; 26.5 adds new guide/stage APIs above existing project/render machinery.

AEIG should record both the invariant semantic role and the version-specific implementation surface.

## Failure patterns
- assign a capability to the DLL whose filename sounds closest -> false ownership;
- serialize a host handle across a boundary that only promises semantic identity -> stale pointer/reference;
- treat media source identity as render-layer identity -> wrong cache invalidation;
- treat GPU residency as pixel validity -> stale or prematurely purged resources;
- use UI/view state to explain final-render differences without proving it enters render context;
- infer call order from import direction alone.

## Boundary-mapping experiment
For one user action, capture four synchronized views: project/AEP diff, module/call/trace activity, render identity/receipt changes, and output pixels. Repeat with a mutation deliberately confined to one state class such as view-only, media-content, property value, stage/topology or GPU device.

The goal is a **boundary transition table**: which semantic event crosses which subsystem edge, what representation/identity is produced, and which downstream domains invalidate.

## Unknown frontier
Still unresolved: exact TDB↔BEE ownership split, graph-construction ownership between BEE/RG, adapter classes bridging MediaFoundation frames to PF worlds, TXT/AGM responsibility for final shape/text rasterization, and which dvacore services are cross-product infrastructure versus AE-owned policy.

Related: `docs/architecture/system-overview.md`, `docs/state-model/object-identity.md`, `docs/render-graph/render-nodes.md`, `docs/media-system/runtime-architecture.md`.
