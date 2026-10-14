"""Read-only, scoped native Stream/Layer provider audit of installed Adobe SDK25.6.
This deliberately proves only absence in sampled PUBLIC headers; it does not
prove Adobe has no private/internal/partner extensions.
"""
from pathlib import Path
import re,json,hashlib,datetime,collections
sdk=Path(r"E:\ae25.6_61.64bit.AfterEffectsSDK\Examples\Headers")
root=Path(r"D:\Developer\After Effects Internals Guide")
headers=sorted(list(sdk.rglob("*.h"))+list(sdk.rglob("*.hpp")))
assert len(headers)>=65
texts={str(p.relative_to(sdk)):p.read_text(encoding="utf-8",errors="replace") for p in headers}
general=texts["AE_GeneralPlug.h"]
def extract_struct(n):
 m=re.search(r"typedef\s+struct\s+"+re.escape(n)+r"\s*{(?P<body>.*?)}\s*"+re.escape(n)+r"\s*;",general,re.S)
 if m is None:raise AssertionError("Suite missing: "+n)
 return m["body"]
register=extract_struct("AEGP_RegisterSuite5")
regmethods=re.findall(r"\(\s*\*\s*(AEGP_[A-Za-z0-9_]+)\s*\)",register)
assert len(regmethods)==12,(len(regmethods),regmethods)
assert "AEGP_RegisterArtisan" in regmethods and "AEGP_RegisterIO" in regmethods
assert not any("NativeStream" in s or "LayerProvider" in s for s in regmethods)
# Public factories provide existing AE layers and in-parent children; no custom C++ TDB factory.
dynamic=extract_struct("AEGP_DynamicStreamSuite4")
dynamicmethods=re.findall(r"\(\s*\*\s*(AEGP_[A-Za-z0-9_]+)\s*\)",dynamic)
assert "AEGP_AddStream" in dynamicmethods and "AEGP_CanAddStream" in dynamicmethods
positive_api_terms=["AEGP_AddStream","AEGP_CanAddStream","AEGP_CreateVectorLayerInComp",
                    "AEGP_RegisterArtisan","AEGP_RegisterIO","AEGP_RegisterTracker"]
private_tokens=[r"\bTDB_StreamBase\b",r"\bTDB_StreamFactory\b",r"\bTDB_ScRegisterStreams\b",
  r"\bBEE_Layer\b",r"\bBEE_PaintAtom\b",r"\bRegisterNativeStream\b",
  r"\bRegisterLayerType\b",r"\bRegisterStreamFactory\b",r"\bRegisterNativeLayer\b"]
found_private={}
for pattern in private_tokens:
 occ=[{"file":name,"line":text[:m.start()].count("\n")+1} for name,text in texts.items() for m in re.finditer(pattern,text)]
 found_private[pattern]=occ
assert all(not x for x in found_private.values()),"Public headers include a matching private/registrar token; verify before report!"
public_locations={}
for term in positive_api_terms:
 matches=[{"file":name,"line":t[:m.start()].count("\n")+1} for name,t in texts.items() for m in re.finditer(re.escape(term),t)]
 assert matches,(term,'missing from installed headers')
 public_locations[term]=matches
result={
 "audit_time":"2026-10-14","scope":"Installed Adobe After Effects SDK 25.6 Examples/Headers only",
 "sdk_root":str(sdk),"scanned_header_count":len(headers),
 "scanned_file_hashes":{n:hashlib.sha256(t.encode('utf-8')).hexdigest() for n,t in texts.items()},
 "AEGP_RegisterSuite5_methods":regmethods,"register_method_count":len(regmethods),
 "AEGP_DynamicStreamSuite4_methods":dynamicmethods,
 "positive_api_locations":public_locations,
 "private_or_external_provider_symbols_absent_in_scanned_headers":{k:len(v)==0 for k,v in found_private.items()},
 "third_party_native_stream_type_registration_documented_here":False,
 "third_party_arbitrary_parent_canonical_layout_registration_documented_here":False,
 "third_party_new_BEE_Layer_class_registration_documented_here":False,
 "interpretation_limit":"ABSENCE IN THESE 70 PUBLIC HEADERS ONLY; does not preclude Adobe private/partner ABI or future releases. AEGP_AddStream manipulates existing host-registered type; it does not declare a new TDB class.",
 "host_project_modified":False
}
out=root/"datasets"/"ae25_6_public_native_stream_provider_api_scope_audit.json"
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PASS scanned",len(headers),"public headers")
print("RegisterSuite5 methods",len(regmethods),regmethods)
print("DynamicStreamSuite4 methods",len(dynamicmethods),"contains CanAddStream and AddStream")
print("Unknown native factory/provider class registration:", "NOT EXPOSED in installed public SDK headers")
print("dataset:",out)
