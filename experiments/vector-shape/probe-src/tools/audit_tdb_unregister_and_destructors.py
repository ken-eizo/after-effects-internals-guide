"""Selected complete unregistration, creator ownership and cleanup paths."""
from pathlib import Path
import pefile,subprocess,re,bisect,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP
files={"2025":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\TDB.dll",
       "2026":r"D:\Adobe\Adobe After Effects 2026\Support Files\TDB.dll"}
targets=["UnregisterFactoryFunc_NullOK@TDB_StreamFactory@@",
         "??1TDB_ScRegisterStreams@@","??1TDB_StreamFactory@@",
         "UnregisterCanonicalInstance@TDB_StreamFactory@@",
         "RegisterCanonicalInstance@TDB_StreamFactory@@",
         "??0TDB_ScRegisterStreams@@QEAA@PEAVTDB_StreamFactory@@",
         "IsRegistered@TDB_ScRegisterStreams@@"]
pat=re.compile(r"^\s*\d+\s+[0-9A-Fa-f]+\s+([0-9a-fA-F]{8})\s+(\S+)")
for ver,filepath in files.items():
 raw=Path(filepath).read_bytes();pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
 syms={}
 for line in subprocess.run(["dumpbin","/exports",filepath],capture_output=True,text=True,errors="replace",check=True).stdout.splitlines():
  m=pat.match(line)
  if m:syms[int(m.group(1),16)]=m.group(2)
 it={i.address:mod.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace") for mod in pe.DIRECTORY_ENTRY_IMPORT for i in mod.imports if i.name}
 pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in pe.DIRECTORY_ENTRY_EXCEPTION)
 lows=[x[0] for x in pdata];decoder=Cs(CS_ARCH_X86,CS_MODE_64);decoder.detail=True
 print("==============",ver,flush=True)
 for target in targets:
  for addr,name in syms.items():
   if target not in name:continue
   k=bisect.bisect_right(lows,addr)-1
   start,end=pdata[k] if k>=0 and addr<pdata[k][1] else (addr,addr+90)
   print("\n---",name,"RVA",hex(addr),"START",hex(start),"BYTES",end-start,flush=True)
   for j,ins in enumerate(decoder.disasm(raw[pe.get_offset_from_rva(start):pe.get_offset_from_rva(start)+min(end-start,2200)],base+start)):
    if j>360:break
    call=""
    if ins.mnemonic in ("call","jmp") and ins.operands:
     op=ins.operands[0];dest=None
     if op.type==X86_OP_IMM:dest=op.imm
     elif op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:dest=ins.address+ins.size+op.mem.disp
     if dest:call=syms.get(dest-base) or it.get(dest) or ""
    print(hex(ins.address-base),ins.mnemonic,ins.op_str,("| "+call[:112]) if call else "",flush=True)
