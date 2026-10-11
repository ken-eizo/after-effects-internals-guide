# CompNodeAE Native Editable Path Bridge

A controlled research AEGP, no private Adobe BEE/TDB function calls. Converts four real PICA cubic Bezier curves from independently compiled VectorBridgeAEGP into a true host-native Mask Path on an ordinary selected AV Layer, WITHOUT a Shape Layer.

Built AEX: D:/Developer/ShapeLayerAE/build/native_editable_path/Release/NativeEditablePathBridge.aex

Build: cmake --build D:/Developer/ShapeLayerAE/build/native_editable_path --config Release

Read-only static verifier: python D:/Developer/ShapeLayerAE/labs/native_editable_path/verify_native_path_bridge.py

The user alone handles AEX installation and After Effects GUI testing. Do not install automatically.

## AE Animation menu

1. CompNodeAE: Create Native Editable Mask from PICA

Select exactly one normal Solid/Footage layer; this creates four cubic native Mask Path anchors, with closed path and mask mode NONE (no clipping). Press M to reveal Mask Path and use the real Pen/Selection tools. There is NO new Shape Layer. It is NOT an effect-owned Contents object.

2. CompNodeAE: Native Mask Renderer (ADD, Clips Layer)

Same path, but Mask ADD. The standard AE native mask compositor clips the ordinary layer according to our code-generated path. This is not the Shape Layer AGM/VectorArt renderer.

3. CompNodeAE: Inspect Native Owner Roots (Read Only)

Reads the selected normal/shape layer's true root stream grouping and direct MatchNames into %TEMP%/CNL_NativePath_OwnerProbe.tsv. Save each capture separately, as running the command overwrites it.

## Constraints

- VectorBridgeAEGP must already be installed, because this plugin does NOT replace its PICA geometry provider.
- No path created if PICA Suite absent or layer object is not ordinary AV.
- The cubic geometry is baked at the current comp-time. Not a live continuously linked graph value; manual Pen changes do not feed back to the procedural source.
- A native Mask is owned by the ordinary layer's Mask Parade, NOT by the Effect SDK effect.
- No direct native BEE_VectorArt, Shape Contents root, independent vector operator or native Pen tool ownership in effect has been achieved.
- Explicit menu actions only, host undo and cleanup if insertion fails. Test on a disposable project.
- An AE host success is NOT claimed until the user runs the provided menu commands.

AEIG: F-VECTOR-024, EXP-SHAPE-022. Original source only, no Adobe binaries redistributed.
