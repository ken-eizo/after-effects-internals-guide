---
status: user-observed-failure; fix compiled, host-retest-pending
last_verified: 2026-10-11
evidence: E0-H + user-supplied screenshot (host reported, environment incomplete)
versions: AE runtime reported by user after installing ShapeLayerAE; probe SDK 25.6
---
# EXP-SHAPE-001 — GetNumStreamsInGroup leaf precondition incident

## Failure

User reported three After Effects dialogs:
\`After Effects error: internal verification failure, sorry! {GetNumStreamsInGroup only works on groups}\`

The original observer at \`D:\Developer\ShapeLayerAE\src\ShapeLayerProbe.cpp\` used \`grouping != AEGP_StreamGroupingType_NONE\` as the precondition for \`AEGP_GetNumStreamsInGroup\`. This was **wrong**: \`LEAF\` is not \`NONE\`, but is not a group.

**Distributed E0-H SDK 25.6** \`AE_GeneralPlug.h\` enum (around line 1600):
\`NONE = -1, LEAF = 0, NAMED_GROUP = 1, INDEXED_GROUP = 2\`.
\`AEGP_GetNumStreamsInGroup\` is documented with the explicit comment \`// error on leaf\` (around line 1662).
\`AEGP_GetNewStreamRefByIndex\` says \`// legal for namedgroup, indexedgroup, not leaf\` (around line 1679).

## Repair

Only call \`AEGP_GetNumStreamsInGroup\` when grouping is \`NAMED_GROUP\` or \`INDEXED_GROUP\` and grouping query succeeded. This also avoids making an invalid child request on LEAF.

The corrected C++ source compiled successfully against the local SDK 25.6 using CMake/MSVC. Note: a successfully linked AEX **does not prove** successful run, host restart/reinstall, or that other errors will not arise. The installed plugin is an older file until it is replaced with the newly built \`ShapeLayerAE.aex\` while AE is closed and AE restarted.

## What this observation proves and does not

- It is a reproducible SDK **precondition** issue supported by the exact distributed header, and user reported a consistent AE assertion.
- It is not a crash proof, new private extension mechanism, or evidence that AE's Shape Contents is entirely opaque.
- No debugger/log/AE host-version/after-fix capture was available yet; maintain host-retention uncertainty rather than claiming E2-X reproduced.
- Preserve the reported error in troubleshooting and use this failure to strengthen precondition checks in all future stream observers.
