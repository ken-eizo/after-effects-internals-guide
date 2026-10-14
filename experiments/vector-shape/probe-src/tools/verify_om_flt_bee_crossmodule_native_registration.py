"""Verify actual native OM / FLT / BEE module boot registration paths across AE2025/26.
PURE static Windows PE reads and disassembly; never load DLLs or invoke private APIs.
"""
from pathlib import Path
import pefile,capstone,subprocess,re,json,hashlib
ROOTS={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files"),
       "2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")}
EXPECTED_FLT={"2025":["EFFECT_PATH_PARAM","EFFECT_OPACITY","MASK","MASKS_PARADE",
                      "FORCE_CPU_GPU","EFFECT_BUILT_IN_PARAMS"],
              "2026":["EFFECT_PATH_PARAM","EFFECT_OPACITY","EFFECT_BLENDMODE","MASK",
                      "MASKS_PARADE","FORCE_CPU_GPU","EFFECT_BUILT_IN_PARAMS"]}
CS=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);CS.detail=True
def module(path):
 p=pefile.PE(str(path));base=p.OPTIONAL_HEADER.ImageBase
 exp={}
 txt=subprocess.run(["dumpbin","/exports",str(path)],text=True,capture_output=True,errors="replace",check=True).stdout
 for ln in txt.splitlines():
  m=re.match(r"\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\S+)",ln)
  if m:exp[int(m.group(1),16)]=m.group(2)
 iat={i.address-base:(d.dll.decode(errors="replace").lower(),i.name.decode(errors="replace") if i.name else "")
      for d in p.DIRECTORY_ENTRY_IMPORT for i in d.imports}
 pdata={x.struct.BeginAddress:x.struct.EndAddress for x in p.DIRECTORY_ENTRY_EXCEPTION}
 return {"pe":p,"base":base,"exp":exp,"iat":iat,"pdata":pdata,"sha":hashlib.sha256(path.read_bytes()).hexdigest()}
def symbol(m,prefix):
 vals=[r for r,n in m["exp"].items() if n.startswith(prefix)]
 assert len(vals)==1,(prefix,vals)
 return vals[0]
def insns(m,r):
 end=m["pdata"][r]
 return list(CS.disasm(m["pe"].get_data(r,end-r),m["base"]+r))
def target(m,i):
 vals=[]
 for o in i.operands:
  if o.type==capstone.x86.X86_OP_MEM and o.mem.base==capstone.x86.X86_REG_RIP:
   vals.append(i.address+i.size+o.mem.disp-m["base"])
  if o.type==capstone.x86.X86_OP_IMM and i.mnemonic in ("call","jmp"):
   vals.append(o.imm-m["base"])
 return vals
def named_iat_calls(m,body,prefix):
 return [i for i in body if i.mnemonic=="call" and any(m["iat"].get(r,("",""))[1].startswith(prefix) for r in target(m,i))]
def has_direct_ref(m,body,r):
 return any(r in target(m,i) for i in body)
def lea_rdx_match_names(m,body,prefix):
 rows=[]
 for i in body:
  if i.mnemonic!="lea" or len(i.operands)<2:continue
  if i.operands[0].type!=capstone.x86.X86_OP_REG or CS.reg_name(i.operands[0].reg)!="rdx":continue
  for r in target(m,i):
   v=m["exp"].get(r,"")
   if v.startswith(prefix):rows.append((i.address-m["base"],r,v))
 return rows
res={}
for version,root in ROOTS.items():
 om=module(root/"OM.dll");flt=module(root/"FLT.dll");aelib=module(root/"aelib.dll")
 ob=symbol(om,"?OM_Birth@@");od=symbol(om,"?OM_Death@@")
 oc=symbol(om,"?Create@OM_Stream@@");on=symbol(om,"?OM_StreamNamePtr_MASK_SHAPE@@")
 birth=insns(om,ob);death=insns(om,od)
 rcall=named_iat_calls(om,birth,"?RegisterFactoryFunc@TDB_StreamFactory@@")
 ucall=named_iat_calls(om,death,"?UnregisterFactoryFunc@TDB_StreamFactory@@")
 assert len(rcall)==len(ucall)==1
 getter="?Get_AE_StreamFactory@@"
 assert len(named_iat_calls(om,birth,getter))==1
 assert len(named_iat_calls(om,death,getter))==1
 assert has_direct_ref(om,birth,oc) and has_direct_ref(om,birth,on) and has_direct_ref(om,death,on)
 assert any(i.mnemonic=="mov" and on in target(om,i) and i.address<rcall[0].address for i in birth)
 assert any(i.mnemonic=="mov" and on in target(om,i) and i.address<ucall[0].address for i in death)
 # The OM_Birth constructor receives the exact literal, not an inferred AEGP name.
 mask_literal_sites=[]
 for i in birth:
  if i.mnemonic!="lea" or not i.op_str.startswith("rdx,"):continue
  for r in target(om,i):
   try:
    if om["pe"].get_data(r,16)==b"ADBE Mask Shape\x00":mask_literal_sites.append(hex(i.address-om["base"]))
   except:pass
 assert mask_literal_sites
 methods=("?Read@OM_Stream@@","?Write@OM_Stream@@","?CloneStream@OM_Stream@@",
          "?SetValue@OM_Stream@@","?GetValueEx@OM_Stream@@")
 vmethods=[om["exp"][symbol(om,x)] for x in methods]
 assert len(vmethods)==5
 # FLT.dll native effect-register scoped helper, not a third-party plug-in registration.
 fbody_rva=0xcc20 if version=="2025" else 0xd0c0
 fbody=insns(flt,fbody_rva)
 fcalls=named_iat_calls(flt,fbody,"?Register@TDB_ScRegisterStreams@@")
 assert len(fcalls)==len(EXPECTED_FLT[version])
 frows=[]
 for ci in fcalls:
  idx=fbody.index(ci)
  prevs=fbody[max(0,idx-16):idx]
  matches=[]
  for i in prevs:
   if i.mnemonic!="lea" or not i.op_str.startswith("rdx,"):continue
   for r in target(flt,i):
    s=flt["exp"].get(r,"")
    if s.startswith(("?FLT_StreamGroupName_","?FLT_StreamName_")):matches.append(s)
  assert matches,hex(ci.address-flt["base"])
  match=matches[-1]
  suffix=match.split("Name_",1)[1].split("@@",1)[0]
  frows.append(suffix)
 assert frows==EXPECTED_FLT[version],(version,frows)
 assert len(named_iat_calls(flt,insns(flt,0xef60 if version=="2025" else 0xf360),
                             "?UnregisterAll@TDB_ScRegisterStreams@@"))==1
 # aelib.dll's same parent function has all three built-in stream bootstraps.
 # Instruction order is directly observable; run-time branch execution is not assumed.
 abr=0x6d9b0 if version=="2025" else 0x6fd80
 adr=0x6edc0 if version=="2025" else 0x71150
 born=insns(aelib,abr);ended=insns(aelib,adr)
 prefixes_birth=["?OM_Birth@@","?FLT_Birth@@","?BEE_Birth@@"]
 prefixes_death=["?OM_Death@@","?FLT_Death@@","?BEE_Death@@"]
 sites_birth=[named_iat_calls(aelib,born,n) for n in prefixes_birth]
 sites_death=[named_iat_calls(aelib,ended,n) for n in prefixes_death]
 assert all(len(v)==1 for v in sites_birth+sites_death)
 addrs_birth=[x[0].address-aelib["base"] for x in sites_birth]
 addrs_death=[x[0].address-aelib["base"] for x in sites_death]
 assert addrs_birth==sorted(addrs_birth) and addrs_death==sorted(addrs_death)
 res[version]={
  "OM_sha256":om["sha"],"FLT_sha256":flt["sha"],"aelib_sha256":aelib["sha"],
  "OM_Birth_rva":hex(ob),"OM_MaskShape_literal_lea_rvas":mask_literal_sites,
  "OM_native_creator":om["exp"][oc],"OM_stream_matchname_global":om["exp"][on],
  "OM_register_factory_call_rva":hex(rcall[0].address-om["base"]),
  "OM_unregister_factory_call_rva":hex(ucall[0].address-om["base"]),
  "OM_read_write_clone_value_exports":vmethods,
  "FLT_Register_calls":len(fcalls),"FLT_native_effect_type_symbols":frows,
  "aelib_boot_parent_function":hex(abr),
  "aelib_boot_call_order":["OM_Birth","FLT_Birth","BEE_Birth"],
  "aelib_boot_call_rvas":[hex(x) for x in addrs_birth],
  "aelib_death_parent_function":hex(adr),
  "aelib_death_call_order":["OM_Death","FLT_Death","BEE_Death"],
  "aelib_death_call_rvas":[hex(x) for x in addrs_death]}
 print("PASS",version,"OM mask path native cross-DLL registration+teardown, FLT",len(fcalls),
       "native effect types, aelib boot/death 3+3 direct ordered calls")
 print("  OM factory reg",hex(rcall[0].address-om["base"]),"unreg",hex(ucall[0].address-om["base"]),
       "mask literal",mask_literal_sites)
 print("  FLT types",frows)
 print("  aelib birth",list(map(hex,addrs_birth)),"death",list(map(hex,addrs_death)))
out=Path(__file__).resolve().parents[4]/"datasets"/"ae-native-om-flt-bee-crossmodule-boot-verified-2025-2026.json"
if out.exists():
 previous=json.loads(out.read_text(encoding="utf-8"))
 for version in ROOTS:
  for field in ("OM_sha256","FLT_sha256","aelib_sha256"):
   assert previous[version][field]==res[version][field],f"host Adobe binary changed unexpectedly: {version} {field}"
out.write_text(json.dumps(res,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("PASS ALL, saved",out)
