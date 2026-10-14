---
status: internal-implementation-reference
last_verified: 2026-10-15
evidence: E2-L + E0-H + H
versions: Windows AE2025/2026 native TDB; Adobe SDK25.6 public API comparison
---

# TDB_IndexedStreamGroup::RemoveStream — Detaching Native Child Properties

The native TDB_IndexedStreamGroup has a C++ method named **RemoveStream(index)** which returns a TDB_StreamBase pointer. It removes an existing child from an indexed native group. This is **private Adobe implementation**, not a supported third-party AEGP function.

The public SDK operation with similar user intent is AEGP_DeleteStream, accessed through AEGP_DynamicStreamSuite4. The public API operates on StreamRefH and is **undoable** under its documented constraints; its handle disposal contract and host command routing must not be conflated with a raw private TDB_StreamBase pointer.

## The native parent pointer

In the examined TDB_StreamBase object layout for both Windows AE2025 and 2026, the native parent pointer is at **this +0x20**.

- TDB_StreamBase::SetParent(parent) directly stores its argument into that field, and when non-null invokes NotifyParentsStreamStored.
- TDB_IndexedStreamGroup::RemoveStream(index) directly writes zero into the same field on the detached child.
- TDB_IndexedStreamGroup::RemoveChild(child) has its own direct parent-pointer-zeroing success path. It returns a boolean and performs additional lookup and cache management.

These statements are cross-checked in the original native code. The private offset is not a stable SDK ABI and cannot be used as a replacement for public StreamRef APIs.

## RemoveStream operational sequence

~~~text
TDB_IndexedStreamGroup::RemoveStream(index)
  ├─ validate index against virtual GetNumStreams (+0x168)
  ├─ obtain original child via virtual indexed getter (+0x178)
  ├─ retain child TDB_StreamBase*
  ├─ host change notifications / bookkeeping
  ├─ remove pointer from native child vector
  ├─ UpdateReverseIndexVector(index)
  ├─ invalidate/update affected indexed entries
  ├─ child->parent = nullptr        [child+0x20 = 0]
  └─ return original child pointer [same object]
~~~

The key point: **removal from the group is not necessarily destruction of the child object**. On the observed success path this method returns the same raw pointer it obtained from the group; no deleting destructor on that object is called in the method's visible normal branch. Its subsequent C++ lifetime depends on the caller.

The function also emits internal notifications/events whose payload types and ordering have not yet been fully resolved. This summary must not be understood to describe every failure branch, all destruction contexts, or Undo retention.

## Verified code locations

| Native code | AE 2025 RVA | AE 2026 RVA |
| --- | --- | --- |
| RemoveStream | 0x3E0C0 | 0x3EB90 |
| SetParent writes child+0x20 | 0x3F0EA | 0x3FB2A |
| Original child obtained | 0x3E113 | 0x3EBDA |
| Child array shortened by pointer width | 0x3E1B7 | 0x3EC68 |
| Reverse-index update | 0x3E1D6 | 0x3EC85 |
| Child parent cleared | 0x3E228 | 0x3ECDA |
| Original child returned | 0x3E29E | 0x3ED3F |

The exact sequence was verified in both SHA-pinned installed TDB DLL builds; see F-VECTOR-099 and the accompanying machine-readable dataset.

## Related operations and ownership

| Operation | Native role | Ownership observation |
| --- | --- | --- |
| TDB_IndexedStreamGroup::InsertStream | Accept/attach a child, set parent and cached path state | Incoming native smart pointer is relinquished after successful insertion |
| TDB_IndexedStreamGroup::RemoveStream | Detach by index | Returns original raw Stream pointer |
| TDB_IndexedStreamGroup::RemoveChild | Remove a specified member | Returns boolean; separate cache/path handling |
| BEE_CmdRemoveIndexedGroupEntry | Host-native command wrapper | Uses BEE UndoContext and BEE_DoCommand, not a raw public delete |
| AEGP_DeleteStream | Documented third-party AEGP structural edit | Undoable; caller must dispose public StreamRefH |

No cross-DLL private call should be attempted from a regular third-party AEX based on this table.

## Why the lifetime boundary matters

A foreign C++ Stream subclass would have virtual methods and destructor code in the module that implemented it. If the host or an Undo task retains a pointer after it has been detached, unloading that module would leave dangling virtual function pointers. Conversely, prematurely destroying a detached object while a task still holds it can cause use-after-free.

**Not yet established:** the identity of the owner that receives the returned pointer for every command, whether the Undo task retains the original object or a clone, the method ultimately responsible for deleting detached objects, the exact object lifetime during Undo/Redo and macOS ABI.

For supported third-party code use AEGP's documented APIs. See [Native Structural Commands and Undo](structural-command-undo.md), [Indexed Group Insertion](indexed-group-insertion.md), [Stream Object Model](stream-object-model.md), and [AEGP DynamicStreamSuite4](../../host-integration/cpp-sdk/aegps/dynamic-stream-suite.md).
