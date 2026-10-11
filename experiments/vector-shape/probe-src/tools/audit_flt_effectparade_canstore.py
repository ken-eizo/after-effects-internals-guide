"""Decode real FLT_Parade::CanStore admissions in AE2025/AE2026.
Offline PE, no host call.
"""
import pefile,hashlib,json,bisect
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\FLT.dll",0x53580),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\FLT.dll",0x55300)}
out={}
for year,(path,rva) in cfg.items():
 data=Path(path).read_bytes();p=pefile.PE(data=data);base=p.OPTIONAL_HEADER.ImageBase
 ex={e.address:e.name.decode(errors="replace") for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 assert "CanStore@FLT_Parade@@" in ex[rva]
 fs=sorted((f.struct.BeginAddress,f.struct.EndAddress) for f in p.DIRECTORY_ENTRY_EXCEPTION)
 ix=bisect.bisect_right([f[0] for f in fs],rva)-1
 assert ix>=0 and rva<fs[ix][1]
 a,b=fs[ix];md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
 inst=[];refs=[]
 for x in md.disasm(data[p.get_offset_from_rva(a):p.get_offset_from_rva(b)],base+a):
  row={"rva":hex(x.address-base),"m":x.mnemonic,"op":x.op_str}
  if x.operands and x.mnemonic in ("call","jmp","lea"):
   op=x.operands[-1] if x.mnemonic=="lea" else x.operands[0]
   tar=None
   if op.type==X86_OP_IMM:tar=op.imm-base
   if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:tar=x.address+x.size+op.mem.disp-base
   if tar is not None:
    row["target_rva"]=hex(tar)
    row["export"]=ex.get(tar,"")
    if x.mnemonic=="lea":
     try:buf=data[p.get_offset_from_rva(tar):p.get_offset_from_rva(tar)+80]
     except Exception:buf=b""
     for encoding in ("ascii","utf-16-le"):
      lit=buf.split(b"\x00\x00" if encoding=="utf-16-le" else b"\x00",1)[0]
      if encoding=="utf-16-le":continue
      if lit and len(lit)>=4:
       try:row["literal"]=lit.decode(encoding)
       except UnicodeDecodeError:pass
  inst.append(row)
 print(year,"CanStore",hex(rva),"instructions",len(inst),flush=True)
 for x in inst[:85]:print(x["rva"],x["m"],x["op"],x.get("export","")[:110],x.get("literal","")[:60],flush=True)
 out[year]={"sha256":hashlib.sha256(data).hexdigest(),"function_pdata":[hex(a),hex(b)],"instructions":inst}
dest=Path(r"D:\Developer\ShapeLayerAE\results\flt_effectparade_canstore_contract_2025_2026.json")
dest.write_text(json.dumps({"scope":"offline native FLT_Parade CanStore; real host acceptance not yet tested","versions":out},indent=2)+"\n",encoding="utf8")
print("SAVED",dest)
