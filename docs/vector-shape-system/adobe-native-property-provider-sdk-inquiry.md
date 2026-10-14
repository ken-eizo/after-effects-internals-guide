# After Effects SDK team inquiry — Third-party native Timeline Stream/Group provider API

> **Draft only. Not sent.** Prepared for the Adobe After Effects **C++ SDK** developer support channel.
>
> Entry: https://developer.adobe.com/developer-support/ (After Effects → C++).

**Subject: Is there a supported SDK/partner interface for registering new host-native Timeline Stream and Group classes (Paint / Text Animator style)?**

Hello After Effects SDK team,

We are developing a native Windows/macOS After Effects plug-in that requires **new classes of properties and property groups** to appear directly in the standard **After Effects Timeline**. Our specific goal is a third-party-defined native property hierarchy that users can expand, edit, reorder, keyframe, select, and save to an .aep project, comparable in integration to the built-in Paint effect's *Strokes → Brush → Stroke Options* and a Text Layer's *Animators → Animator Properties*.

We do **not** mean custom Drawbot UI, an independent extension panel, a pseudo-effect, a fixed `PF_Param_GROUP_START`/END topic around ordinary PF effect controls, or adding existing `ADBE` property types to an existing indexed group. We specifically need to **register previously unknown native Stream classes and parent/child group schemas** whose values, keyframes, lifetime and persistence are hosted by AE.

We have verified with the installed After Effects SDK 25.6:

- `AEGP_DynamicStreamSuite4` can enumerate and manipulate **existing registered** native Stream types, but `AEGP_AddStream` does not provide a new Stream class definition.
- `AEGP_RegisterSuite5` offers 12 registration hooks covering commands, IO, Artisan, trackers, etc., but no documented generic native Stream or Layer provider.
- The built-in brush-created **Paint** effect is an AEX with internal host-level handling; we can enumerate its real native Strokes and Path property leaves using public AEGP.
- On AE2026, `AEGP_CanAddStream` for the Paint Strokes group returns true for `ADBE Paint Atom` but false for an unknown custom child MatchName. We cannot infer arbitrary class registration from Paint's own functionality.

Could you clarify the following API support questions?

1. **Native Stream type provider:** Is there a supported extension interface — public, partner-only, or under another SDK — that lets a third-party AEX define a new native Timeline property/Stream class with a unique MatchName, type, factory and value/editor callbacks?
2. **Native group admission:** Can a third party define a native Named/Indexed Group with its own allowed child types and native Add / Delete / Reorder behavior, beyond `PF_Param_GROUP_START`?
3. **Effect vs layer ownership:** Could this custom native property group belong directly to a third-party **effect** (similar to Paint's Strokes) rather than requiring a new Layer class?
4. **Host lifecycle:** If an interface exists, what are the supported registration timing, class lifetime, unload, Undo, multi-frame evaluation, .aep serialization, version migration and macOS ABI requirements?
5. **Unsupported scope:** If neither the public nor partner SDK permits these capabilities, can you confirm that genuinely new host-native Timeline Stream classes/groups are **not currently supported for third-party plug-ins**, and whether they are on the roadmap?

A precise supported API name or clear unsupported statement would be extremely helpful, so we can avoid relying on unstable undocumented internals.

Thank you for any guidance.

---

## Internal notes — do not copy into the public post unless useful

Related internal evidence:
- `F-VECTOR-080`: Paint Stream factories and BEE/TDB static registration.
- `F-VECTOR-083`: actual Paint child admission in AE2026.
- `F-VECTOR-087`: real Paint 6 Brush / 170 Stream / 142 leaf metadata host test; Paint Path returns `AEGP_StreamType_NO_DATA`.
- `F-VECTOR-088`: 70 public headers, no exposed class provider registrar.
- `docs/vector-shape-system/native-property-extension-admission-gates.md`: complete host-owned acceptance gates.

A reply proving no supported provider would close the **publicly supported solution** branch but not imply an unsupported private implementation is technically impossible in principle. Do not promise a native product until a host-admitted third-party Stream and full archive/lifecycle have actually been tested.
