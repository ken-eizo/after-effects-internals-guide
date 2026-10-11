# CNL Private TDB Disposable Registration (HIGH RISK, NOT HOST TESTED)

This is a separate research AEGP containing unverified Adobe private-API calls. It is NOT the safe CNLNativeVectorHostProbe AEX. Do NOT install or run in working AE or real projects.

Research hypothesis: in a disposable clean AE process, use the known complete Adobe TDB_ParamPathStream::Create callback under a NEW CNL-specific MatchName to test whether the native StreamFactory permits external type registration; then immediately unregister. This is NOT independently owned Contents, Shape, Mask, native Pen path, or BEE vector rendering.

Static evidence: installed AE2025/2026 TDB_MatchName(char const*, bool) constructs a 16-byte GUID via TDBp_MatchNamePool::GuidFromName; TDB_ParamPathStream::Create allocates a real Adobe-native 0x468-byte C++ class. TDB_StreamFactory::RegisterFactoryFunc takes a by-value MSVC std::function, eagerly calls CreateStream, and invokes native virtual methods; UnregisterFactoryFunc removes maps and destroys a native stream. These are PRIVATE, unstable contracts.

## Deliberate safety gates

1. Absolutely nothing mutates private registries at startup. Only an explicit Animation menu command can attempt registration.
2. Loaded TDB.dll must have the EXACT pinned 2025 or 2026 SHA256.
3. Exact decorated native exports must exist for Get_AE_StreamFactory, TDB_MatchName constructor, TDB_ParamPathStream::Create, RegisterFactoryFunc and UnregisterFactoryFunc.
4. Getter x64 opcode fingerprint must match.
5. No active selected layer.
6. Set process environment variable CNL_TDB_DISPOSABLE_HOST_TEST to exactly I_ACCEPT_PRIVATE_REGISTRY_CRASH_RISK before launching the disposable AE host.
7. Create one-shot file %TEMP%\CNL_TDB_DISPOSABLE_ACK.flag with exact content CNL_TDB_ONLY_DISPOSABLE_NO_REAL_PROJECTS (newline optional).
8. The one-shot file is DELETED before invoking private registration. A second click requires recreating it.
9. If registration succeeds, immediately request UnregisterFactoryFunc before returning.
10. Exact stage journal flushed to %TEMP%\CNL_PrivateTDB_Disposable_Test.tsv before potentially crashing calls.

THESE GATES DO NOT MAKE IT SAFE. Native code may assert, crash, corrupt caches, or leave references even if UnregisterFactoryFunc returns true. Only a clean, isolated disposable process with no valuable AEP/projects is appropriate. Restart after the test. Never ship in production. A successful return is not proof of native editable Contents. Do not use this AEX until the safe AEX host preflight has been tested by the user, and the user explicitly elects to try the dangerous experiment.

## Build only (researcher has NOT installed this AEX)

    cmake -S "D:\Developer\ShapeLayerAE\labs\native_tdb_registration_disposable" -B "D:\Developer\ShapeLayerAE\build\native_tdb_registration_disposable" -G "Visual Studio 17 2022" -A x64
    cmake --build "D:\Developer\ShapeLayerAE\build\native_tdb_registration_disposable" --config Release

Output:
D:\Developer\ShapeLayerAE\build\native_tdb_registration_disposable\Release\CNLPrivateTDBDisposable.aex

After an explicitly authorized disposable user test: inspect stage log and clean shutdown before declaring any success. No Adobe host process was controlled by the researcher.

## Evidence and scope

AEIG F-VECTOR-025..031, EXP-SHAPE-027..030; static ABI + MSVC cross-module callback mock. Does not provide host-native layer output/editor/renderer. Failure is an informative result, not a reason to force the operation.


## v2 IMPORTANT (2026-10-12): previous experimental AEX is invalid; DO NOT RUN IT

Audit discovered that the original experimental Creator callback mistakenly used (bool,unsigned,unsigned) where the native Adobe MSVC std::function signature actually requires (bool,unsigned int,bool). Old source also erased the native class pointers to void*. This is a material C++ ABI mismatch: do not attempt an old build of this experiment.

The corrected project compiles against exact native C++ class names, with the full std::function parameter-type suffix shown to match both installed AE2025 and AE2026 RegisterFactoryFunc exports through a separate MSVC COFF symbol verification. This reduces ABI uncertainty, but DOES NOT establish safe private C++ object layout, allocator, host registry unload or project shutdown.

The previous no-active-layer gate was insufficient. This build now uses the SAME read-only, public SDK NativeProjectSafety.h as the safe host-probe AEX: exactly one non-dirty, empty project, no non-root active item or project content, empty render queue, fail-closed. Run ONLY the safe AEX v2 first and inspect disposable_project_gate_pass; DO NOT run this mutation AEX in daily AE.

New MatchName includes process id/tick for collision resistance. Creator invocation count is logged via a plugin-static LONG (no stack-captured callback references). After registering (never yet attempted), automatic unregister is best-effort and does not certify rollback.

Even with all gates this remains HIGH RISK and cannot be certified safe; only consider a separate explicitly authorized, isolated disposable AE environment. No private registrar function has been called in an AE host by this research.

## v3 (2026-10-12): fail-closed runtime entrypoint fingerprints and UNSAVED project guard

This supersedes prior v2 AEX binaries. The shared public-only disposable-project gate now rejects even a clean, EMPTY project if the public AEGP_GetProjectPath returns a non-empty UTF-16 path. AEGP project path handles are locked, unlocked, and released through MemorySuite1; missing or failed SDK operations reject the test. Both AEX files have been rebuilt after this shared change.

The dangerous AEX now checks 16 code bytes at EACH of 5 private function entrypoints (getter, MatchName constructor, ParamPathStream creator, registrar, unregistrar), against both exact pinned TDB.dll versions. These values were extracted from the actual PE export RVAs with tools/audit_tdb_native_entry_fingerprints.py. They are compared against live executable memory, not only the on-disk DLL hash. Discrepancies or uninspectable pages cause refusal.

Other v3 changes:
- AEGP_GetActiveLayer API errors also fail closed (previous logic ignored an error).
- Consumes the existing explicit one-shot confirmation, then checks public project state AGAIN before the first private call.
- Uses an atomic, per-AEX-module one-attempt latch; after any private attempt, further clicks are refused for this loaded AEX instance.
- Records creator invocation count and post-attempt public project state. The audit log explicitly writes private_registry_rollback_proven=0 even if unregister returned success.
- The static AEX verifier checks all five fingerprints against the actual installed, pinned 2025 and 2026 PE binaries; static verification is NOT an AE runtime test.

Build output: build/native_tdb_registration_disposable/Release/CNLPrivateTDBDisposable.aex.
**DO NOT INSTALL OR RUN THIS MUTATING AEX YET.** The 2026-10-12 v3 build is compiled and statically verified ONLY. Runtime acceptance, canonical object cleanup, dangling callback safety, native editing and renderer integration remain UNPROVEN. Entry fingerprints cannot prevent a crash caused by a correct-but-unsupported internal operation. The public project gate does not isolate global host memory. The latch does not persist across DLL reload and cannot compensate for an unsafe registrar.
