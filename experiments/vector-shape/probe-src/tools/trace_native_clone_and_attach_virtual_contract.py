"""Cross-version BEE_Layer::CloneAndAttach method code and its
virtual copy-vs-owner contract. Native disk read only."""
from pathlib import Path
import pefile,bisect,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x2e20e0),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x2eb090)}
out={}
for year,(name,entry) in cfg.items():
 data=Path(name).read_bytes()
 p=pefile.PE(data=data,fast_load=True)
 p.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"],pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXCEPTION"]])
 b=p.OPTIONAL_HEADER.ImageBase
 pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in p.DIRECTORY_ENTRY_EXCEPTION)
 bounds=next((a,z) for a,z in pdata if a<=entry<z)
 exps={int(x.address):x.name.decode(errors="replace") for x in p.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
 cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
 rows=[];calls=[];indirect=[]
 for i in cs.disasm(data[p.get_offset_from_rva(bounds[0]):p.get_offset_from_rva(bounds[1])],b+bounds[0]):
  row={"at":hex(i.address-b),"ins":i.mnemonic+" "+i.op_str}
  rows.append(row)
  if i.mnemonic not in ("call","jmp"):continue
  target=None
  if i.operands and i.operands[0].type==X86_OP_IMM:
   target=i.operands[0].imm-b
  if target is not None:
   row["target"]=hex(target);row["symbol"]=exps.get(target,"")
   calls.append(row)
  else:indirect.append(row)
 print("==",year,hex(bounds[0]),hex(bounds[1]),"direct",len(calls),"indirect",len(indirect),flush=True)
 for row in rows:print(row["at"],row["ins"],row.get("symbol","")[:90],flush=True)
 out[year]={"entry":hex(entry),"end":hex(bounds[1]),"instructions":rows,"direct_calls":calls,"indirect_calls":indirect}
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_clone_and_attach_native_virtual_contract_2025_2026.json")
dst.write_text(json.dumps({"scope":"E2-L native cloneAndAttach compiled executable code, no live host invocation","versions":out},indent=2)+"\n")
print("SAVED",dst,flush=True)
