# EXP-SHAPE-107 — MEE general plug-in Setdown versus PLUG routine lifetime

**Result: PASS, AE2025 and AE2026 installed original Windows binaries, read-only static x64.**

## Question

When the `aelib` termination state machine visits Stage 32 and invokes `SetdownGeneralPlugins`, does the function automatically unload the corresponding third-party plug-in DLL?

## Observed native path

```text
aelib Terminate stage 32
 → MEE_AEGP_Death
 → MEE_AEGP_Terminate
    → PLUG_UnprepRoutine
    → PLUG_UnregisterRoutine
 → MEE::SetdownGeneralPlugins
    → for each general plug-in record (stride 0xB8):
        if callback at +0x58: invoke with refcon at +0x10
        if prepared flag at +0xB0:
            clear flag
            PLUG_UnprepRoutine(routine descriptor)

PLUG_UnprepRoutine:
 → Lock RecursiveMutex
 → native routine-descriptor method virtual +0x30
 → bookkeeping
 → Unlock

Later native PLUG module Stage 14:
 → PLUG_Death
    → PLUG_UnregisterRoutine
```

**Crucial boundary:** an Unprep operation has no direct `FreeLibrary` call in its examined native body; however, indirect routine descriptor and module wrapper code could release an image. Thus neither immediate unloading nor guaranteed retention is established. An independent native Stream provider still needs a separate proof that its code/vtables remain alive while Undo tasks and project objects can reference them.

## Reproduction

```powershell
python "D:\Developer\After Effects Internals Guide\experiments\vector-shape\probe-src\tools\verify_mee_plug_setdown_unprep_unregister.py"
```

The verifier SHA-pins four original `MEE.dll`/`PLUG.dll` images and checks exported C++ functions, RIP-relative imports, private per-record offsets, indirect callback order and the distinct Unregister path. **No Adobe private function was called.**

Receipt: `datasets/ae-mee-plug-general-plugin-setdown-unprep-unregister-2025-2026.json`.

Finding: `research/findings/F-VECTOR-107-mee-plug-general-plugin-setdown-unprep-unregister-lifetime.md`. Primary AEIG feature page: `docs/host-integration/aegp/general-plugin-setdown-lifetime.md`.
