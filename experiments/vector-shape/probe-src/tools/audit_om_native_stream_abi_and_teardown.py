"""Verify native OM_Stream allocation/creator/global MatchName teardown contract.
Static installed OM.dll x64 PE only, no actual Adobe execution.
"""
from pathlib import Path
import re,subprocess,hashlib,json,pefile,capstone
ROOTS={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")}
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
def info(path):
 p=pefile.PE(str(path));base=p.OPTIONAL_HEADER.ImageBase
 exp={}
 for l in subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
  m=re.match(r"\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\S+)",l)
  if m:exp[int(m.group(1),16)]=m.group(2)
 iat={i.address-base:(d.dll.decode(errors="replace"),i.name.decode(errors="replace") if i.name else "")
      for d in p.DIRECTORY_ENTRY_IMPORT for i in d.imports}
 pd={x.struct.BeginAddress:x.struct.EndAddress for x in p.DIRECTORY_ENTRY_EXCEPTION}
 return p,base,exp,iat,pd
def sym(ex,needle):
 x=[r for r,s in ex.items() if s.startswith(needle)]
 assert len(x)==1,(needle,x)
 return x[0]
def body(p,base,pd,r):
 return list(md.disasm(p.get_data(r,pd[r]-r),base+r))
def targets(i,base):
 x=[]
 for o in i.operands:
  if o.type==capstone.x86.X86_OP_MEM and o.mem.base==capstone.x86.X86_REG_RIP:
   x.append(i.address+i.size+o.mem.disp-base)
  if o.type==capstone.x86.X86_OP_IMM and i.mnemonic in ("call","jmp"):x.append(o.imm-base)
 return x
def idxcall(ins,base,iat,dll,s):
 return [n for n,i in enumerate(ins) if i.mnemonic=="call" and any(t in iat and iat[t][0].lower()==dll and iat[t][1].startswith(s) for t in targets(i,base))]
out={}
for year,root in ROOTS.items():
 path=root/"OM.dll";p,base,ex,iat,pd=info(path)
 cr=sym(ex,"?Create@OM_Stream@@")
 ctor=sym(ex,"??0OM_Stream@@QEAA@IEPEBVTDB_MatchName@@PEAVTDB_StreamFactory@@_N@Z")
 birth=sym(ex,"?OM_Birth@@");death=sym(ex,"?OM_Death@@")
 name=sym(ex,"?OM_StreamNamePtr_MASK_SHAPE@@")
 vt=sym(ex,"??_7OM_Stream@@6B@")
 derived_ctor=sym(ex,"??0?$TDB_DerivedStream@UOM_MaskShapeStreamTraits@@@@QEAA@IEPEBVTDB_MatchName@@PEAVTDB_StreamFactory@@_N@Z")
 creator=body(p,base,pd,cr);bi=body(p,base,pd,birth);de=body(p,base,pd,death)
 alloc=idxcall(creator,base,iat,"u.dll","??2U_MemTrackedObject@@")
 assert len(alloc)==1
 ai=alloc[0]
 assert ai>0 and creator[ai-1].mnemonic=="mov" and creator[ai-1].op_str=="ecx, 0x450"
 native_ctor=body(p,base,pd,ctor)
 assert any(i.mnemonic=="call" and derived_ctor in targets(i,base) for i in native_ctor)
 assert any(i.mnemonic=="lea" and vt in targets(i,base) for i in native_ctor)
 assert any(i.mnemonic=="mov" and i.op_str=="qword ptr [rbx], rax" for i in native_ctor)
 assert any(i.mnemonic=="mov" and i.op_str=="byte ptr [rbx + 0x448], 0" for i in native_ctor)
 con=[i for i in creator if i.mnemonic=="call" and ctor in targets(i,base)]
 assert len(con)==1
 mb=idxcall(bi,base,iat,"u.dll","??2U_MemTrackedObject@@")
 assert len(mb)==1 and bi[mb[0]-1].op_str=="ecx, 0x10"
 mctor=idxcall(bi,base,iat,"tdb.dll","??0TDB_MatchName@@")
 assert len(mctor)==1
 reg=idxcall(bi,base,iat,"tdb.dll","?RegisterFactoryFunc@TDB_StreamFactory@@")
 unreg=idxcall(de,base,iat,"tdb.dll","?UnregisterFactoryFunc@TDB_StreamFactory@@")
 free=idxcall(de,base,iat,"u.dll","??3U_MemTrackedObject@@")
 assert len(reg)==len(unreg)==len(free)==1
 assert unreg[0]<free[0]
 # Validate actual global match pointer reference before registration, unregister,
 # deallocation, then zeroing of global, using native RIP addressing.
 assert any(name in targets(i,base) and i.mnemonic=="mov" for i in bi[:reg[0]])
 assert any(name in targets(i,base) and i.mnemonic=="mov" for i in de[:unreg[0]])
 assert any(name in targets(i,base) and i.mnemonic=="mov" for i in de[unreg[0]+1:free[0]+1])
 zero=[i for i in de[free[0]+1:] if i.mnemonic=="mov" and name in targets(i,base) and i.op_str.endswith(", 0")]
 assert len(zero)==1,(year,zero)
 # Verify concrete custom value/persistence surface in the C++ class export table.
 methods={}
 for key in ("?Read@OM_Stream@@","?Write@OM_Stream@@","?CloneStream@OM_Stream@@","?GetValueEx@OM_Stream@@","?SetValue@OM_Stream@@","?CanHaveExpression@OM_Stream@@"):
  methods[key]=hex(sym(ex,key))
 out[year]={"OM_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
  "native_concrete_class":"OM_Stream : TDB_DerivedStream<OM_MaskShapeStreamTraits>",
  "native_creator_rva":hex(cr),"native_stream_constructor_rva":hex(ctor),
  "native_typed_base_constructor_rva":hex(derived_ctor),
  "vtable_initialized_in_constructor":True,
  "object_last_byte_initialized_at_offset":hex(0x448),
  "OM_Stream_vtable_rva":hex(vt),"native_stream_allocation_bytes":0x450,
  "native_allocator_import":"U.dll!U_MemTrackedObject::operator new",
  "native_factory_constructor_callsite_rva":hex(con[0].address-base),
  "matchname_allocation_bytes":0x10,"birth_matchname_constructor_callsite_rva":hex(bi[mctor[0]].address-base),
  "matchname_pointer_export":ex[name],
  "register_factory_call_rva":hex(bi[reg[0]].address-base),
  "unregister_factory_call_rva":hex(de[unreg[0]].address-base),
  "matchname_delete_call_rva":hex(de[free[0]].address-base),
  "matchname_global_reset_rva":hex(zero[0].address-base),
  "native_stream_persistence_and_value_exports":methods,
  "important_limit":"Object allocation size matches 2025/26 but C++ ABI and vtables are PRIVATE and not guaranteed stable. No reference lifetime safety inferred."}
 print(year,"PASS OM native Stream bytes",hex(0x450),
   "constructor",hex(ctor),"vtable",hex(vt),
   "registration",hex(bi[reg[0]].address-base),"unregister",hex(de[unreg[0]].address-base),
   "free",hex(de[free[0]].address-base))
dest=Path(__file__).resolve().parents[4]/"datasets"/"ae-om-native-maskshape-stream-abi-and-teardown-2025-2026.json"
if dest.exists():
 previous=json.loads(dest.read_text(encoding="utf-8"))
 for version in ROOTS:
  assert previous[version]["OM_sha256"]==out[version]["OM_sha256"],f"original native OM.dll changed unexpectedly: {version}"
dest.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("PASS 2/2 native OM stream custom-class allocator/value/archive/teardown; all static. Saved",dest)
