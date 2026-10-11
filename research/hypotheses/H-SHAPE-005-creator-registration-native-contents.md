---
status: hypothesis
last_verified: 2026-10-11
evidence: H + E2-L + E2-X
versions: AE 2025/2026 internal binary and AE2026 read-only AEGP host probe
---
# H-SHAPE-005 — A third-party native stream type can participate in a built-in vector group through TDB creator registration

## Mechanistic hypothesis

H-OPEN: `Get_AE_StreamFactory` exposes a host-owned factory with a callback registry, `TDB_ScRegisterStreams::Register` registers a `TDB_MatchName`/creator, and `BEE_VectorStream::VectorsStreamGroup::CanStore` permits new shapes via prefix match. If a plug-in installed a valid creator with a new `ADBE Vector Shape - ...` match name, an existing native indexed group **might** accept and instantiate it. This would be a first step, **not** independent owner/Timeline/renderer parity.

H-CLOSED: Factory callbacks require private layout, module initializer linkage, canonical instance setup, proprietary class identity, serialization registration, and guarded host lifecycle. Even if internal Adobe modules use the creator registry, external AEGP plugins may not meet those contracts. A mere dynamic LoadLibrary/GetProcAddress call is no proof of safe registration.

H-OWNER: Even if a valid custom child stream can be created inside an existing native Shape Layer, an independent Effect-owned Contents tree may be blocked by BEE_VectorLayer/TDB project-owner dispatch. This is a separate success gate.

H-RENDER: Even if custom native stream type can be registered, AE's `PopulateVectorArt` may dispatch only on a closed set of built-in vector stream subclasses; this blocks actual native vector rendering.

## Stepwise falsifiable tests

1. Read-only native `AEGP_CanAddStream` for syntactically valid **unregistered** Vector Shape/Graphic/Filter prefixed names against real Contents and Effects. Confirm unknown names were not added.
2. Explicitly opt-in to read-only invocation of pinned private `Get_AE_StreamFactory()`; record only nonnull boolean and module/export/fingerprint state; do not dereference pointer.
3. Reconstruct factory ownership and canonical prototype creation from offline disassembly of `TDB_StreamFactory::RegisterFactoryFunc` and `CreateStream`.
4. Only in an isolated disposable host and after ABI/ownership contracts are understood, test controlled registration of a new type; log unloading, saving, Undo and rendering separately.
5. Distinguish registering into an **existing** native Shape Layer (partial breakthrough) from creating a separate plugin-owned native Contents tree (core objective).

If an unknown prefix gets CanAdd=true but no registered factory exists, that is evidence of **schema admission separate from construction**, not evidence of full plugin extensibility.

## Safety and evidence discipline

The current public Read-Only Factory Getter probe is **compiled only** and never auto-invokes a private symbol on startup. Unknown prefix and factory getter tests have distinct explicit user commands. All actual registrations/modifications remain absent from code and host execution. A factory callback could create dangling vtables/function closures on unload; require isolation/version pinning and safe teardown before any future experiment.
