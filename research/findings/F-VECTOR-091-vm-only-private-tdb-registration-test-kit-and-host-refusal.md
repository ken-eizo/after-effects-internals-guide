---
date: 2026-10-14
status: PASS safe host-side VM-only kit packaging, manifest verification, and physical-host fail-closed tests; BLOCKED actual native registration due to unavailable isolated Windows guest
evidence: E2-L installed OS and VirtualBox inventory, VM model and storage read-only enumeration; x64 C++ dangerous AEX static verifier; two strict PowerShell guest-only guards; source kit ZIP SHA; tests intentionally refuse physical host
---
# F-VECTOR-091 — Disposable Windows VM gate and isolated private TDB registration experiment readiness

## User authorization and safety requirement

The user explicitly authorized experiments using Adobe private APIs with potential AE crashes, **provided that they occur inside a disposable isolated environment**. Authorization did not extend to modifying the normal physical machine's installed AE, user project or Adobe binaries. This finding therefore treats the existence of a genuine independent, snapshot-revertible Windows guest as a **mandatory launch condition**, not an optional preference.

## Actual host environment (read-only verified)

- Physical host is Windows 10 Home build 19045, with Microsoft hypervisor presence. **HypervisorPresent does not indicate the host OS is itself a guest.**
- Windows Sandbox executable not present; Windows Home edition is not supported by Windows Sandbox per Microsoft official documentation: https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/ .
- Oracle VirtualBox CLI exists, but it is version **5.2.20r125813 (2018)**. The sole existing guest `default` is **Linux boot2docker 64-bit**, powered off since 2024, not a Windows AE test guest. The existing VM was NOT started, cloned, modified or used.
- Hyper-V compatibility support was added/improved as an experimental integration in VirtualBox 6.0: https://docs.oracle.com/en/virtualization/virtualbox/6.0/relnotes/hyperv-integ.html ; VirtualBox 5.2 is therefore not a reliable assumed working Windows VM engine on this Hyper-V-active host.
- Local Windows install ISO/VHD/VMDK candidates were not found in the inspected customary download/VM directories. This does **not** prove no ISO exists elsewhere on the drives.
- Guest OS installation, Adobe 2026 inside guest, separate guest disk, snapshot and network-isolated guest are all **absent / unverified**.

## VM-only test kit created on the host but NOT installed into AE

Local research kit:

`D:/Developer/ShapeLayerAE/labs/native_tdb_registration_disposable/VM_Only_Test_Kit/`

ZIP deliverable on user-controlled PC:

`D:/Developer/ShapeLayerAE/results/CNLPrivateTDB_VM_ONLY_20261014.zip`

ZIP SHA-256 `B881BC258B0CC19DB694B2FEA056C86C07AC27744AD10D85B47D3F9EA6789D2A`, 23,999 bytes, 5 files:

1. `CNLPrivateTDBDisposable.aex` — SHA256 `C91FFCE77BE481A394C243C0DE64568487D3F24E5864CBBA9376EAF1500B5622`, 36,864 bytes, prior MSVC native-private ABI experiment. STATIC verified, NEVER host executed.
2. `VM_Preflight_ReadOnly.ps1` — fail-closed read-only checks. Requires recognized VM guest manufacturer/model, virtual guest hard disk, ZIP extracted on guest local `C:\CNL_VM_LAB`, 64-bit Windows, all NICs disconnected, no mapped host shares, separately installed guest AE2026, zero live AE processes, valid guest plug-in folder, and explicit known-physical-model denial.
3. `VM_Stage_And_Run_Manual.ps1` — requires `-SnapshotConfirmed` plus exact `-RiskAccepted I_ACCEPT_PRIVATE_REGISTRY_CRASH_RISK`. Runs child PowerShell preflight and **refuses** unless exit code zero. Verifies AEX SHA, installs only into the guest's `Plug-ins\CNL_DISPOSABLE_PRIVATE_REGISTRY`, writes one-shot confirmation, starts guest AE. **Never programmatically clicks the private registration command**. Manual menu click is separate; only an empty unsaved project is allowed. Journal remains inside disposable VM.
4. `MANIFEST_SHA256.txt` — inner file hashes.
5. `VM_ONLY_README_JP.md` — Japanese instructions, snapshot/network/share requirements and risk boundaries.

Local (not published) host safety verifier:

`D:/Developer/ShapeLayerAE/labs/native_tdb_registration_disposable/verify_vm_only_kit.py`

It validated all five ZIP members' hashes, the private AEX exact SHA, and executed **negative tests only** on the user's physical host:
- `VM_Preflight_ReadOnly.ps1` exited **20 REFUSED**, correctly identifying the physical PC as not being a qualified VM.
- `VM_Stage_And_Run_Manual.ps1 -SnapshotConfirmed -RiskAccepted ...` explicitly refused the physical root location before copying or executing an AEX.
- All normal AE plugin directories remained free of the experimental AEX, and no Adobe process was launched by the test.

## What has NOT happened

**No private TDB registry function has been invoked inside After Effects.** No new `CNL:` host-native Stream was attached to the standard AE Timeline. The current user AE2026 plugin `CNLNativeShapeLayer.aex` remains the safe read-only/CNL-independent build. Build and mock ABI PASS cannot satisfy the native Timeline custom-type acceptance gates.

Even a disposable VM register/unregister PASS, if later reached, would prove **only** experimental creator acceptance, not parent canonical UILayout, native edits, keyframes, AE Undo, project archive, renderer, Pen/gizmos or cross-platform product readiness.

## Next action gate

Acquire or install a separate **Windows guest** and compatible VM tool, with AE2026 independently installed/activated in guest and a saved pre-test snapshot. Remove all host shared folders, disable virtual NIC and run the guest preflight. The user may then trigger the single-shot register experiment manually in disposable AE and provide its stage log. **Do not substitute a separate AE process on the physical host** for the requested isolated environment; global caches, preferences, plugin state and credentials can still be shared across processes.

Status: `WAITING_FOR_ISOLATED_WINDOWS_GUEST`, product: `NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM`.
