"""Read-only pinned aelib -> BEE_Birth/Death IAT callsite audit."""
from pathlib import Path
import pefile,hashlib,json,bisect
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
paths={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\aelib.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\aelib.dll"}
out={}
for year,path in paths.items():
 raw=Path(path).read_bytes();pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
 imports={i.address:mod.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for mod in pe.DIRECTORY_ENTRY_IMPORT for i in mod.imports if i.name and mod.dll.lower()==b"bee.dll"}
 target={a:n for a,n in imports.items() if "?BEE_Birth@@" in n or "?BEE_Death@@" in n}
 assert len(target)==2,(year,target)
 section=next(s for s in pe.sections if s.Name.rstrip(b"\x00")==b".text")
 start=section.VirtualAddress;code=section.get_data()
 pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in pe.DIRECTORY_ENTRY_EXCEPTION)
 begins=[a for a,b in pdata];md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
 verified={}
 cache={}
 for opcode in (b"\xff\x15",b"\xff\x25"):
  at=code.find(opcode)
  while at>=0 and at+6<=len(code):
   source=start+at
   slot=base+source+6+int.from_bytes(code[at+2:at+6],"little",signed=True)
   if slot in target:
    idx=bisect.bisect_right(begins,source)-1
    if idx>=0 and source<pdata[idx][1]:
     a,b=pdata[idx]
     if b-a<=80000:
      if a not in cache:
       chunk=raw[pe.get_offset_from_rva(a):pe.get_offset_from_rva(a)+(b-a)]
       rows=[]
       for ins in md.disasm(chunk,base+a):
        if ins.mnemonic in ("call","jmp") and ins.operands and ins.operands[0].type==X86_OP_MEM and ins.operands[0].mem.base==X86_REG_RIP:
         ref=ins.address+ins.size+ins.operands[0].mem.disp
         rows.append((ins.address-base,ref,ins.mnemonic))
       cache[a]=rows
      kind="call" if opcode==b"\xff\x15" else "jmp"
      if (source,slot,kind) in cache[a]:
       verified.setdefault(target[slot],[]).append({"site":hex(source),"caller_function_rva":hex(a),"kind":kind,"IAT_VA":hex(slot)})
   at=code.find(opcode,at+1)
 print("YEAR",year,"BEE IMPORTS",len(imports))
 for iat,name in target.items():
  rows=verified.get(name,[])
  print(name[:90],"IAT",hex(iat),"verified refs",len(rows))
  for row in rows[:20]:print(" ",row)
 out[year]={"aelib_sha256":hashlib.sha256(raw).hexdigest(),"imports":{name:{"iat_va":hex(a),"verified_code_references":verified.get(name,[])} for a,name in target.items()}}
dst=Path(__file__).resolve().parents[4]/"datasets"/"ae-aelib-bee-lifecycle-crossmodule-2025-2026.json"
dst.write_text(json.dumps({"scope":"Two installed aelib.dll images, only direct IAT RIP-relative CALL/JMP references; no dynamic runtime claims","versions":out},indent=2),encoding="utf-8")
print("OUTPUT",dst)
