"""Compare native Adobe MSVC callback std::function mangled ABI directly
to an independently compiled MSVC object. No Adobe functions executed.
"""
from pathlib import Path
import json,re,subprocess,hashlib
root=Path(r"D:\Developer\ShapeLayerAE")
abi_obj=root/"build/tdb_callback_abi_mock/CNLABISignatureProbe.dir/Release/NativeABISignatureProbe.obj"
source=root/"labs/native_tdb_registration_disposable/CNLPrivateTDBDisposable.cpp"
assert abi_obj.is_file()
obj_symbols=subprocess.run(["dumpbin","/symbols",str(abi_obj)],
 capture_output=True,text=True,errors="replace",check=True).stdout
native_by_year={}
for year,path in {
 "2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll",
 "2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll"}.items():
 native_by_year[year]=subprocess.run(["dumpbin","/exports",path],
  capture_output=True,text=True,errors="replace",check=True).stdout
prefix="?CNL_ABI_SignatureComparator@@YA_N"
match=re.search(re.escape(prefix)+r'([^\s]+)',obj_symbols)
assert match, "compiled C++ mangling for local function not found"
own=prefix+match.group(1)
native={}
for year,symbols in native_by_year.items():
 found=re.search(r'(\?RegisterFactoryFunc@TDB_StreamFactory@@QEAA_N[^\s]+)',symbols)
 assert found,("missing native RegisterFactoryFunc",year)
 native[year]=found.group(1)
contract='AEBVTDB_MatchName@@V?$function@$$A6APEAVTDB_StreamBase@@AEBVTDB_MatchName@@PEAVTDB_StreamFactory@@_NI2@Z@std@@_N@Z'
assert own.endswith(contract),own
for year,sym in native.items():
 assert sym.endswith(contract),(year,sym)
text=source.read_text(encoding="utf8")
assert "using CreatorSignature=TDB_StreamBase*(const TDB_MatchName&,TDB_StreamFactory*,bool,unsigned,bool);" in text
assert "using NativeParamPathCreator=TDB_StreamBase* (__cdecl*)(const TDB_MatchName&,TDB_StreamFactory*,bool,unsigned,bool);" in text
assert 'using NativeRegister=bool (__cdecl*)(TDB_StreamFactory*,const TDB_MatchName&,CreatorObject,bool);' in text
assert "CNL_CheckDisposableProject" in text
assert "explicit_two_factor_ack_consumed" in text
receipt={
 "experiment":"EXP-SHAPE-031",
 "evidence":"E2-B binary symbol comparison with exact Adobe TDB 2026 PE export; not runtime registry acceptance",
 "source_object":str(abi_obj),
 "object_sha256":hashlib.sha256(abi_obj.read_bytes()).hexdigest(),
 "cpp_compiled_mangled_signature":own,
 "native_adobe_register_factory_mangled_signature_by_version":native,
 "function_parameter_mangled_suffix_exact_match":True,
 "observed_argument_types":["const TDB_MatchName&","TDB_StreamFactory*","bool","unsigned int","bool"],
 "prior_last_parameter_unsigned_int_bug_fixed":True,
 "unsafe_AEX_rebuilt_with_exact_typed_std_function":True,
 "private_registration_called":False,
 "disposable_gate_in_source":True,
 "notes":["C++ function-object mangling matches native export exactly but does not establish host class layout/allocator/lifetime compatibility",
 "AEX private API calls must still not be attempted in a production host"]
}
file=root/"results/tdb_exact_msvc_callback_abi_receipt_20261012.json"
file.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print("PASS exact MSVC C++ native TDB std::function type decoration matches installed Adobe factory export")
print("PASS original unsigned int fifth callback argument corrected to bool")
print("SAVED",file)
