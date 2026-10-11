---
status: strongly-supported-static-proposed-host-experiment
last_verified: 2026-10-12
evidence: E2-L + H
versions: locally installed AE2025 and AE2026 TDB.dll
---

# F-VECTOR-030 — Native Adobe path-stream Creator as an external new-MatchName registration bootstrap candidate

## Why this test is materially different from standard AE plugins

The research must create a new native TDB type under a plugin-specific MatchName, with no Mask, built-in Shape Layer, SVG or pixel-only PF_World output. Adobe's private StreamFactory does accept real C++ native stream Creator callbacks internally, but a foreign half-initialized TDB_StreamBase is unsafe: RegisterFactoryFunc eagerly invokes CreateStream and virtual methods (F-VECTOR-026).

A new, safer **unexecuted hypothesis** is to use Adobe's own complete TDB_ParamPathStream::Create as the callback for a NEW plugin-specific native TDB MatchName in a version-pinned, explicitly user-triggered, immediately rolled-back disposable-host experiment. This tests whether the native factory accepts externally supplied registrations without simultaneously requiring us to implement a complete proprietary TDB_StreamBase subclass. It is not the final design and does not establish independent owner or rendering.

## Concrete native export and constructor evidence

The exact AE2025 and AE2026 installed TDB.dll exports include a native Creator of this signature:

TDB_StreamBase* TDB_ParamPathStream::Create(TDB_MatchName const&, TDB_StreamFactory*, unsigned __int64, unsigned int, unsigned int)

| Host | Creator RVA | ParamPathStream constructor RVA | MatchName(char const*,bool) RVA |
| --- | --- | --- | --- |
| AE2025 | 0x10750 | 0xea90 | 0x2c610 |
| AE2026 | 0x107c0 | 0xeb30 | 0x2d1f0 |

Actual disassembly confirms that the Creator uses native tracked U.dll allocation, then constructs a derived TDB stream object using a native constructor, rather than returning an arbitrary foreign buffer. The MatchName constructor initializes native Guid and obtains a named identity from TDBp_MatchNamePool::GuidFromName. A TDB_StreamBase base constructor exists and also references TDB_AreTDBStreamScriptingIDsEnabled and a main-thread predicate.

In addition, both installed versions export native TDB_StreamFactory::RegisterFactoryFunc, TDB_ScRegisterStreams::Register, and the corresponding unregister functions. F-VECTOR-026 confirms RegisterFactoryFunc eagerly constructs a stream and requires valid native IsLeaf/GetAsLeaf/SetupCanonicalLayout implementations; an Adobe-built class can at least meet the class ABI constraints better than guessed third-party structs.

## Critical unresolved hazards — NO live registration authorized by this finding

- These exports are private Adobe C++ methods, not a supported plug-in extension. No third-party registering any new name has been observed.
- TDB_MatchName and the by-value MSVC std::function Creator parameter have opaque native layouts/compiler/lifetime semantics. A locally built std::function is not automatically ABI-compatible, even with MSVC 2022.
- The ParamPathStream constructor may require built-in per-type schema/configuration. Reusing it with a novel MatchName might fail during eager canonical setup, assert, corrupt host memory or leak.
- Register/unregister may depend on early host bootstrap order and on native project threads. TDB_StreamBase constructor consults host state and main-thread status.
- Native creator class is not an independent AE vector owner, not a root Contents type, and not a BEE_VectorArt operator.
- A foreign creator's std::function vtable must remain alive as long as the host registry stores it. Plugin unload with a lingering callable is dangerous.
- A unique registration may be unremovable or live project instances may survive. No actual test has proven safety.

## Proposed strict experimental gates

1. Preflight exact binary SHA256, exported native method names, constructor/layout and MSVC callback vtable semantics. Both tested TDB hashes pinned: AE2025 2ed19824997f3de797a75fef6f22d4d11ac8548c9d35f6093aa2afc1a6ed2e69; AE2026 82677a20bdf871878b579522c4b4e0def8af0a50a810e3b9972da1170f546c1b.
2. Build an offline mock ABI and callback lifecycle harness — no private host invocation — to check exact C++ by-value std::function transfer and reverse-order cleanup semantics first.
3. Only on the user's explicitly authorized disposable AE host, no production project: a manual command with further confirmation would register a unique CNL-prefixed MatchName using the known native Creator and immediately unregister it; never run from plugin initialization or render.
4. Prove native registry returns success, synchronous canonical stream creation succeeds, unregister returns success, no stale native canonical pointer/registered name remains and clean AE shutdown follows. A lack of crash is NOT sufficient proof.
5. Only if that passes: independent owner/TDB indexed tree registration, Pen selection identity, BEE evaluator and native render graph are separate experiments.

Do NOT ship an unsafe, always-on private registration AEX. This finding provides feasibility evidence only; no host test or new registered type currently exists.

## Reproducible artifact

- datasets/ae-native-tdb-built-in-path-creator-registration-feasibility-2025-2026.json
- experiments/vector-shape/probe-src/tools/audit_tdb_builtin_creator_as_external_bootstrap.py
- EXP-SHAPE-027-built-in-creator-new-matchname-registration-preflight.md
- Prior F-VECTOR-025/026/027/028/029

This is read-only static disassembly, with no AE host control and no installed new plug-in.
