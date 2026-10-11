"""EXE/DLL C++ callback ABI model verifier. This does not link to or load AE."""
from pathlib import Path
import pefile,subprocess,hashlib,json
base=Path(r"D:\Developer\ShapeLayerAE")
root=base/"build/tdb_callback_abi_mock/Release"
host=root/"TDBNativeCallbackHostMock.dll"
client=root/"TDBNativeCallbackClientTest.exe"
assert host.is_file() and client.is_file()
pe=pefile.PE(str(host))
exports={i.name.decode(errors="replace") for i in pe.DIRECTORY_ENTRY_EXPORT.symbols if i.name}
expected={"MockRegister","MockUnregister","MockIsRegistered","MockHasCanonical",
          "MockCount","MockCanonicalLayoutCalls","MockStreamDestructors"}
assert expected==exports,(expected-exports,exports-expected)
imports={i.dll.decode(errors="replace").lower() for i in pe.DIRECTORY_ENTRY_IMPORT}
assert "bee.dll" not in imports and "tdb.dll" not in imports
p=subprocess.run(["ctest","--test-dir",str(base/"build/tdb_callback_abi_mock"),
                  "-C","Release","--output-on-failure"],
                 capture_output=True,text=True,errors="replace")
assert p.returncode==0,(p.stdout,p.stderr)
actual=subprocess.run([str(client)],capture_output=True,text=True,errors="replace")
assert actual.returncode==0,actual.stderr
assert actual.stdout.startswith("PASS cross-EXE/DLL MSVC")
receipt={
"experiment":"EXP-SHAPE-029","date":"2026-10-12","status":"pass-cross-module-MSVC-mock",
"evidence":"E2-B compiled Windows x64 DLL+separate EXE",
"host_mock_file":str(host),"client_test_file":str(client),
"host_mock_SHA256":hashlib.sha256(host.read_bytes()).hexdigest(),
"client_test_SHA256":hashlib.sha256(client.read_bytes()).hexdigest(),
"host_DLL_exports":sorted(exports),
"ctest":"PASS","client_stdout":actual.stdout.strip(),
"actually_called_Adobe_TDB_registry":False,
"actually_created_AE_native_type":False,
"registered_TDB_StreamBase_in_real_host":False,
"warning":"This only verifies corresponding C++ std::function inter-module protocol and cleanup in a NON-Adobe toy host; it does not validate Adobe C++ class ABI or lifecycle."
}
dst=base/"results/tdb_callback_abi_mock_receipt_20261012.json"
dst.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("PASS real x64 DLL/EXE std::function copy/eager canonical/explicit unregister model; NOT Adobe")
print("SAVED",dst)
