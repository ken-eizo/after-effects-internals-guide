---
date: 2026-10-14
status: PASS bounded public SDK v25.6 registration surface audit; no arbitrary native Layer type registration discovered
evidence: E2-L locally installed Adobe SDK AE_GeneralPlug.h with source SHA-256, reproducible static verifier
---
# F-VECTOR-072 — Public AEGP creation and registration contracts do not include custom native BEE Layer classes

## User requirement

The goal is to provide independent ChapeLayer-native layer families and arbitrary nested Timeline Contents, not a built-in Shape/Mask/effect carrier. The actual public API boundary must be distinguished from Adobe's separate internal BEE/TDB registries before considering any private ABI.

## Inspected source and scope

Source is the installed `E:/ae25.6_61.64bit.AfterEffectsSDK/Examples/Headers/AE_GeneralPlug.h`. Its exact SHA-256 is captured in `datasets/ae-public-sdk-native-layer-extension-surface-25-6.json`. This is the locally installed SDK 25.6 header, **not** an assertion that every possible future SDK, Adobe-private capability, or host build has the same contract.

The offline audit extracts the complete function-pointer names in `AEGP_RegisterSuite5`, the `AEGP_CreateVectorLayerInComp` prototype, `AEGP_ObjectType` enum and the specific DynamicStream/Command operations. The full list of 12 public RegisterSuite entries is frozen by a fail-closed assertion in the verifier.

## What is positively available

- `AEGP_CompSuite12::AEGP_CreateVectorLayerInComp(AEGP_CompH, AEGP_LayerH*)` creates an **existing Adobe Vector/Shape layer**. It accepts no foreign layer kind, custom native constructor, C++ factory callback or property schema parameter.
- `AEGP_LayerSuite9::AEGP_AddLayer` adds an existing item to a composition; it is not a registration mechanism for new C++ Layer subclasses.
- `AEGP_DynamicStreamSuite` exposes `AEGP_CanAddStream` and `AEGP_AddStream` for manipulating host-recognized Indexed Group contents, but the API declaration does not define a new native Stream class, creator or renderer.
- `AEGP_Menu_NEW` can be used to add a Layer > New menu **command**. The command callback does not itself define a new native BEE Layer type.
- `AEGP_RegisterSuite5` supports commands, update/death/version/about/idle hooks, Artisan/Interactive Artisan, IO, Tracker and preset localization, but **no explicit custom native Layer class, TDB_StreamBase type, BEE Vector evaluator, or property schema registrar**.
- `AEGP_ObjectType` lists existing AV/Light/Camera/Text/Vector/3D Model variants plus reserved enum values. Reserved identifiers alone are not extension registration APIs.

## What this means for the native architecture

Publicly creating a genuine **built-in** Vector Layer is supported and must not be misreported as impossible. Creating a separate native `ChapeLayer` family with its own `BEE_Layer` subclass, host-owned Contents grammar and evaluator is a different requirement. No function serving that need was found in this precise public registration suite.

That does NOT prove globally that a private extension mechanism does not exist, and does not automatically prohibit a plugin from maintaining CNL-owned data. F-VECTOR-037 showed the built-in `CreateLayerFromType` dispatcher is closed to ninth arbitrary integer kinds. F-VECTOR-071 showed that even the generic-looking Layer attachment performs version-specific object/vtable operations. Neither route is a supported bridge merely because a related command exists.

A built-in Shape Layer carrier or custom PF Effect UI would not satisfy the independent Layer objective.

## Reproduction

- `experiments/vector-shape/probe-src/tools/audit_public_sdk_native_layer_extension.py`
- `datasets/ae-public-sdk-native-layer-extension-surface-25-6.json`
- `experiments/vector-shape/EXP-SHAPE-072-public-sdk-native-layer-registration-surface.md`
- `experiments/observatory/manifests/EXP-SHAPE-072.json`

Offline verifier PASS on the installed SDK. No AE runtime, private host calls, Adobe binaries, CompNodeAE, or user projects were modified.

## Remaining highest-priority unsolved questions

1. Is there any separate, host-supported native Layer class provider mechanism in AE outside the inspected public AEGP suites and fixed LayerType constructor? What exact load/registration boundary would make it valid?
2. If only an Adobe-private C++ registrar exists, can it be made ABI-safe with deterministic registration/unregistration, version-correct RTTI, stable ownership, serialization and user document safety?
3. If no credible external registration boundary can be demonstrated, record the evidence-limited limit and define separately what a private API or Adobe cooperation would need to supply. Do not relabel a built-in Shape or Effect as an independent Layer.
