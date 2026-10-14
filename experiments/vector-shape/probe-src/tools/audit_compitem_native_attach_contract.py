"""Static analysis only: BEE_CompItem native attach; no host execution."""
from pathlib import Path
import bisect, hashlib, json, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86_const import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP
DLLS = {
  "2025": (r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll", {"attach":0x392120,"partial_attach":0x3920F0,"clone_and_attach":0x2E20E0}),
  "2026": (r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll", {"attach":0x39D4D0,"partial_attach":0x39D4A0,"clone_and_attach":0x2EB090})
}
out = {}
for year,(fname, funcs) in DLLS.items():
 raw=Path(fname).read_bytes()
 pe=pefile.PE(data=raw)
 base=pe.OPTIONAL_HEADER.ImageBase
 xports={int(s.address):s.name.decode(errors="replace") for s in pe.DIRECTORY_ENTRY_EXPORT.symbols if s.name}
 imports={i.address:mod.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for mod in pe.DIRECTORY_ENTRY_IMPORT for i in mod.imports if i.name}
 pdata=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in pe.DIRECTORY_ENTRY_EXCEPTION)
 starts=[a for a,b in pdata]
 md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
 result={}
 for tag,rva in funcs.items():
  idx=bisect.bisect_right(starts,rva)-1
  assert idx>=0 and rva<pdata[idx][1],(year,tag)
  a,z=pdata[idx]
  assert z-a<60000,(year,tag,a,z)
  insns=list(md.disasm(raw[pe.get_offset_from_rva(a):pe.get_offset_from_rva(a)+(z-a)],base+a))
  rows=[]
  for ins in insns:
   row={"rva":hex(ins.address-base),"asm":ins.mnemonic+" "+ins.op_str}
   if ins.mnemonic in ("call","jmp") and ins.operands:
    op=ins.operands[0]
    target=op.imm if op.type==X86_OP_IMM else ins.address+ins.size+op.mem.disp if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP else None
    if target is not None:
     row["target_rva"]=hex(target-base);row["target_name"]=xports.get(target-base,imports.get(target,""))
    else:row["indirect_call"]=True
   rows.append(row)
  # Archive only decisive instruction evidence, not whole Adobe function bodies.
  selected={"mov rbx, rdx", "mov rsi, rcx", "mov ebp, dword ptr [rbx + 0x2d8]",
            "mov ebp, dword ptr [rbx + 0x26c]", "call qword ptr [rax + 0x278]",
            "call qword ptr [rax + 0x550]", "call qword ptr [rax + 0x560]",
            "inc dword ptr [rsi + 0x3c8]", "inc dword ptr [rsi + 0x420]",
            "lock xadd dword ptr [rbx + 8], eax", "lock xadd dword ptr [rbx + 0xc], edi"}
  if tag=="attach":
   evidence=[r for r in rows if r["asm"] in selected or r["asm"] in {f"mov edx, {v}" for v in (1,2,5,7)}]
  else:
   evidence=[r for r in rows if "AttachLayerToCompOnly@" in r.get("target_name","") or "TDB_StreamBase" in r.get("target_name","")]
  result[tag]={"entry":hex(rva),"begin":hex(a),"end":hex(z),"size":z-a,"decoded_instruction_count":len(rows),"instructions":evidence}
  print(f"=== {year} {tag} start={hex(rva)} pdata=[{hex(a)},{hex(z)}) insns={len(rows)}")
  for r in rows[:170] if tag!="clone_and_attach" else rows[:65]:
   print(r["rva"],r["asm"],r.get("target_name","")[:160])
 out[year]={"SHA256":hashlib.sha256(raw).hexdigest(),"functions":result}
dst=Path(__file__).resolve().parents[4] / "datasets" / "ae-bee-compitem-attach-owner-contract-2025-2026.json"
dst.write_text(json.dumps({"scope":"Pinned local Adobe BEE.dll offline PE executable disassembly; no private API calls","versions":out},indent=2)+"\n",encoding="utf-8")
print("OUTPUT",dst)
