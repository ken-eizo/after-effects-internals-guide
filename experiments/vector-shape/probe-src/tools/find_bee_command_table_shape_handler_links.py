"""Scan 32-byte native BEE command table executable handlers for calls/jumps
to exported CmdNewVectorLayer, shared worker, and relevant command routers.
PE-only with exact Capstone instruction boundary in native .text.
"""
from pathlib import Path
import pefile,json,bisect
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
cfg={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
tbl=json.load(open(r"D:\Developer\ShapeLayerAE\results\bee_native_command_table_32byte_entries_2025_2026.json"))["versions"]
out={}
for year,path in cfg.items():
 blob=Path(path).read_bytes();p=pefile.PE(data=blob);base=p.OPTIONAL_HEADER.ImageBase
 exp={e.address:e.name.decode(errors="replace") for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 target={rva:name for rva,name in exp.items() if name.startswith(("?BEE_CmdNewVectorLayer@@","?BEE_CmdNewLayer@@","?BEE_DoCommand@@"))}
 target[0x667610 if year=="2025" else 0x682f90]="shared_new_layer_worker"
 pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 starts=[a for a,b in pdata]
 dis=Cs(CS_ARCH_X86,CS_MODE_64);dis.detail=True
 found=[];examples=[]
 for row in tbl[year]["entries"]:
  for col in (1,2):
   q=row["pointers_rva"][col]
   if not q:continue
   addr=int(q,16)
   k=bisect.bisect_right(starts,addr)-1
   a,z=pdata[k] if k>=0 and addr<pdata[k][1] else (addr,addr+160)
   calls=[]
   for x in dis.disasm(blob[p.get_offset_from_rva(a):p.get_offset_from_rva(z)],base+a):
    if x.mnemonic not in ("call","jmp") or not x.operands:continue
    v=x.operands[0];t=None
    if v.type==X86_OP_IMM:t=v.imm-base
    if t in target:calls.append({"site":hex(x.address-base),"target":target[t]})
   if calls:
    item={"cmd_idx":row["index"],"handler_slot":col,"handler_rva":hex(addr),"matching_calls":calls}
    found.append(item)
   if row["index"] in (1,15,45,100) and col==2:
    examples.append({"cmd_idx":row["index"],"handler_rva":hex(addr),"native_function_range":[hex(a),hex(z)]})
 print(year,"Handlers directly referencing known creation and command targets:",len(found),flush=True)
 for r in found:print(" ",r,flush=True)
 out[year]={"direct_native_shape_or_command_handlers":found,"sample_handler_facts":examples}
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_native_command_table_shape_handler_link_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L disassembled BEE static native command entry +8/+16 function pointers with direct native calls; no runtime calls","versions":out},indent=2)+"\n")
print("SAVED",dst)
