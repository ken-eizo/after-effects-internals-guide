---
status: strongly-supported-static
last_verified: 2026-10-11
evidence: E2-L + E0-G + H
versions: installed AE2026 BEE.dll
---
# F-VECTOR-018 — Native SVG paste builds the ROOT_VECTORS_GROUP TDB path in a generic BEE_Layer context

## Static native code evidence

AE2026 exports BEE_PasteSVGIntoComp with an initial BEE_Layer* argument and a std::shared_ptr<ScSVGParse> input. The type is BEE_Layer*, not BEE_VectorLayer*. This does not establish that arbitrary BEE layers may actually be used: caller preconditions and prior native Shape Layer creation are not yet resolved.

Inside the compiled function at BEE.dll RVA 0x3ae190:

- RVA 0x3ae542 is LEA RDX, RIP-relative; the resolved RVA 0x169fe30 is precisely the exported BEE_VectorStream::StreamName_ROOT_VECTORS_GROUP.
- RVA 0x3ae550 constructs TDB_StreamID, 0x3ae562 constructs TDB_StreamIDPath and 0x3ae575 assigns the result to another TDB path.
- RVA 0x3ae5d6 constructs BEE_Layer::ScSuppressStreamReordered; RVA 0x3ae5ed constructs ScSuppressStreamVisibilityUpdate.
- The same function resolves C_AGMDLTranslatePort::GetProcs and invokes LayerSelectSetupPrePlayback at 0x3ae6cc, and LayerSelectTeardown at 0x3ae84d.

These callsites demonstrate that the native SVG conversion workflow couples parsed vector art, native Root Vectors stream identity, batched host layer-contents mutation guards and AGM display-list translation.

Adobe's official 2026 user documentation confirms SVG import/paste as editable native Shape Layers: https://helpx.adobe.com/after-effects/desktop/import-files/import-svg-files/import-svg-files.html .

## Discriminating hypotheses

A) The passed BEE_Layer is always an already-created BEE_VectorLayer: SVG conversion is a useful one-click native Shape bake, but not an independent effect vector output.

B) A non-vector BEE layer can hold and resolve an authentic Root Vectors TDB path with valid ownership: the importer may be a lead toward custom host-native ownership, but this still requires Timeline, serialization, cache and Tool bindings before claiming parity.

C) Hidden caller state is mandatory: private importer reuse may be impractical without replicating the bootstrap.

No private SVG paste or mutation function was called by ShapeLayerAE. Paths and pointer contract must not be treated as a supported public API.

## Evidence

datasets/ae-svg-paste-native-owner-path-2026.json; tools/audit_svg_native_paste_owner.py; tools/inspect_svg_paste_streampath.py. Offline PE analysis only.
