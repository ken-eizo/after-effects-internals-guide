---
date: 2026-10-14
status: PASS pinned native cross-version direct CompItem attachment xrefs and stock layer factory in both load paths
evidence: E2-L x64 static Capstone decode, two pinned AE2025/2026 BEE.dll binaries
---
# F-VECTOR-067 — Eleven native CompItem attachment callers, and two layer load paths call the closed builtin factory

## Main discovery

F-VECTOR-058 solved the original New Shape command's BEE_Layer::CreateLayerFromType
to BEE_CompItem::AttachLayerToCompOnly path. Could reopening a specially encoded
project instead load a custom ninth BEE_Layer kind without that closed switch?

An exact x64 relative CALL/JMP scan of the installed BEE.dll binaries
recovered **11 native direct incoming callsites per version**, spanning 10
unique native caller functions, into the CompItem attachment methods.
This is not an exhaustive search of indirect and polymorphic dispatch.

The direct caller set includes:
- BEE_Layer::CloneAndAttach, which receives/produces a BEE_Layer and calls
  the generic native CompItem attachment.
- The built-in new-layer transaction worker.
- BEE_TextLayer::CloneAndAttachFromAVLayer.
- Native file/project layer materialization and other CompItem helper paths.

Exact target RVAs:
- 2025: CompItem AttachLayerToCompOnly 0x392120, partial Attach 0x3920F0.
- 2026: CompItem AttachLayerToCompOnly 0x39D4D0, partial Attach 0x39D4A0.

## Important secondary factory guard: BOTH native file-layer materializers

The two file/project-layer creation functions in each version that attach
a BEE Layer BOTH call the SAME closed builtin layer factory FIRST:

AE2025:
- 0x505090: fixed factory at callsite 0x5052FB (target 0x2E3E10),
  then native CompItem attach at 0x505376.
- 0x505400: fixed factory calls at 0x505631 and 0x505643,
  then native CompItem attach at 0x5056AF.

AE2026:
- 0x51F2F0: fixed factory call at 0x51F55D (target 0x2ECD00),
  then native CompItem attach at 0x51F5C6.
- 0x51F650: fixed factory calls at 0x51F865 and 0x51F877,
  then native CompItem attach at 0x51F8E0.

All these callsite ordering facts are checked directly in compiled native
instructions in BOTH AE versions by verify_native_layer_load_not_foreign_factory.py.

Thus an arbitrary MatchName in a saved .aep is not evidenced to bypass the
stock 0..7 type dispatcher through these two particular native load paths.
This closes an attractive but unsupported "encode a foreign layer in a
project and let AE construct it" shortcut.

## What the generic native clone path does AND does not imply

BEE_Layer::CloneAndAttach is a separate method with a legitimate native
CompItem insertion call operating on a cloned/preconstructed BEE_Layer.
This is relevant to an independent owner investigation: at the final attach
site the C++ pointer's original class/ownership matters, not merely an
integer type argument to the stock factory.

BUT the clone path does not supply a new foreign BEE_Layer constructor,
prove that BEE accepts a late registered subclass, or establish native
Timeline editor, Undo, serialization and VectorArt safety. It must NOT be
invoked on an unverified private C++ object in the user's AE environment.

A generalizable distinction now supported by code:
- TDB child registration is NOT BEE Layer construction.
- Native prefix CanAdd TRUE is NOT a creator/evaluator.
- BEE CompItem Attach accepts a pointer but is NOT a custom factory.
- Project loading/reopening does NOT automatically mean arbitrary layer type
  construction; the two examined real materializers call the closed factory.

## Scope

The above is a static direct-call census, NOT a proof that no indirect
factory pathway or other undocumented third-party extension could exist.
The genuine independent Adobe-host-owned ChapeLayer is still NOT implemented.
The CNL typed native Timeline model F-VECTOR-066 is compiled and testable, but
has not been admitted to Adobe's BEE/TDB Timeline, editor or renderer.

## Reproduction

Source:
experiments/vector-shape/probe-src/tools/scan_native_compitem_attachment_xrefs.py
experiments/vector-shape/probe-src/tools/verify_native_layer_load_not_foreign_factory.py

Datasets:
datasets/ae-bee-compitem-attach-inbound-xrefs-2025-2026.json
datasets/ae-bee-compitem-load-path-closed-layer-factory-2025-2026.json

All analysis offline. No Adobe DLL changes, no AE host private calls,
no user project mutation, no CompNodeAE changes, Phase F paused.
