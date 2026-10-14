"""Audit supported AE SDK 25.6 native layer extension surface (offline).
No host execution, private API calls, or vendor binary modification.
"""
from pathlib import Path
import hashlib,json,re
HEADER=Path(r"E:\ae25.6_61.64bit.AfterEffectsSDK\Examples\Headers\AE_GeneralPlug.h")
ROOT=Path(r"D:\Developer\After Effects Internals Guide")
text=HEADER.read_text(encoding="utf-8-sig",errors="replace")
def line(symbol):
 m=re.search(r"\b"+re.escape(symbol)+r"\b",text)
 assert m is not None,symbol
 return text.count("\n",0,m.start())+1
def suite(name):
 m=re.search(r"typedef\s+struct\s+"+name+r"\s*\{(?P<body>.*?)\}\s*"+name+r"\s*;",text,re.S)
 assert m,name
 return m.group("body"),text.count("\n",0,m.start("body"))
body,base=suite("AEGP_RegisterSuite5")
registration=[]
for m in re.finditer(r"\(\s*\*\s*(AEGP_Register\w+)\s*\)",body):
 registration.append({"name":m.group(1),"header_line":base+body.count("\n",0,m.start())+1})
expected={"AEGP_RegisterCommandHook","AEGP_RegisterUpdateMenuHook","AEGP_RegisterDeathHook","AEGP_RegisterVersionHook",
"AEGP_RegisterAboutStringHook","AEGP_RegisterAboutHook","AEGP_RegisterArtisan","AEGP_RegisterIO",
"AEGP_RegisterIdleHook","AEGP_RegisterTracker","AEGP_RegisterInteractiveArtisan",
"AEGP_RegisterPresetLocalizationString"}
actual={x["name"] for x in registration}
assert actual==expected,(actual-expected,expected-actual)
assert not any(any(needle in x for needle in ("Layer","Stream","NativeProperty","Evaluator")) for x in actual)
creators=["AEGP_CreateTextLayerInComp","AEGP_CreateBoxTextLayerInComp",
          "AEGP_CreateVectorLayerInComp","AEGP_AddLayer","AEGP_CreateCameraInComp","AEGP_CreateLightInComp"]
for name in creators:assert re.search(r"\(\s*\*"+name+r"\s*\)",text),name
m=re.search(r"\(\s*\*AEGP_CreateVectorLayerInComp\s*\)\s*\((.*?)\)\s*;",text,re.S)
assert m
prototype=" ".join(m.group(1).split())
assert "AEGP_CompH" in prototype and "AEGP_LayerH" in prototype
assert "creator" not in prototype.lower() and "type" not in prototype.lower()
object_type=re.search(r"enum\s*\{(\s*AEGP_ObjectType_NONE.*?)\}\s*;\s*typedef\s+A_long\s+AEGP_ObjectType",text,re.S)
assert object_type
enumerants=re.findall(r"\bAEGP_ObjectType_\w+\b",object_type.group(1))
must_have=["AEGP_ObjectType_AV","AEGP_ObjectType_LIGHT","AEGP_ObjectType_CAMERA",
           "AEGP_ObjectType_TEXT","AEGP_ObjectType_VECTOR","AEGP_ObjectType_3D_MODEL"]
assert all(n in enumerants for n in must_have)
for name in ("AEGP_AddStream","AEGP_CanAddStream","AEGP_Menu_NEW","AEGP_InsertMenuCommand"):assert name in text,name
result={"classification":"static audit of installed public SDK header only; no global impossibility claim",
"header_sha256":hashlib.sha256(HEADER.read_bytes()).hexdigest(),"header":str(HEADER),
"register_suite":{"name":"AEGP_RegisterSuite5","functions":registration,"has_custom_layer_class_registration":False,
"has_custom_tdb_stream_type_registration":False},
"built_in_layer_creator":{"name":"AEGP_CreateVectorLayerInComp","line":line("AEGP_CreateVectorLayerInComp"),
"signature":prototype,"accepts_custom_layer_type":False},
"object_type_enum":{"line":line("AEGP_ObjectType_NONE"),"enumerants":enumerants},
"dynamic_stream_operations":{"can_add_line":line("AEGP_CanAddStream"),"add_line":line("AEGP_AddStream")},
"menu_command":{"menu_new_line":line("AEGP_Menu_NEW"),"insert_command_line":line("AEGP_InsertMenuCommand")},
"external_private_owner_extensibility":"not established by this inspection"}
path=ROOT/"datasets"/"ae-public-sdk-native-layer-extension-surface-25-6.json"
path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("PASS SDK header",HEADER)
print("REGISTER_SUITES",len(registration),"methods",",".join(x["name"] for x in registration))
print("BUILTIN_VECTOR_LAYER_CREATE",prototype)
print("OBJECT_TYPES",",".join(enumerants))
print("OUTPUT",path)
