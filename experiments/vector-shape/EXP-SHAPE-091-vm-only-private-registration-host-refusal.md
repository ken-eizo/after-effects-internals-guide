# EXP-SHAPE-091 — VM-only private TDB registration preparation and physical-host hard rejection

**Status: PASS on preflight/kit static and host-negative tests, BLOCKED on actual private ABI host mutation.**

User explicitly approved a crash-tolerant, disposable, isolated **Windows VM** experiment. Local host audit found Windows 10 Home (no supported Windows Sandbox), VirtualBox 5.2.20 with only a boot2docker Linux VM, and no installed/verified independent Windows AE guest. The physical host is therefore *not* an eligible execution environment.

A 5-file private test kit exists **only on the user's local disk**:
`D:\Developer\ShapeLayerAE\results\CNLPrivateTDB_VM_ONLY_20261014.zip`

- ZIP SHA256: `B881BC258B0CC19DB694B2FEA056C86C07AC27744AD10D85B47D3F9EA6789D2A`.
- Contains `CNLPrivateTDBDisposable.aex` (36,864 bytes, SHA256 `C91FFCE77BE481A394C243C0DE64568487D3F24E5864CBBA9376EAF1500B5622`), fail-closed VM guest preflight, VM-only manual launcher, SHA manifest, Japanese README.
- PowerShell AST static parse: **2/2 PASS**.
- All five zipped members and SHA manifest: **PASS**.
- Physical-host negative test: `VM_Preflight_ReadOnly.ps1` **REFUSED exit 20**.
- Physical-host negative test: `VM_Stage_And_Run_Manual.ps1` **REFUSED before plugin copy or AE launch**.
- No experimental `CNLPrivateTDBDisposable.aex` installed to user's live AE; no private ABI calls executed by this experiment.
- Existing C++ mock native callback ABI tests: 1/1 each; MSVC real decorated signature comparison PASS.
- Windows guest has not been created or run.

Local verifier not copied into the public repo (contains explicit physical-host refusal): `D:/Developer/ShapeLayerAE/labs/native_tdb_registration_disposable/verify_vm_only_kit.py`.

The ZIP is **not published** to a public GitHub release or repo because it contains a knowingly hazardous private Adobe ABI mutation AEX, intended only for isolated testing by the owner.

Blocked conditions: independent Windows VM + guest-installed AE2026 + disk snapshot + network off + host shared folders disconnected. User must meet them before the next experiment.

Finding: `research/findings/F-VECTOR-091-vm-only-private-tdb-registration-test-kit-and-host-refusal.md`.
