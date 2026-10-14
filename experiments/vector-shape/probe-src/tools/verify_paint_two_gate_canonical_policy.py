from pathlib import Path
import json,re,subprocess,hashlib,struct,capstone,pefile
ROOTS={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")}
BASE=Path(r"D:\Developer\ShapeLayerAE\labs\paint_native_properties_audit")
def exports(path):
 txt=subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True).stdout
 out={}
 for line in txt.splitlines():
  m=re.match(r"\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\S+)",line)
  if m:out[int(m.group(1),16)]=m.group(2)
 return out
def expect_symbol(exp,phrase):
 matches=[rv for rv,name in exp.items() if name.startswith(phrase)]
 assert len(matches)==1,(phrase,matches)
 return matches[0]
def ctx(path):
 pe=pefile.PE(str(path));base=pe.OPTIONAL_HEADER.ImageBase
 return {
 "path":str(path),"pe":pe,"base":base,"export":exports(path),
 "pdata":{x.struct.BeginAddress:x.struct.EndAddress for x in pe.DIRECTORY_ENTRY_EXCEPTION},
 "iat":{x.address-base:(d.dll.decode("latin1"),x.name.decode("latin1") if x.name else str(x.ordinal))
 for d in pe.DIRECTORY_ENTRY_IMPORT for x in d.imports},
 "sha256":hashlib.sha256(path.read_bytes()).hexdigest()
 }
def insns(c,rva):
 cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);cs.detail=True
 end=c["pdata"].get(rva,rva+512);assert end>rva and end-rva<250000
 return list(cs.disasm(c["pe"].get_data(rva,end-rva),c["base"]+rva))
def ref(c,i,o):
 if o.type==capstone.x86.X86_OP_MEM and o.mem.base==capstone.x86.X86_REG_RIP:
  return i.address+i.size+o.mem.disp-c["base"]
 return None
def pointer(c,rva):
 return struct.unpack("<Q",c["pe"].get_data(rva,8))[0]-c["base"]
out={}
for year,root in ROOTS.items():
 bee=ctx(root/"BEE.dll");tdb=ctx(root/"TDB.dll")
 assert len(bee["export"])>10000 and len(tdb["export"])>1200
 vt=expect_symbol(bee["export"],"??_7BEE_PaintStrokesGroup@@6B@")
 vtbase=expect_symbol(bee["export"],"??_7BEE_StrokesGroupBase@@6B@")
 slot56=pointer(bee,vt+56*8)
 assert slot56==pointer(bee,vtbase+56*8)
 thunk=list(capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64).disasm(
 bee["pe"].get_data(slot56,6),bee["base"]+slot56))
 assert len(thunk)==1 and thunk[0].mnemonic=="jmp"
 # x86-64 FF25 disp32 import jump; check exact opcode and IAT binding
 b=bee["pe"].get_data(slot56,6)
 assert b[:2]==b"\xff\x25"
 iat=slot56+6+struct.unpack("<i",b[2:])[0]
 assert bee["iat"].get(iat,('', ''))[0].lower()=="tdb.dll"
 assert bee["iat"][iat][1].startswith("?CanStore@TDB_StreamGroup@@")
 slot57=pointer(bee,vt+57*8)
 fill=expect_symbol(bee["export"],"?FillInCanonicalUILayout@BEE_StrokesGroupBase@@")
 assert slot57==fill
 fill_ins=insns(bee,fill)
 match=expect_symbol(bee["export"],"?BEE_StreamGroupName_PAINT_ATOM@@")
 match_refs=[(i.address-bee["base"]) for i in fill_ins for op in i.operands if ref(bee,i,op)==match]
 assert match_refs,("canonical Paint Atom constant missing",year)
 imported_canonical=[]
 for i in fill_ins:
  if i.mnemonic!="call":continue
  for op in i.operands:
   at=ref(bee,i,op)
   if at is not None and at in bee["iat"] and bee["iat"][at][1].startswith("?GetCanonicalStream@TDB_StreamBase@@"):
    imported_canonical.append(i.address-bee["base"])
 assert imported_canonical,("canonical constructor bridge missing",year)
 setup=expect_symbol(tdb["export"],"?SetupCanonicalLayout@TDB_StreamGroup@@")
 setup_ins=insns(tdb,setup)
 vcall=[i.address-tdb["base"] for i in setup_ins if i.mnemonic=="call" and "[rax + 0x1c8]" in i.op_str]
 assert vcall,("vtable fill slot57 not used",year)
 setui=expect_symbol(tdb["export"],"?SetUILayout@TDB_StreamGroup@@")
 setcalls=[i.address-tdb["base"] for i in setup_ins if i.mnemonic=="call" and any(op.type==capstone.x86.X86_OP_IMM and op.imm-tdb["base"]==setui for op in i.operands)]
 assert setcalls,("canonical fill not installed into UILayout",year)
 canstore=expect_symbol(tdb["export"],"?CanStore@TDB_StreamGroup@@")
 canins=insns(tdb,canstore)
 exact=expect_symbol(tdb["export"],"??8TDB_MatchName@@")
 compares=[i.address-tdb["base"] for i in canins if i.mnemonic=="call" and any(op.type==capstone.x86.X86_OP_IMM and op.imm-tdb["base"]==exact for op in i.operands)]
 assert compares
 assert any("[rcx + 0x210]" in i.op_str for i in canins)
 assert any("[rcx + 0x218]" in i.op_str for i in canins)
 register=expect_symbol(tdb["export"],"?Register@TDB_ScRegisterStreams@@")
 regfac=expect_symbol(tdb["export"],"?RegisterFactoryFunc@TDB_StreamFactory@@")
 regcalls=[i.address-tdb["base"] for i in insns(tdb,register) if i.mnemonic=="call" and any(op.type==capstone.x86.X86_OP_IMM and op.imm-tdb["base"]==regfac for op in i.operands)]
 assert regcalls
 out[year]={
 "BEE_sha256":bee["sha256"],"TDB_sha256":tdb["sha256"],
 "paint_strokes_vtable_rva":hex(vt),
 "canstore_virtual_slot":56,"paint_canstore_thunk_rva":hex(slot56),
 "canstore_iat_rva":hex(iat),"canstore_iat_import":bee["iat"][iat][1],
 "canonical_fill_virtual_slot":57,"paint_canonical_fill_rva":hex(fill),
 "canonical_paint_atom_match_rva":hex(match),"match_reference_rvas":[hex(x) for x in match_refs],
 "get_canonical_stream_call_rvas":[hex(x) for x in imported_canonical],
 "tdb_setup_canonical_layout_rva":hex(setup),"tdb_fill_virtual_call_rvas":[hex(x) for x in vcall],
 "tdb_set_ui_layout_call_rvas":[hex(x) for x in setcalls],
 "tdb_canstore_rva":hex(canstore),"match_name_comparison_call_rvas":[hex(x) for x in compares],
 "tdb_register_rva":hex(register),"tdb_factory_register_rva":hex(regfac),"factory_register_call_rvas":[hex(x) for x in regcalls]
 }
 print(year,"PASS PaintStrokes vtable slot56 TDB_CanStore, slot57 FillInCanonicalUILayout, canonical Paint Atom, TDB canonical SetupUILayout and exact match check")
 print("    Paint vtable",hex(vt),"CanStore thunk",hex(slot56),"canonical PaintAtom match",hex(match),"fill",hex(fill))
 print("    TDB SetupCanonicalLayout",hex(setup),"CanStore",hex(canstore),"RegisterFactoryFunc",hex(regfac))
p=BASE/"paint_two_gate_canonical_policy_2025_2026.json"
p.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print("PASS 2/2 saved",p)
