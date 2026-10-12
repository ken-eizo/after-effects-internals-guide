"""Pin exact native BEE owner factory and generic TDB property-insertion bridge.
Read actual AE2025/2026 export targets / bounded assembly only.
No plugin loaded, no private functions executed.
"""
from pathlib import Path
import bisect,pefile,hashlib,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_OP_IMM,X86_REG_RIP
cfg={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
     "2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
classes=[
"?Create@BEE_VectorLayer@@",
"?CreateLayerFromType@BEE_Layer@@",
"?AddProperty@BEE_LayerSet@@"
]
out={}
for year,path in cfg.items():
 data=Path(path).read_bytes();p=pefile.PE(data=data);base=p.OPTIONAL_HEADER.ImageBase
 exports={e.name.decode(errors="replace"):e.address for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 names={rva:sym for sym,rva in exports.items()}
 imps={e.address:entry.dll.decode(errors="replace")+"!"+e.name.decode(errors="replace")
       for entry in p.DIRECTORY_ENTRY_IMPORT for e in entry.imports if e.name}
 pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 start=[a for a,b in pdata]
 dis=Cs(CS_ARCH_X86,CS_MODE_64);dis.detail=True
 findings={}
 for clazz in classes:
  hits=[(symbol,rva) for symbol,rva in exports.items() if symbol.startswith(clazz)]
  assert len(hits)==1,(year,clazz,hits)
  symbol,entry=hits[0]
  k=bisect.bisect_right(start,entry)-1
  assert k>=0 and entry<pdata[k][1],(year,clazz,hex(entry))
  a,b=pdata[k]
  lines=[];calls=[];cmp=[]
  for i in dis.disasm(data[p.get_offset_from_rva(a):p.get_offset_from_rva(b)],base+a):
   row={"rva":hex(i.address-base),"asm":i.mnemonic+" "+i.op_str}
   if i.mnemonic in ("call","jmp") and i.operands:
    op=i.operands[0];address=None
    if op.type==X86_OP_IMM:address=op.imm
    if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:address=i.address+i.size+op.mem.disp
    row["target"]=imps.get(address) or names.get(address-base,"") if address is not None else ""
    calls.append(row)
   if i.mnemonic in ("cmp","test") and len(cmp)<80:cmp.append(row)
   if len(lines)<90:lines.append(row)
  findings[clazz]={"export":symbol,"entry_rva":hex(entry),"function_start":hex(a),"function_end":hex(b),
      "native_bytes":b-a,"calls":calls,"first_instructions":lines,"comparisons":cmp}
  print(year,clazz,"size",b-a,"calls",len(calls),flush=True)
  for v in calls[:32]:print(" ",v["rva"],v["target"][:145],v["asm"],flush=True)
 out[year]={"BEE_SHA256":hashlib.sha256(data).hexdigest(),"factories":findings}
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_vector_owner_factory_vs_generic_layer_dispatch_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L exact installed native BEE x64 BEE_VectorLayer::Create, fixed BEE_Layer::CreateLayerFromType, and BEE_LayerSet::AddProperty static call graphs","versions":out},indent=2)+"\n")
print("SAVED",dst)
