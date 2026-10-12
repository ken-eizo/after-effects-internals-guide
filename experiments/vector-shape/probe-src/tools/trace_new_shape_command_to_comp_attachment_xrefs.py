"""Resolve direct CALL and JMP references to the actual native Shape
construction/attachment transaction function and the NewVectorLayer command.
Raw byte refs are filtered by disassembly at candidate caller .pdata start.
Only read pinned BEE.dll on disk, no host calls.
"""
from pathlib import Path
import pefile,bisect,struct,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
 {"create_then_attach":0x3a7ca0, "new_shape_command":0x65cdd0,"shared_new_layer_tail":0x667610}),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",
 {"create_then_attach":0x3b4110,"new_shape_command":0x6783e0,"shared_new_layer_tail":0x682f90})}
out={}
for y,(path,targets) in cfg.items():
 pe=pefile.PE(path);symbols={e.address:e.name.decode(errors="replace") for e in pe.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 pd=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in pe.DIRECTORY_ENTRY_EXCEPTION)
 starts=[a for a,b in pd]
 dis=Cs(CS_ARCH_X86,CS_MODE_64);dis.detail=True
 candidates={a:[] for a in targets.values()}
 for section in pe.sections:
  if not section.Characteristics&0x20000000:continue
  txt=section.get_data()
  for prefix in (0xe8,0xe9):
   pos=0
   while True:
    pos=txt.find(bytes((prefix,)),pos)
    if pos<0:break
    if pos+5<len(txt):
     at=section.VirtualAddress+pos
     dst=at+5+struct.unpack_from("<i",txt,pos+1)[0]
     if dst in candidates:candidates[dst].append((at,prefix))
    pos+=1
 rows={}
 for name,addr in targets.items():
  valid=[]
  for caller,opcode in candidates[addr]:
   k=bisect.bisect_right(starts,caller)-1
   if k<0 or caller>=pd[k][1]:continue
   a,b=pd[k];fileoff=pe.get_offset_from_rva(a)
   matched=False
   for instruction in dis.disasm(txt[0:0] if False else pe.get_data(a,b-a),pe.OPTIONAL_HEADER.ImageBase+a):
    if instruction.address-pe.OPTIONAL_HEADER.ImageBase==caller and instruction.id and instruction.mnemonic in ("call","jmp"):
     if instruction.operands[0].type==X86_OP_IMM and instruction.operands[0].imm-pe.OPTIONAL_HEADER.ImageBase==addr:
      matched=True
     break
   if matched:valid.append({"caller_rva":hex(caller),"containing_function":hex(a),
    "containing_native_export":symbols.get(a,""),"kind":"call" if opcode==0xe8 else "jmp"})
  rows[name]={"target_rva":hex(addr),"raw_ref_count":len(candidates[addr]),"verified_x64_instruction_boundary_refs":valid}
  print(y,name,"raw",len(candidates[addr]),"verified",len(valid),flush=True)
  for x in valid[:15]:print(" ",x,flush=True)
 out[y]=rows
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_new_shape_command_to_comp_attach_xrefs_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L BEE PE actual raw + Capstone verified direct E8/E9 references for native Shape-layer construction and New Shape command","versions":out},indent=2)+"\n")
print("SAVED",dst)
