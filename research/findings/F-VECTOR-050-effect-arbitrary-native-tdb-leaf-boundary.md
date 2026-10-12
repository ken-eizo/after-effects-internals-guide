---
status: strong-static-cross-version-native-host-arbitrary-leaf
date: 2026-10-12
evidence: E2-L pinned FLT2025/26 PE + separately built public-SDK AEX
---

# F-VECTOR-050 — Public Effect arbitrary data is backed by real native TDB-derived FLT stream

## New cross-boundary bridge from F-VECTOR-049

F-VECTOR-049 built and tested an actual 64-bit `CNLOwnedVectorEffect.aex` with native CNL nested Bezier groups, per-effect host-serializable `PF_Param_ARBITRARY_DATA`, robust binary/text archive callbacks, and a visible 8bpc CPU render path without Mask/Shape carriers. That proves the plugin-side data ownership contract in a separately compiled effect.

The corresponding Adobe-host native wrapper can now be identified much more precisely. The installed AE2025 and AE2026 **FLT.dll** export the real type **`FLT_ParamArbDataStream`**, with a primary vtable and constructor inheriting from **`TDB_DerivedStream<FLT_ParamArbDataStreamTraits>`**. This is a *native TDB stream object that owns the Effect's Arbitrary parameter value*, rather than a fabricated match-name entry or a custom vector Contents group.

### Exact native evidence

| Native operation | AE2025 RVA | AE2026 RVA |
| --- | --- | --- |
| `FLT_SeqInqParamStream` (effect parameter index → host stream) | `0x62520` | `0x64390` |
| `FLT_ParamArbDataStream::Create` | `0x3AC0` | `0x3CA0` |
| `FLT_ParamArbDataStream::CloneStream` | `0x37A0` | `0x3990` |
| `FLT_ParamArbDataStream` native regular constructor | `0x25B30` | `0x271A0` |
| `FLT_ParamArbDataStream::DisposeValue` | `0x262F0` | `0x27B60` |
| `FLT_ArbitraryPrint` | `0x26320` | `0x27B90` |
| `FLT_ArbitraryPrintSize` | `0x263A0` | `0x27C00` |
| `FLT_ArbitraryScan` | `0x26420` | `0x27C70` |

The `Create` and `CloneStream` implementations each allocate **`0x470` bytes** via Adobe's `U_MemTrackedObject` allocator in both releases, then call their real native constructors, including the `TDB_DerivedStream<FLT_ParamArbDataStreamTraits>` base. The `DisposeValue` path delegates to `DeleteArbDataItem`; that method calls `TDB_Stream::GetValueDesc` and `TDB_StreamBase::GetParamDef`, and retrieves an associated Effect spec. All three arbitrary PRINT/SIZE/SCAN entrypoints call `FLT_ParamArbDataStream::GetAssociatedArbDataEffect_Impl` before dispatching their operation, binding arbitrary serialization to the real host Effect owner.

The actual `FLT_SeqInqParamStream` takes a `FLT_FCSeqSpec`, a parameter index and an output stream pointer, connecting a real Effect parameter to native FLT/TDB stream identity. This method's existence and compiled code do **not** authorize a third-party AEX to call this undocumented FLT API; the connection is structural evidence.

## Key architectural conclusion

It is now possible to distinguish:

**Already implemented by CNL:** an independent indexed/serializable CNL Group/Path/Bezier document, inside the real public Effect's arbitrary parameter, plus real compiling/rendering callback code. Real host acceptance and AEP roundtrip have not yet been manually tested.

**Provided by Adobe natively:** the host-side `FLT_ParamArbDataStream` value-level TDB wrapper for Effect arbitrary params, including native clone/dispose/print/scan integration with `FLT_FCSeqSpec`.

**Not provided by this contract:** arbitrary third-party insertion of distinct CNL `TDB_NamedStreamGroup` child streams; native `TDB_StreamIDPath` for each individual CNL Group/Path node; AE Composition Pen/Selection hit-test and drag/writeback; `BEE_VectorArt` evaluation or `BEE_VectorLayer::Rasterize2DGraph`. An arbitrary *leaf* in the host hierarchy is not the same as native *editable Contents*.

The possibility of using genuine native Effect parameter Undo/animation/value setters with entire CNL archive data merits future investigation, but byte-level editing of one archive through an otherwise native stream is **not evidence that Adobe's Pen tool can edit vertices**. Do not patch FLT.dll, call this opaque private C++ ABI from an AEX, or treat “TDB-derived” as a magic route to the renderer.

## Reproduction

- `experiments/vector-shape/probe-src/tools/trace_effect_arbitrary_tdb_stream_bridge.py`
- `experiments/vector-shape/probe-src/tools/verify_effect_arbitrary_native_stream_bridge.py`
- `datasets/ae-flt-effect-arbitrary-native-stream-bridge-2025-2026.json`
- `datasets/ae-flt-effect-arbitrary-native-stream-bridge-verified-2025-2026.json`
- `experiments/vector-shape/EXP-SHAPE-050-effect-arbitrary-data-native-tdb-leaf-boundary.md`

All results are on-disk native FLT PE static disassembly, with no host private API calls. The new CNL compiled AEX remains untested in actual AE 2026 until the user manually runs it on a disposable project.
