"""Static x64 registration virtual dispatch semantics across AE 2025 and 2026.
Native TDB register calls a canonical prototype's known virtual slots.
No Adobe runtime API invoked.
"""
from pathlib import Path
import pefile,subprocess,re,capstone,struct,hashlib,json
ROOTS={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")}
RELEVANT={0x58:"IsLeaf",0x80:"GetAsLeaf",0x150:"SetupCanonicalLayout",0x298:"IsSeparationLeader"}
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);cs.detail=True
out={}
for year,root in ROOTS.items():
 path=root/"TDB.dll";pe=pefile.PE(str(path));base=pe.OPTIONAL_HEADER.ImageBase
 exp={}
 for line in subprocess.run(["dumpbin","/exports",str(path)],text=True,capture_output=True,check=True,errors="replace").stdout.splitlines():
  m=re.match(r"\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\S+)",line)
  if m:exp[int(m.group(1),16)]=m.group(2)
 reg=[r for r,n in exp.items() if n.startswith("?RegisterFactoryFunc@TDB_StreamFactory@@")]
 vt=[r for r,n in exp.items() if n.startswith("??_7TDB_ParamPathStream@@6B@")]
 assert len(reg)==len(vt)==1
 pd={x.struct.BeginAddress:x.struct.EndAddress for x in pe.DIRECTORY_ENTRY_EXCEPTION}
 a=reg[0];body=list(cs.disasm(pe.get_data(a,pd[a]-a),base+a))
 slots={}
 for off,label in RELEVANT.items():
  b=struct.unpack("<Q",pe.get_data(vt[0]+off,8))[0]
  assert base<=b<base+pe.OPTIONAL_HEADER.SizeOfImage,(year,off,hex(b))
  name=exp.get(b-base,"")
  assert label in name,(year,off,label,name)
  slots[hex(off)]={"label":label,"slot_target_rva":hex(b-base),"resolved_export":name}
 def vm_calls(off):
  x=[i for i in body if i.mnemonic=="call" and re.search(r"\[(?:rax|rdx) \+ 0x%x\]"%off,i.op_str)]
  return [hex(i.address-base) for i in x]
 for off,v in RELEVANT.items():
  hits=vm_calls(off)
  assert len(hits)==(2 if v=="GetAsLeaf" else 1),(year,v,hits)
  slots[hex(off)]["registration_virtual_callsite_rvas"]=hits
 assert any(i.mnemonic=="call" and any(o.type==capstone.x86.X86_OP_IMM and o.imm-base in [r for r,n in exp.items() if n.startswith("?CreateStream@TDB_StreamFactory@@")] for o in i.operands) for i in body)
 init_sites=[(hex(i.address-base),i.op_str) for i in body if i.mnemonic=="mov" and i.op_str.startswith("r9d, 0x258")]
 assert len(init_sites)==1
 out[year]={"TDB_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"factory_registrar_rva":hex(a),"native_parampath_vtable_rva":hex(vt[0]),
 "virtual_methods_proven_by_real_parampath_vtable":slots,"create_stream_mode_constant":init_sites[0],
 "scope":"static disassembly; virtual slot identity for known native param-path; not arbitrary foreign vtable"}
 print("PASS",year,"TDB RegisterFactoryFunc->CreateStream + virtual dispatch")
 for off,row in slots.items():print(" ",off,row["label"],row["registration_virtual_callsite_rvas"],row["resolved_export"][:106])
dest=Path(__file__).resolve().parents[4]/"datasets"/"ae-tdb-eager-canonical-vtable-2025-2026.json"
if dest.exists():
 previous=json.loads(dest.read_text(encoding="utf-8"))
 for version in ("2025","2026"):
  assert previous[version]["TDB_sha256"]==out[version]["TDB_sha256"],"Original Adobe DLL changed: "+version+" TDB_sha256"
dest.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print("PASS BOTH VERSIONS",dest)
