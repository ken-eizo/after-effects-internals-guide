"""Resolve FLT's exact native effect Stream MatchName per real TDB registrar CALL.
Static original FLT.dll 2025/2026 x64 PE; private methods are NEVER invoked.
"""
from pathlib import Path
import pefile,subprocess,re,capstone,json,hashlib
roots={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files"),
       "2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")}
starts={"2025":0xcc20,"2026":0xd0c0}
out={}
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);cs.detail=True
for year,root in roots.items():
 path=root/"FLT.dll";pe=pefile.PE(str(path));base=pe.OPTIONAL_HEADER.ImageBase
 exp={}
 for line in subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
  m=re.match(r"\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\S+)",line)
  if m:exp[int(m.group(1),16)]=m.group(2)
 iat={i.address-base:(d.dll.decode(errors="replace"),i.name.decode(errors="replace") if i.name else "")
      for d in pe.DIRECTORY_ENTRY_IMPORT for i in d.imports}
 pdata={r.struct.BeginAddress:r.struct.EndAddress for r in pe.DIRECTORY_ENTRY_EXCEPTION}
 a=starts[year];insns=list(cs.disasm(pe.get_data(a,pdata[a]-a),base+a))
 rows=[]
 for idx,ins in enumerate(insns):
  if ins.mnemonic!="call":continue
  refs=[ins.address+ins.size+o.mem.disp-base for o in ins.operands if o.type==capstone.x86.X86_OP_MEM and o.mem.base==capstone.x86.X86_REG_RIP]
  if not any(t in iat and iat[t][1].startswith("?Register@TDB_ScRegisterStreams@@") for t in refs):continue
  found=None
  for prev in reversed(insns[max(0,idx-13):idx]):
   if prev.mnemonic=="call":break
   if prev.mnemonic=="lea" and len(prev.operands)==2 and prev.operands[0].type==capstone.x86.X86_OP_REG and cs.reg_name(prev.operands[0].reg)=="rdx" and prev.operands[1].type==capstone.x86.X86_OP_MEM and prev.operands[1].mem.base==capstone.x86.X86_REG_RIP:
    ptr=prev.address+prev.size+prev.operands[1].mem.disp-base
    n=exp.get(ptr,"")
    if n.startswith(("?FLT_StreamName_","?FLT_StreamGroupName_")):
     found={"match_symbol":n,"match_rva":hex(ptr),"match_load_rva":hex(prev.address-base)}
    break
  assert found,(year,hex(ins.address-base))
  # The registrar is called with RCX = the scope-local TDB_ScRegisterStreams object,
  # RDX = the exact BEE/FLT match object, R8 std::function, R9 bool.
  rows.append({"register_call_rva":hex(ins.address-base),**found})
 print(year,"FLT native effect type registrations",len(rows),flush=True)
 for row in rows:print(" ",row["register_call_rva"],row["match_symbol"].split("@@",1)[0],flush=True)
 assert len(rows)==(6 if year=="2025" else 7)
 assert all("FLT_StreamName_EFFECT_BLENDMODE" not in d["match_symbol"] for d in rows) if year=="2025" else any("FLT_StreamName_EFFECT_BLENDMODE" in d["match_symbol"] for d in rows)
 out[year]={"FLT_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"registration_helper_rva":hex(a),"registers":rows}
outp=Path(__file__).resolve().parents[4]/"datasets"/"ae-flt-native-effect-register-types-2025-2026.json"
outp.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print("PASS",outp)
