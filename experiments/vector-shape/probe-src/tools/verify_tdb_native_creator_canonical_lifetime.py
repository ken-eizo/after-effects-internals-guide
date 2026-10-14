"""Strict read-only native TDB canonical prototype lifecycle order.
Checks register/creator map ordering and native unregister/removal sequence.
Does not execute or load Adobe private functions.
"""
from pathlib import Path
import pefile,subprocess,re,capstone,hashlib,json
roots={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files"),
       "2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")}
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);cs.detail=True
records={}
for year,root in roots.items():
 path=root/"TDB.dll";pe=pefile.PE(str(path));base=pe.OPTIONAL_HEADER.ImageBase
 exports={}
 for line in subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,check=True,errors="replace").stdout.splitlines():
  m=re.match(r"\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\S+)",line)
  if m:exports[int(m.group(1),16)]=m.group(2)
 pdata={x.struct.BeginAddress:x.struct.EndAddress for x in pe.DIRECTORY_ENTRY_EXCEPTION}
 def sym(name):
  matches=[r for r,s in exports.items() if s.startswith(name)]
  assert len(matches)==1,(year,name,matches)
  return matches[0]
 def body(r):return list(cs.disasm(pe.get_data(r,pdata[r]-r),base+r))
 def sites(ins,frag):
  return [i for i in ins if frag in i.op_str]
 def call_after(ins,i):
  ix=ins.index(i);calls=[x for x in ins[ix+1:ix+5] if x.mnemonic=="call"]
  assert len(calls)==1,(year,hex(i.address-base),[x.op_str for x in ins[ix+1:ix+5]])
  return calls[0]
 reg=sym("?RegisterFactoryFunc@TDB_StreamFactory@@")
 create=sym("?CreateStream@TDB_StreamFactory@@")
 unreg=sym("?UnregisterFactoryFunc@TDB_StreamFactory@@")
 unreg_body=sym("?UnregisterFactoryFunc_NullOK@TDB_StreamFactory@@")
 rr=body(reg);ur=body(unreg_body)
 create_call=[i for i in rr if i.mnemonic=="call" and any(o.type==capstone.x86.X86_OP_IMM and o.imm-base==create for o in i.operands)]
 assert len(create_call)==1
 callback_reg=[i for i in rr if i.mnemonic=="lea" and "+ 0x28]" in i.op_str and i.op_str.startswith("rcx,")]
 canonical_reg=[i for i in rr if i.mnemonic=="lea" and "+ 0x38]" in i.op_str and i.op_str.startswith("rcx,")]
 assert len(callback_reg)==len(canonical_reg)==1,(year,len(callback_reg),len(canonical_reg))
 assert callback_reg[0].address<create_call[0].address<canonical_reg[0].address
 ccan=[i for i in ur if i.mnemonic=="lea" and "+ 0x38]" in i.op_str and i.op_str.startswith("rcx,")]
 ccb=[i for i in ur if i.mnemonic=="lea" and "+ 0x28]" in i.op_str and i.op_str.startswith("rcx,")]
 assert len(ccan)==len(ccb)==1,(year,len(ccan),len(ccb))
 rem_can=call_after(ur,ccan[0]);rem_cb=call_after(ur,ccb[0])
 assert rem_can.address<rem_cb.address
 vdelete=[i for i in ur if i.mnemonic=="call" and i.op_str=="qword ptr [rax]"]
 assert len(vdelete)==1
 assert rem_cb.address<vdelete[0].address
 assert any(i.mnemonic=="mov" and i.op_str in ("r12, qword ptr [rdi + 0x30]","r12, qword ptr [rbx + 0x30]") for i in ur[:ur.index(rem_can)]),(year,"canonical prototype pointer not retained")
 assert any(i.mnemonic=="mov" and i.op_str=="rax, qword ptr [r12]" for i in ur[ur.index(rem_cb):ur.index(vdelete[0])]),(year,"prototype vtable target is not loaded")
 assert any(i.mnemonic=="test" and i.op_str=="r12, r12" for i in ur[ur.index(rem_cb):ur.index(vdelete[0])]),(year,"prototype null-check not observed")
 ix=ur.index(vdelete[0])
 assert any(x.mnemonic=="mov" and x.op_str=="edx, 1" for x in ur[max(0,ix-4):ix]),(year,ix)
 wrapper=list(cs.disasm(pe.get_data(unreg,8),base+unreg))
 assert wrapper[0].mnemonic=="xor" and wrapper[0].op_str=="r8d, r8d"
 assert wrapper[1].mnemonic=="jmp" and wrapper[1].operands[0].imm-base==unreg_body
 result={"original_TDB_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
 "register_factory_rva":hex(reg),"register_callback_map_offset":"0x28",
 "register_callback_map_insert_pre_create_rva":hex(callback_reg[0].address-base),
 "eager_create_call_rva":hex(create_call[0].address-base),
 "register_canonical_map_offset":"0x38",
 "register_canonical_map_insert_post_create_rva":hex(canonical_reg[0].address-base),
 "unregister_factory_wrapper_rva":hex(unreg),"unregister_impl_rva":hex(unreg_body),
 "unregister_canonical_map_remove_call_rva":hex(rem_can.address-base),
 "unregister_callback_map_remove_call_rva":hex(rem_cb.address-base),
 "unregister_canonical_virtual_deleting_destructor_call_rva":hex(vdelete[0].address-base),
 "scope_warning":"Static ordering only; no guarantee of rollback if exceptions occur during registration or if live child references survive."}
 records[year]=result
 print("PASS",year,"factory inserts callback -> eager creates canonical -> stores prototype")
 print("      unregister removes canonical map -> callback map -> virtual delete")
 print("      rvAs",result["eager_create_call_rva"],result["unregister_canonical_map_remove_call_rva"],result["unregister_callback_map_remove_call_rva"],result["unregister_canonical_virtual_deleting_destructor_call_rva"])
dst=Path(__file__).resolve().parents[4]/"datasets"/"ae-tdb-native-creator-canonical-lifetime-2025-2026.json"
if dst.exists():
 previous=json.loads(dst.read_text(encoding="utf-8"))
 for version in ("2025","2026"):
  assert previous[version]["original_TDB_sha256"]==records[version]["original_TDB_sha256"],"Original Adobe TDB.dll changed: "+version
dst.write_text(json.dumps(records,indent=2)+"\n",encoding="utf-8")
print("PASS BOTH",dst)
