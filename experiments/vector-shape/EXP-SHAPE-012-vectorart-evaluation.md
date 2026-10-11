---
status: observed-static-only
last_verified: 2026-10-11
evidence: E2-L
versions: installed AE2025 and AE2026 BEE.dll
---

# EXP-SHAPE-012 — Native vector object returned before raster output

`BEE_VectorLayer::GetVectorArt` is exported with an intrusive reference-counted `BEE_VectorArt::Group` return type in both binaries, distinguishable from `BEE_VectorLayer::Rasterize2DGraph` returning `RG_RenderNode`.

`GetVectorArt` bounded x64 static disassembly confirms direct calls to Group constructor, TDB_StreamID and TDB_StreamIDPath constructors, `BEE_VectorStream::PopulateVectorArt`, and `BEE_VectorArt::GetBounds`. AE2026 RVAs: `0x708348`, `0x7083A7`, `0x7083B5`, `0x7083E3`, and `0x708448`. Corresponding AE2025 calls: `0x6E3A4F`, `0x6E3ABA`, `0x6E3ACD`, `0x6E3AFC`, `0x6E3BBB`.

`BEE_VectorArt::Path` is constructible inside Adobe's own code from `CAGMPath` or `CAIMBezierPath`. `StreamBasedFilter` binds a `BEE_VectorLayer`, stream path and time. These facts demonstrate why native vector geometry exists as a non-pixel intermediate but **do not establish that an ordinary Effect SDK plug-in can output this intermediate to AE**.

Evidence file: `datasets/ae-vectorart-render-entry-calls-2025-2026.json` — SHA-256 `70482A8AE5C5408B74A7F7E76C5363E82B6BCE21AF29DFBFA2FFA2A95ABCB787`.

Code: `experiments/vector-shape/probe-src/tools/trace_vectorart_render_entrycalls.py`.

Next research must independently find the owner/geometry-provider registration contract before using any private type on a real project. A successful vector Path C++ constructor call would **not** satisfy native editable CompNodeAE output by itself.
