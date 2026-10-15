"""EXP-SHAPE-105: Original AE 2025/2026 BEE_Birth installs TDB name-lookup callback.

Pure PE/x64 read-only verification. Distinguishes the global per-group
name-search callback from native StreamFactory MatchName Creator registration.
No private Adobe API executed or host process loaded.
"""
import pefile,capstone,hashlib,json
from pathlib import Path
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
ROOT=Path(r"D:\Developer\After Effects Internals Guide")
INFO={
"2025":{"bee":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
 "tdb":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll",
 "bee_sha":"98c682351e30f38cb7021eaa142f5ec473aea92885e14915d87c157cda971730",
 "tdb_sha":"2ed19824997f3de797a75fef6f22d4d11ac8548c9d35f6093aa2afc1a6ed2e69",
 "birth_rva":0x64a530,"set_site":0x64a5f2,"setter_rva":0x2b690,"find_rva":0x2b540,
 "static_function_rva":0xa79d0,"function_slot_rva":0xa7a08},
"2026":{"bee":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",
 "tdb":r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll",
 "bee_sha":"5fd8d318456228b9fd2a6733a5758f6b84206b7a8effcba5202957cd27ac680e",
 "tdb_sha":"82677a20bdf871878b579522c4b4e0def8af0a50a810e3b9972da1170f546c1b",
 "birth_rva":0x664f70,"set_site":0x66502e,"setter_rva":0x2c440,"find_rva":0x2c280,
 "static_function_rva":0xc0c60,"function_slot_rva":0xc0c98}}
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);cs.detail=True
def inst(pe,rva,size):
 return list(cs.disasm(pe.get_data(rva,size),pe.OPTIONAL_HEADER.ImageBase+rva))
def rip(pe,x):
 for p in x.operands:
  if p.type==X86_OP_MEM and p.mem.base==X86_REG_RIP:
   return x.address+x.size+p.mem.disp-pe.OPTIONAL_HEADER.ImageBase
def one(items,label):
 assert len(items)==1,(label,len(items))
 return items[0]
def loc(pe,z):return hex(z.address-pe.OPTIONAL_HEADER.ImageBase)
res={}
for year,c in INFO.items():
 images={}
 for name in ("bee","tdb"):
  path=Path(c[name]);data=path.read_bytes();digest=hashlib.sha256(data).hexdigest()
  assert digest==c[name+"_sha"],(year,name,digest)
  p=pefile.PE(data=data)
  exports={e.address:e.name.decode(errors="replace") for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
  imports={i.address-p.OPTIONAL_HEADER.ImageBase:(d.dll.decode(errors="replace").lower(),
                   i.name.decode(errors="replace") if i.name else "")
           for d in p.DIRECTORY_ENTRY_IMPORT for i in d.imports}
  pdata={e.struct.BeginAddress:e.struct.EndAddress for e in p.DIRECTORY_ENTRY_EXCEPTION}
  images[name]=(p,exports,imports,pdata,digest)
 bp,bex,bimp,bpd,bd=images["bee"];tp,tex,timp,tpdata,td=images["tdb"]
 assert bex.get(c["birth_rva"],"").startswith("?BEE_Birth@@")
 assert tex.get(c["setter_rva"],"").startswith("?SetFindStreamByNameNullOKFunction@TDB_StreamGroup@@")
 assert tex.get(c["find_rva"],"").startswith("?FindStreamByNameNullOK@TDB_StreamGroup@@")
 birth=inst(bp,c["birth_rva"],bpd[c["birth_rva"]]-c["birth_rva"])
 matches=[x for x in birth if x.mnemonic=="call" and x.address-bp.OPTIONAL_HEADER.ImageBase==c["set_site"]]
 assert len(matches)==1
 call=matches[0];slot=rip(bp,call)
 assert bimp.get(slot,("",""))[0]=="tdb.dll"
 assert bimp[slot][1].startswith("?SetFindStreamByNameNullOKFunction@TDB_StreamGroup@@")
 assert birth[birth.index(call)-1].op_str.startswith("rcx, [rsp + 0x")
 # The setter is a short leaf-tailcall which assigns a stored std::function
 # via a target within TDB.dll's own static storage.
 setter=inst(tp,c["setter_rva"],28)
 arg=one([x for x in setter if x.mnemonic=="mov" and x.op_str=="rdx, rcx"],"setter transfers callback argument")
 st=one([x for x in setter if x.mnemonic=="lea" and x.op_str.startswith("rcx, [rip")],"setter static function target")
 assert rip(tp,st)==c["static_function_rva"]
 tail=one([x for x in setter if x.mnemonic=="jmp" and x.operands[0].type==X86_OP_IMM],"setter delegates std::function assignment")
 assert st.address<tail.address
 # BEE registration and TDB retrieval share one function storage, and
 # the dispatcher handles absent callback without constructing a Stream.
 find=inst(tp,c["find_rva"],60)
 slotload=one([x for x in find if x.mnemonic=="mov" and x.op_str.startswith("rcx, qword ptr [rip")],"lookup reads registered callback")
 assert rip(tp,slotload)==c["function_slot_rva"]
 assert c["function_slot_rva"]-c["static_function_rva"]==0x38
 nulltest=one([x for x in find if x.mnemonic=="test" and x.op_str=="rcx, rcx"],"lookup null test")
 nulljump=one([x for x in find if x.mnemonic=="je"],"null callback branch")
 vm=one([x for x in find if x.mnemonic=="call" and x.op_str=="qword ptr [rax + 0x10]"],"invokes stored callable")
 zero=one([x for x in find if x.mnemonic=="xor" and x.op_str=="eax, eax"],"without callback return nullptr")
 assert slotload.address<nulltest.address<nulljump.address<vm.address<zero.address
 assert nulljump.operands[0].type==X86_OP_IMM and nulljump.operands[0].imm==zero.address
 res[year]={
  "BEE_sha256":bd,"TDB_sha256":td,
  "BEE_Birth":{"entry":hex(c["birth_rva"]),"TDB_SetFindStreamByNameNullOKFunction_call":loc(bp,call),
               "installed_parameter_type":"std::function<const TDB_StreamBase*(const TDB_StreamGroup*, const UTF16String&, unsigned int&, bool&)> (private MSVC symbol, conceptual)"},
  "TDB_SetFindStreamByNameNullOKFunction":{"entry":hex(c["setter_rva"]),
      "static_callback_storage_base":hex(c["static_function_rva"]),
      "std_function_assignment_tailcall":loc(tp,tail)},
  "TDB_StreamGroup_FindStreamByNameNullOK":{"entry":hex(c["find_rva"]),
      "stored_callable_pointer_offset":"0x38",
      "stored_callable_load":loc(tp,slotload),
      "null_callback_branch":loc(tp,nulljump),
      "std_function_invoke_slot":"+0x10",
      "invocation":loc(tp,vm),
      "callback_absent_returns_null":loc(tp,zero)},
  "api_boundary":"Name-based lookup callback; NOT TDB_StreamFactory::RegisterFactoryFunc and NOT a public third-party native Stream provider",
  "runtime_execution":False}
 print("PASS",year,"BEE_Birth -> private TDB name-lookup std::function; FindByName invokes or returns nullptr; distinct from Creator factory",flush=True)
out=ROOT/"datasets"/"ae-bee-tdb-native-name-lookup-callback-2025-2026.json"
out.write_text(json.dumps({"evidence":"E2-L original SHA pinned BEE and TDB x64 binaries; no Adobe code executed",
 "versions":res},indent=2)+"\n",encoding="utf8")
print("DATASET",out)
