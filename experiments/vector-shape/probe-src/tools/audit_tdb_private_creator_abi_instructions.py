"""Read-only full function disassembly around TDB native registry.
No runtime private calls, no injection; output restricted to selected
functions, with exact pinned RVA and decoded exports/imports.
"""
import pefile,subprocess,re,bisect,hashlib
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
FILES={
"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll",
"2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll"}
QUERIES=["RegisterFactoryFunc@TDB_StreamFactory@@",
"UnregisterFactoryFunc@TDB_StreamFactory@@",
"Register@TDB_ScRegisterStreams@@","UnregisterAll@TDB_ScRegisterStreams@@",
"CreateStream@TDB_StreamFactory@@","RegisterCanonicalInstance@TDB_StreamFactory@@",
"UnregisterCanonicalInstance@TDB_StreamFactory@@",
"GetCanonicalInstance@TDB_StreamFactory@@"]
pat=re.compile(r"^\s*\d+\s+[A-Fa-f0-9]+\s+([0-9a-fA-F]{8})\s+(\S+)")
for ver,file in FILES.items():
 print("\n========= AE",ver,flush=True)
 data=Path(file).read_bytes(); pe=pefile.PE(data=data); base=pe.OPTIONAL_HEADER.ImageBase
 print("SHA256",hashlib.sha256(data).hexdigest(),flush=True)
 exports={}
 for line in subprocess.run(["dumpbin","/exports",file],check=True,capture_output=True,text=True,errors="replace").stdout.splitlines():
  m=pat.match(line)
  if m:exports[int(m.group(1),16)]=m.group(2)
 imp={i.address:e.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace")
      for e in pe.DIRECTORY_ENTRY_IMPORT for i in e.imports if i.name}
 pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in pe.DIRECTORY_ENTRY_EXCEPTION)
 starts=[x[0] for x in pdata];dis=Cs(CS_ARCH_X86,CS_MODE_64);dis.detail=True
 for query in QUERIES:
  hits=[(rva,name) for rva,name in exports.items() if query in name]
  if len(hits)!=1: print("QUERY_UNIQUE_FAIL",query,len(hits));continue
  rva,name=hits[0];i=bisect.bisect_right(starts,rva)-1
  low,high=pdata[i] if i>=0 and rva<pdata[i][1] else (rva,rva+300)
  print("\n====",query,"RVA",hex(rva),"REGION",hex(low),hex(high),"LEN",high-low,flush=True)
  if high-low>1200:high=low+1200
  buf=data[pe.get_offset_from_rva(low):pe.get_offset_from_rva(high)]
  for ins in dis.disasm(buf,base+low):
   target=None
   if ins.mnemonic in ("call","jmp") and ins.operands:
    op=ins.operands[0]
    if op.type==X86_OP_IMM:target=op.imm
    elif op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
     target=ins.address+ins.size+op.mem.disp
   label=(exports.get(target-base) or imp.get(target) or "") if target else ""
   print(hex(ins.address-base),ins.mnemonic,ins.op_str,("| "+label[:120]) if label else "",flush=True)
