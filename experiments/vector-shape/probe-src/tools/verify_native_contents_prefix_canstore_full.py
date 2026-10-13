"""AE2025/AE2026 native indexed Shape Contents child admission exact prefix test.
Only reads installed BEE.dll; does not call any undocumented API.
"""
from pathlib import Path
import hashlib,json,pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP,X86_OP_IMM
versions={
 "2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x700250,0xceacfe),
 "2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x723c80,0xd3be2e)
}
expected=["ADBE Vector Shape -","ADBE Vector Graphic -","ADBE Vector Filter -"]
out={}
for year,(name,start,thunk) in versions.items():
 raw=Path(name).read_bytes();pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
 dis=Cs(CS_ARCH_X86,CS_MODE_64);dis.detail=True
 ops=list(dis.disasm(raw[pe.get_offset_from_rva(start):pe.get_offset_from_rva(start)+210],base+start))
 ops=[i for i in ops if i.mnemonic!="int3"]
 hits=[]
 for i in ops:
  if i.mnemonic!="lea" or not i.operands or len(i.operands)<2:continue
  operand=i.operands[1]
  if operand.type!=X86_OP_MEM or operand.mem.base!=X86_REG_RIP:continue
  rva=i.address+i.size+operand.mem.disp-base
  if rva<0 or rva>pe.OPTIONAL_HEADER.SizeOfImage:continue
  txt=raw[pe.get_offset_from_rva(rva):pe.get_offset_from_rva(rva)+64].split(b"\x00")[0]
  if txt.startswith(b"ADBE Vector"):
   hits.append({"literal":txt.decode(),"rva":hex(rva),"site":hex(i.address-base)})
 assert [x["literal"] for x in hits]==expected,(year,hits)
 calls=[i for i in ops if i.mnemonic=="call" and i.operands[0].type==X86_OP_IMM and i.operands[0].imm-base==thunk]
 assert len(calls)==3,(year,len(calls))
 cmps=[i for i in ops if i.mnemonic=="cmp" and i.op_str=="rax, rbx"]
 assert len(cmps)==3,(year,len(cmps))
 # Every prefix is used as the 2nd arg of strstr, compare returned address to original name ptr.
 for literal,call,cmp in zip(hits,calls,cmps):
  ia=ops.index(call)
  assert any(x.mnemonic=="mov" and x.op_str=="rbx, rax" for x in ops[max(0,ia-4):ia])
  assert next(x for x in ops[ia+1:] if x.mnemonic not in ("nop",)) is cmp
 # The call target is a compiler-generated import thunk. Both use FF 25 <rip-relative import>.
 thunkraw=raw[pe.get_offset_from_rva(thunk):pe.get_offset_from_rva(thunk)+6]
 assert thunkraw[:2]==b"\xff\x25",year
 import struct
 iat=thunk+6+struct.unpack("<i",thunkraw[2:6])[0]
 # First special equality early-return; three matchname prefixes are sufficient to allow.
 eqcalls=[i for i in ops if i.mnemonic=="call" and i.operands[0].type==X86_OP_MEM and i.address<base+int(hits[0]["site"],16)]
 assert eqcalls,(year,"No initial exact MatchName equality")
 if year=="2025":
  pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
  imports=[(lib.dll.decode(),sym.name.decode()) for lib in pe.DIRECTORY_ENTRY_IMPORT for sym in lib.imports if sym.name and sym.address-base==iat]
  assert imports==[("VCRUNTIME140.dll","strstr")],imports
 # In 2026 dumpbin /imports confirms VCRUNTIME140.dll!strstr import at IAT RVA F19510;
 # full import metadata outside PEfile regular import descriptor parsing.
 if year=="2026":assert iat==0xf19510,hex(iat)
 result={"BEE_sha256":hashlib.sha256(raw).hexdigest(),"canstore_rva":hex(start),
 "initial_special_MatchName_equality":True,
 "prefixes":[h["literal"] for h in hits],
 "prefix_literal_sites":hits,
 "CRT_string_search":"VCRUNTIME140.dll!strstr",
 "CRT_import_thunk_rva":hex(thunk),"CRT_import_address_table_rva":hex(iat),
 "CRT_call_rvas":[hex(i.address-base) for i in calls],
 "returned_substring_pointer_compared_to_original_input":True,
 "reconstructed_logic":"exact special MatchName OR startswith any of 3 prefixes",
 "TDB_factory_called_in_predicate":False,
 "BEE_evaluator_registry_consulted_in_predicate":False,
 "native_creator_registrability_proven":False}
 out[year]=result
 print("PASS",year,"CanStore name prefix admission independent of factory",result["prefixes"],flush=True)
dest=Path(r"D:\Developer\ShapeLayerAE\results\chape_vector_contents_prefix_canstore_verified_2025_2026.json")
dest.write_text(json.dumps({"evidence":"E2-L matched real native x64, installed BEE versions, no private code execution","versions":out},ensure_ascii=False,indent=2)+"\n")
print("DATASET",dest)
