---
status: hypothesis
last_verified: 2026-10-11
evidence: E2-L + H
versions: AE 2025 and AE 2026
---
# H-SHAPE-003 — RegisterStreams means stream-operation command registration, type registration, or both?

## Competing hypotheses

H-COMMAND: The per-layer `RegisterStreams` routine registers stream *operations* (undoable command/handler entries), distinct from type factory bootstrap. Observed calls to `BEE_CmdSetStreamBaseFlag`, `BEE_CmdSetStreamVary`, `BEE_CmdSetExpressionEnabled`, `BEE_SelectKeyframe` and (from AVLayer) `BEE_CmdReorderIndexedGroupEntry` are compatible.

H-TYPE: The routine registers **stream type constructors/schemas** with the factory, and the operation calls are incidental. This requires identifying actual writes of new match-name/type-descriptor entries into a factory-owned registry.

H-MIXED: The routine registers both operation dispatch and new stream type data.

## Discriminating test

Pin AE build and BEE SHA-256. Analyze the routine's exact callers, complete control flow and resulting data writes, not just export names. Distinguish command registration storage from stream factory allocation. Observe runtime initialization safely and compare the same graph to `BEE_TextLayer::RegisterStreams` and `BEE_Layer::RegisterStreams`. Never conclude open third-party registration from built-in registration.

## Success gate

An independent, host-owned indexed Contents-like group with native Timeline editing, persistence and path tools, created without normal Shape Layer construction, would falsify a sealed-only model. Until such a test succeeds, private factory availability remains **unverified**.
