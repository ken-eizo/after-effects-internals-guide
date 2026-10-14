"""Read-only OM_Stream vtable dispatch bridge to native TDB methods.
Parses installed AE2025/2026 OM.dll PE file import trampolines.
"""
from pathlib import Path
import pefile,capstone,subprocess,re,struct,hashlib,json
roots={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")}
expected={0x58:"IsLeaf",0x80:"GetAsLeaf",0x150:"SetupCanonicalLayout",0x298:"IsSeparationLeader"}
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);cs.detail=True
res={}
for year,root in roots.items():
 pth=root/"OM.dll";pe=pefile.PE(str(pth));base=pe.OPTIONAL_HEADER.ImageBase
 exports={}
 for line in subprocess.run(["dumpbin","/exports",str(pth)],capture_output=True,text=True,check=True,errors="replace").stdout.splitlines():
  m=re.match(r"\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\S+)",line)
  if m:exports[int(m.group(1),16)]=m.group(2)
 iat={i.address-base:(d.dll.decode(errors="replace").lower(),i.name.decode(errors="replace") if i.name else "")
      for d in pe.DIRECTORY_ENTRY_IMPORT for i in d.imports}
 vt=[r for r,n in exports.items() if n.startswith("??_7OM_Stream@@6B@")]
 assert len(vt)==1,(year,vt)
 rows=[]
 for off,kind in expected.items():
  ptr=struct.unpack("<Q",pe.get_data(vt[0]+off,8))[0]
  assert base<=ptr<base+pe.OPTIONAL_HEADER.SizeOfImage
  rv=ptr-base
  op=list(cs.disasm(pe.get_data(rv,10),ptr))
  assert op,(year,kind)
  ins=op[0]
  if ins.mnemonic=="jmp":
   assert len(ins.operands)==1 and ins.operands[0].type==capstone.x86.X86_OP_MEM and ins.operands[0].mem.base==capstone.x86.X86_REG_RIP
   trg=ins.address+ins.size+ins.operands[0].mem.disp-base
   symbol=iat.get(trg)
   assert symbol and symbol[0]=="tdb.dll" and kind in symbol[1],(year,kind,symbol)
   result={"mode":"direct_import_trampoline","import_dll":symbol[0],"import_symbol":symbol[1],"import_iat_rva":hex(trg)}
  else:
   nm=exports.get(rv,"")
   assert kind in nm,(year,kind,nm)
   result={"mode":"OM-local override","native_symbol":nm,"first_instructions":[i.mnemonic+" "+i.op_str for i in op[:3]]}
  rows.append({"vtable_offset":hex(off),"semantic":kind,"vtable_target_rva":hex(rv),**result})
 print(year,"PASS OM native cross-DLL virtual dispatch",[(x["semantic"],x["mode"]) for x in rows])
 res[year]={"OM_sha256":hashlib.sha256(pth.read_bytes()).hexdigest(),"vtable_rva":hex(vt[0]),"slots":rows}
dest=Path(__file__).resolve().parents[4]/"datasets"/"ae-om-native-vtable-to-tdb-dispatch-2025-2026.json"
if dest.exists():
 previous=json.loads(dest.read_text(encoding="utf-8"))
 for version in ("2025","2026"):
  assert previous[version]["OM_sha256"]==res[version]["OM_sha256"],"Original Adobe DLL changed: "+version+" OM_sha256"
dest.write_text(json.dumps(res,indent=2)+"\n",encoding="utf-8")
print("PASS vtable bridge cross-version",dest)
