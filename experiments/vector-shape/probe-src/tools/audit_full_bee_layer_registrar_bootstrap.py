"""Pinned offline audit of direct BEE native stream registrar callsites.
No Adobe DLL is loaded or executed. Counts only instruction-boundary-verified calls.
"""
from pathlib import Path
import pefile,hashlib,json,bisect,re,subprocess
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM
config={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll"}
families=["BEE_Layer","BEE_AVLayer","BEE_TextLayer","BEE_VectorLayer","BEE_CameraLayer","BEE_LightLayer","BEE_ModelLayer","BEE_ParametricMeshLayer","BEE_MaterialOverrideLayer"]
out={}
for year,filename in config.items():
 raw=Path(filename).read_bytes();pe=pefile.PE(data=raw)
 base=pe.OPTIONAL_HEADER.ImageBase
 # BEE exports exceed the default pefile 8192-symbol parsing cap: use full dumpbin listing.
 names={}
 dump=subprocess.run(["dumpbin","/exports",filename],capture_output=True,text=True,errors="replace",check=True).stdout
 for record in dump.splitlines():
  m=re.match(r"^\s*\d+\s+[0-9a-fA-F]+\s+([0-9a-fA-F]{8})\s+(\S+)",record)
  if m:names[int(m.group(1),16)]=m.group(2)
 assert len(names)>12000,(year,len(names))
 targets={rva:name for rva,name in names.items() if any("RegisterStreams@"+cls+"@@" in name or "UnregisterStreams@"+cls+"@@" in name for cls in families)}
 # Call sites above establish these specific shared bootstrap function boundaries.
 bootstrap={"2025":(0x36dd90,0x36def0),"2026":(0x3787b0,0x378910)}
 for i,rva in enumerate(bootstrap[year]):targets[rva]=f"LOCAL_RegisterStreams_bootstrap_{i}"
 assert len(targets)>=9,(year,targets)
 print('FULL_EXPORTS',year,len(names),'REGISTRAR_TARGETS',len(targets),flush=True)
 section=next(s for s in pe.sections if s.Name.rstrip(b"\x00")==b".text")
 start=section.VirtualAddress;buf=section.get_data();ends=start+len(buf)
 pdata=sorted((v.struct.BeginAddress,v.struct.EndAddress) for v in pe.DIRECTORY_ENTRY_EXCEPTION)
 begins=[p[0] for p in pdata];md=Cs(CS_ARCH_X86,CS_MODE_64);md.detail=True
 grouped={}
 checked_functions={}
 forbyte=0
 for opcode in (b"\xe8",b"\xe9"):
  pos=buf.find(opcode)
  while pos>=0 and pos+5<=len(buf):
   src=start+pos
   rel=int.from_bytes(buf[pos+1:pos+5],"little",signed=True)
   target=src+5+rel
   if target in targets:
    idx=bisect.bisect_right(begins,src)-1
    if idx>=0 and src<pdata[idx][1]:
     a,b=pdata[idx]
     if b-a <= 150000:
      if a not in checked_functions:
       opcodes=set()
       binary=raw[pe.get_offset_from_rva(a):pe.get_offset_from_rva(a)+(b-a)]
       for ins in md.disasm(binary,base+a):
        if ins.mnemonic in ("call","jmp") and ins.operands and ins.operands[0].type==X86_OP_IMM:
         opcodes.add((ins.address-base,ins.operands[0].imm-base,ins.mnemonic))
       checked_functions[a]=opcodes
      kind="call" if opcode==b"\xe8" else "jmp"
      if (src,target,kind) in checked_functions[a]:
       signature=names.get(a,"")
       grouped.setdefault(targets[target],[]).append({"site":hex(src),"caller_function_rva":hex(a),"caller_export":signature,"branch":kind})
   pos=buf.find(opcode,pos+1)
 result={"sha256":hashlib.sha256(raw).hexdigest(),"targets":{}}
 for rva,n in sorted(targets.items()):
  rows=grouped.get(n,[])
  print(year,hex(rva),n[:95],"verified direct xrefs",len(rows))
  for row in rows[:25]:print(" ",row["site"],row["caller_function_rva"],row["caller_export"][:120])
  result["targets"][n]={"rva":hex(rva),"verified_direct_calls":rows}
 out[year]=result
dest=Path(__file__).resolve().parents[4] / "datasets" / "ae-bee-full-layer-family-registration-bootstrap-2025-2026.json"
dest.write_text(json.dumps({"scope":"E2-L exact PE relative call instruction boundary verification, not exhaustive indirect calls","versions":out},indent=2)+"\n",encoding="utf-8")
print("OUTPUT",dest)
