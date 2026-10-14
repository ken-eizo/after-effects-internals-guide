"""Strict offline vtable proof: native TDB group canonical initializer dispatches
virtual FillInCanonicalUILayout overridden by Adobe Shape Contents.
Uses installed original AE2025/AE2026 TDB.dll and BEE.dll only.
"""
from pathlib import Path
import pefile,subprocess,re,capstone,struct,json,hashlib
roots={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files"),
       "2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")}
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);cs.detail=True
def load(path):
 p=pefile.PE(str(path));base=p.OPTIONAL_HEADER.ImageBase;exp={}
 for line in subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,check=True,errors="replace").stdout.splitlines():
  m=re.match(r"\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\S+)",line)
  if m:exp[int(m.group(1),16)]=m.group(2)
 return p,base,exp,{x.struct.BeginAddress:x.struct.EndAddress for x in p.DIRECTORY_ENTRY_EXCEPTION}
def sym(exp,key):
 values=[r for r,n in exp.items() if n.startswith(key)]
 assert len(values)==1,(key,values)
 return values[0]
def slot(pe,base,vtable,off):
 ptr=struct.unpack("<Q",pe.get_data(vtable+off,8))[0]
 assert base<=ptr<base+pe.OPTIONAL_HEADER.SizeOfImage
 return ptr-base
out={}
for year,root in roots.items():
 t,bt,te,tp=load(root/"TDB.dll");b,bb,be,bp=load(root/"BEE.dll")
 ts=sym(te,"?SetupCanonicalLayout@TDB_StreamBase@@")
 tg=sym(te,"?SetupCanonicalLayout@TDB_StreamGroup@@")
 basebytes=t.get_data(ts,3)
 assert basebytes==b"\xc2\x00\x00",(year,"TDB_StreamBase setup not a no-op",basebytes.hex())
 vv=sym(te,"??_7TDB_StreamGroup@@6B@")
 assert slot(t,bt,vv,0x150)==tg
 instructions=list(cs.disasm(t.get_data(tg,tp[tg]-tg),bt+tg))
 calls=[i for i in instructions if i.mnemonic=="call" and i.op_str=="qword ptr [rax + 0x1c8]"]
 assert len(calls)==1,(year,"group virtual canonical hook missing")
 def real_call(target):
  return [i for i in instructions if i.mnemonic=="call" and any(o.type==capstone.x86.X86_OP_IMM and o.imm-bt==target for o in i.operands)]
 separate=sym(te,"?SetupCanonicalLayoutForSeperatedDimensions@TDB_StreamFactory@@")
 assign=sym(te,"?SetUILayout@TDB_StreamGroup@@")
 separate_sites=real_call(separate)
 assign_sites=real_call(assign)
 assert len(separate_sites)==len(assign_sites)==1,(year,separate_sites,assign_sites)
 assert calls[0].address<separate_sites[0].address<assign_sites[0].address
 shape_vt=sym(be,"??_7VectorsStreamGroup@BEE_VectorStream@@6B@")
 shape_fill=sym(be,"?FillInCanonicalUILayout@VectorsStreamGroup@BEE_VectorStream@@")
 shape_actual=slot(b,bb,shape_vt,0x1c8)
 assert shape_actual==shape_fill,(year,hex(shape_actual),hex(shape_fill))
 root_vt=sym(be,"??_7VectorStreamGroup@BEE_VectorStream@@6B@")
 root_fill=sym(be,"?FillInCanonicalUILayout@VectorStreamGroup@BEE_VectorStream@@")
 assert slot(b,bb,root_vt,0x1c8)==root_fill
 out[year]={"TDB_sha256":hashlib.sha256((root/"TDB.dll").read_bytes()).hexdigest(),
 "BEE_sha256":hashlib.sha256((root/"BEE.dll").read_bytes()).hexdigest(),
 "base_nop_setup_rva":hex(ts),"base_setup_opcode":basebytes.hex(),
 "group_setup_rva":hex(tg),"group_setup_vtable_slot":"0x150",
 "group_fillin_virtual_callsite_rva":hex(calls[0].address-bt),
 "group_fillin_vtable_slot":"0x1c8",
 "separated_dimensions_processing_call_rva":hex(separate_sites[0].address-bt),
 "set_uilayout_call_rva":hex(assign_sites[0].address-bt),
 "shape_contents_group_vtable_rva":hex(shape_vt),
 "shape_contents_fillin_rva":hex(shape_fill),
 "shape_root_group_vtable_rva":hex(root_vt),"shape_root_fillin_rva":hex(root_fill)}
 print("PASS",year,"TDB group SetupCanonicalLayout -> vtable[0x1c8] FillInCanonicalUILayout -> BEE Shape overrides")
 print("  ",hex(tg),hex(calls[0].address-bt),"shape contents",hex(shape_fill),"root",hex(root_fill))
dest=Path(__file__).resolve().parents[4]/"datasets"/"ae-tdb-group-to-bee-shape-canonical-dispatch-2025-2026.json"
if dest.exists():
 previous=json.loads(dest.read_text(encoding="utf-8"))
 for version in ("2025","2026"):
  assert previous[version]["TDB_sha256"]==out[version]["TDB_sha256"],"Original Adobe DLL changed: "+version+" TDB_sha256"
  assert previous[version]["BEE_sha256"]==out[version]["BEE_sha256"],"Original Adobe DLL changed: "+version+" BEE_sha256"
dest.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print("PASS BOTH",dest)
