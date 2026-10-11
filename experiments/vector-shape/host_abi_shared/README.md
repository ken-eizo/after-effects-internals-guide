# Shared public-SDK project isolation gate

Original C++17 header NativeProjectSafety.h; includes only official Adobe AEGP suites, no private code.

Used by BOTH research AEX modules:
- native-vector-host-probe-lab (READ ONLY, safe first-pass preflight)
- native-tdb-registration-disposable-lab (HIGH RISK, still untested)

CNL_CheckDisposableProject requires:
- exactly one valid AE project,
- no dirty state,
- no active non-root project item,
- project enumeration has no non-root items,
- render queue contains zero items,
- all public AEGP SDK reads succeed.

The function never creates a layer, edits project data, or calls any private TDB/BEE/AGM function.

IMPORTANT: A PASS indicates only a set of host-public state predicates. It does NOT guarantee sandbox isolation, protect against native C++ memory corruption, prove no useful application-level settings exist, or certify rollback of private TDB factory registration.

The only completed real-host proof remains the earlier safe AEX v1 report; this additional gate in v2 requires separate user-controlled testing inside AE.
