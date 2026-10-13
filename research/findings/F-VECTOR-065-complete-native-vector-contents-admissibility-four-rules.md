---
date: 2026-10-13
status: PASS full built-in Shape Indexed Contents CanStore name predicate reconstructed from AE2025/2026
evidence: E2-L actual installed BEE x64 compiled native global TDB_MatchName initializer and CanStore MatchName equality + CRT strstr prefix branches
---
# F-VECTOR-065 — Complete Shape Contents native accepted-child naming rule: exact Group OR three prefixes

F-VECTOR-063 proved three prefixes from actual CanStore instructions and the VCRUNTIME140.dll!strstr call sequence in both installed AE2025/2026 binaries. It left the initial native TDB_MatchName object identity unresolved.

**The complete name predicate is now reconstructed:**

    CanStore(name) =
        (name == "ADBE Vector Group")
        OR name.startswith("ADBE Vector Shape -")
        OR name.startswith("ADBE Vector Graphic -")
        OR name.startswith("ADBE Vector Filter -")

## The previously missing exact MatchName object

The initial special-case compares the input TDB_MatchName to a single **global TDB_MatchName object**. That object's native static constructor is now located in two installed binaries:

- AE2025: global object's static constructor at RVA 0x1C030: LEA RDX resolves to original read-only literal "ADBE Vector Group", LEA RCX resolves to the global TDB_MatchName object at RVA 0x15EF420, followed by a jump to TDB_MatchName constructor. CanStore at RVA 0x700263 references that same global object at 0x15EF420.
- AE2026: native static constructor at RVA 0x1B760 similarly initializes "ADBE Vector Group" into global object 0x169FDF0. CanStore at RVA 0x723C89 directly references 0x169FDF0.
- These are **exact object address equivalences verified from RIP-relative x64 instructions** in both binaries, not guesses from UI or MatchName conventions.

Then the predicate obtains the original string with TDB_MatchName::GetName and compares three calls of VCRUNTIME140.dll!strstr to the original string pointer (prefix semantics), returning true for any match. It never consults the native TDB factory nor the BEE evaluator registry.

**This rules out the previous possibility of more hidden equality exceptions inside this particular class method.** It does NOT imply the full host AddStream pipeline has no other validator. User-host experiments confirm CanAddStream true for unknown ADBE prefixes but have never attempted unknown AddStream.

## Generalizable architectural constraint

A *plugin-defined group* under the same built-in type cannot choose arbitrary custom child namespace identities unless its parent-admission predicate is also changed. This is different from simply registering new C++ factories. Conversely, spoofing the builtin prefix is insufficient to construct an instance if its native TDB creator/evaluator do not exist. The required extension interfaces are independently:
1. Parent grammar/CanStore rule,
2. Type factory registration and typed lifecycle/serialization,
3. Owner dispatch/Timeline integration,
4. Geometry evaluator, native editor/Undo,
5. BEE_VectorArt/RenderGraph render integration.

The goal of ChapeLayer must remain author-defined native type grammars rather than reproducing PF_Param_GROUP or just building a different SVG renderer.

## Reproduction

Tool: experiments/vector-shape/probe-src/tools/verify_canstore_special_exact_native_group_key.py
Receipt: datasets/ae-vector-contents-canstore-special-group-key-2025-2026.json
Earlier prefix receipts: F-VECTOR-063 / EXP-SHAPE-063.

No private function was invoked in AE; no AE process, project or Adobe binary modified. The genuine CNL native BEE owner and arbitrary native Timeline Contents are still not constructed/registered.
