# CNL Native Vector Host Probe (Research AEGP)

This is a compiled Adobe AEGP containing the independent CNLNativeVectorCore object model. It deliberately DOES NOT register an Adobe TDB stream type, BEE vector evaluator, Pen editor or native VectorArt output. This is an **in-host preflight** only, NOT the final new vector plug-in.

## User-invoked action

- Creates an independent hierarchical CNL document inside AE's process, with a native procedural ellipse as four double-precision cubic Bezier segments (not rasterized, not a Mask, not built-in Shape).
- Computes the exact loaded TDB.dll SHA256. Calls a known nonmutating private no-argument getter **only** when SHA matches a pinned AE 2025/2026 binary AND getter opcode fingerprint matches.
- Checks *export presence* for the private native factory Creator, register/unregister and canonical query. It does NOT call those exports.
- Does not create an AE layer, effect, project data or shape, and does not mutate the private registry.
- Writes %TEMP%\CNL_NativeVector_HostPreflight.tsv, then displays a short AE info dialog.

## How to use (user installs; researcher never installs or operates AE GUI)

1. Obtain D:\Developer\ShapeLayerAE\build\native_vector_host_probe\Release\CNLNativeVectorHostProbe.aex.
2. Close After Effects, copy to the AE Plug-ins directory, restart.
3. Select Animation > CNL Native Vector: Host Preflight (Read Only). No layer or comp required.
4. Inspect %TEMP%\CNL_NativeVector_HostPreflight.tsv.
5. Expect CNL_double_bezier_cubic_status=0 and CNL_native_cubic_segment_count=4. Native type registration is deliberately 0.

## Build

    cmake -S "D:\Developer\ShapeLayerAE\labs\native_vector_host_probe" -B "D:\Developer\ShapeLayerAE\build\native_vector_host_probe" -G "Visual Studio 17 2022" -A x64
    cmake --build "D:\Developer\ShapeLayerAE\build\native_vector_host_probe" --config Release

This is a bridge between native CNL geometry and the AE plug-in host process, not proof of true AE-native editing. Type/owner/editor/evaluator/renderer contracts remain unsolved. Use a disposable project for tests.
