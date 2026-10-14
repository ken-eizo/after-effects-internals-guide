# EXP-SHAPE-090 — Dangerous private Adobe TDB registrar experiment revalidated ONLY offline

**PASS:** static PE/PiPL, x64 MSVC Release AEX build, private ABI symbol and live code fingerprint guard source present. SHA256: `c91ffce77be481a394c243c0de64568487d3f24e5864cbba9376eaf1500b5622`.

**NOT PERFORMED:** loading `CNLPrivateTDBDisposable.aex` into a real AE host and mutating `TDB_StreamFactory`. This AEX was intentionally not installed in any normal AE plug-in folder. Without separate explicit risk consent and true isolated disposable host, run remains BLOCKED. Successful registrar return, if ever achieved, is not equivalent to new host-owned Timeline/Contents.

Source: `D:/Developer/ShapeLayerAE/labs/native_tdb_registration_disposable`.

Verify WITHOUT host load:
```powershell
python D:\Developer\ShapeLayerAE\labs\native_tdb_registration_disposable\verify_no_host_load.py
cmake --build D:\Developer\ShapeLayerAE\build\native_tdb_registration_disposable --config Release
```

Details F-VECTOR-090 and existing source README safety warnings.
