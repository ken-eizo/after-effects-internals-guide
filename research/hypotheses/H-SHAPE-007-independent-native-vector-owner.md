---
status: unresolved
last_verified: 2026-10-12
evidence: E2-L + H
---

# H-SHAPE-007 — A third-party native vector owner can join AE's TDB/BEE Layer + renderer ecosystem

## Claim to test (NOT established)

A plug-in might be able to register an additional native TDB stream Creator and BEE vector evaluator, then expose a persistent independent host-owned Contents tree, route native Pen/Selection editing to those streams and supply its own BEE_VectorArt through a registered native Layer renderer. This would be an AE feature beyond ordinary Effect SDK render callbacks and would meet the central independent native vector-object ambition only if all pieces work.

## Strong existing evidence

- Adobe's own native layer Creators use a common TDB factory callback form and construct BEE_VectorLayer, whose GetLayerType is 4 and GetDefaultTypeMagic is 0x05192004 (AE2025 and 2026).
- A separate BEE registry maps 20 Shape/Graphic/Filter MatchNames to polymorphic native vector evaluator objects; TDB Creator registration itself eagerly instantiates/initializes streams.
- AE2025/26 VectorLayer vftable overrides Rasterize2DGraph at the same slot as AVLayer but with distinct methods; indices change 235 to 238 between versions.
- A native selected-path route resolves BEE_StreamSpec/StreamIDPath into editable TDB streams.
- The standard BEE_CmdNewVectorLayer belongs to an internal project command and Undo lifecycle. The command id shifts 0x65 to 0x6a in consecutive versions.

These are facts about Adobe's internal construction, NOT evidence that third-party code is an accepted factory/Layer/Tool provider.

## Specific falsifiable gates

- S1-TYPE: brand-new third-party MatchName constructs a correct, clonable, refcounted and serializable TDB type in a disposable AE host. Merely CanAdd=true is a fail.
- S1-OWNER: a plugin controls a legal indexed Contents-like root without allocating a built-in Shape Layer or Mask. The host Timeline and Undo persist the actual new children across save/reopen.
- S2-EDITOR: ordinary AE Pen/Selection tools target anchors and tangents owned by S1-OWNER; callbacks reach new authored source streams, not legacy mask/shape streams or overlays.
- S3-RENDER: new owner's render graph entry consumes geometry via BEE_VectorArt and a production RG_RenderNode rather than effect PF_World; correct frame variation/MFR/cache dependency under random access.
- S4-PORTABILITY: pinned AE2025 and AE2026 independently reproduce the behavior with version-appropriate ABI, no host table patch.

## Disproof or limits

If only Shape Layer owns Root Vectors + VectorLayer render virtual, a new evaluator installed under an existing Shape Layer is **not the desired independent owner**. It may be a useful product branch but should be reported separately. If public AEGP stream manipulation is possible only on predefined parents, it does not meet S1. If arbitrary native host layer registration is impossible without modifying BEE's executable tables, the proposed route is a private patch rather than a robust plugin and must be labeled accordingly.

## Safety and ethics

No test in a user's productive project; no unconditional private registrar calls from plugin load. Public SDK samples, x64 static forensic data, disposable offline mocks and source-level verification first. Only when allocator ownership, C++ ABI, destructor/lifetime and host shutdown semantics are understood should a fully rollbackable experiment be proposed. Never ship built-in host vtable patches as a stable API.

## Product potential if proven

Novel native parametric vector layers and effect-owned Contents, user-defined shape operators (procedural typography, offset/merge/filter, constructive path systems), native Pen editing on procedural geometry and AE production vector rasterization with host Undo/animation are genuinely new third-party authoring capabilities. There is no current evidence that the complete feature can be shipped.
