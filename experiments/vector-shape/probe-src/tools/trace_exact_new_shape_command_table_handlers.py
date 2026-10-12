"""Resolve real Shape Layer NewVector command ID into BEE_DoCommand's
two native table callback functions, both AE2025 and AE2026.
Offline pinned BEE.dll only.
"""
from pathlib import Path
import pefile,bisect,hashlib,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
pairs={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",101),
       "2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",106)}
data=json.load(open(r"D:\Developer\ShapeLayerAE\results\bee_native_command_table_32byte_entries_2025_2026.json"))["versions"]
out={}
for y,(path,number) in pairs.items():
 raw=Path(path).read_bytes();p=pefile.PE(data=raw);base=p.OPTIONAL_HEADER.ImageBase
 exp={e.address:e.name.decode(errors="replace") for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 imported={i.address:d.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for d in p.DIRECTORY_ENTRY_IMPORT for i in d.imports if i.name}
 pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION);starts=[a for a,b in pdata]
 dec=Cs(CS_ARCH_X86,CS_MODE_64);dec.detail=True
 row=data[y]["entries"][number]
 callback={}
 for slot in (1,2):
  rva=int(row["pointers_rva"][slot],16)
  ix=bisect.bisect_right(starts,rva)-1
  a,b=pdata[ix] if ix>=0 and rva<pdata[ix][1] else (rva,rva+120)
  instructions=[];links=[]
  for inst in dec.disasm(raw[p.get_offset_from_rva(a):p.get_offset_from_rva(b)],base+a):
   one={"site":hex(inst.address-base),"op":inst.mnemonic+" "+inst.op_str}
   if len(instructions)<115:instructions.append(one)
   if inst.mnemonic in ("call","jmp") and inst.operands:
    dest=None;operand=inst.operands[0]
    if operand.type==X86_OP_IMM:dest=operand.imm
    if operand.type==X86_OP_MEM and operand.mem.base==X86_REG_RIP:dest=inst.address+inst.size+operand.mem.disp
    if dest is not None:
     one["dest"]=hex(dest-base)
     one["symbol"]=exp.get(dest-base) or imported.get(dest,"")
    links.append(one)
  callback[slot]={"rva":hex(rva),"range":[hex(a),hex(b)],"instructions":instructions,"links":links}
  print(y,number,"slot",slot,hex(rva),"size",b-a,"links",len(links),flush=True)
  for x in links[:25]:print(" ",x,flush=True)
 out[y]={"BEE_SHA256":hashlib.sha256(raw).hexdigest(),
         "new_shape_command_ID":number,
         "record_rva":row["entry_rva"],
         "callback_factory_plus8":callback[1],
         "callback_execution_plus16":callback[2]}
dest=Path(r"D:\Developer\ShapeLayerAE\results\bee_new_shape_exact_command_table_handlers_2025_2026.json")
dest.write_text(json.dumps({"evidence":"E2-L actual NewVectorLayer command encoded ID to BEE_DoCommand 32byte table +8 and +16 handler compiled code, offline static only","versions":out},indent=2)+"\n")
print("SAVED",dest)
