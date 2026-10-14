"""Offline BEE_Birth argument-provenance boundary check in Adobe aelib.
No host execution: bounded machine instructions around proven calls only.
"""
from pathlib import Path
import hashlib,json,bisect,pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
root=Path(__file__).resolve().parents[4]
config={
"2025":{"file":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\aelib.dll","sites":[0x6e272,0x6f6cf],"immediate":"0xf0b2603"},
"2026":{"file":r"D:\Adobe\Adobe After Effects 2026\Support Files\aelib.dll","sites":[0x70647,0x71bc8],"immediate":"0xf118657"}}
out={}
for year,c in config.items():
 raw=Path(c["file"]).read_bytes();p=pefile.PE(data=raw)
 base=p.OPTIONAL_HEADER.ImageBase
 pdata=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in p.DIRECTORY_ENTRY_EXCEPTION)
 starts=[x[0] for x in pdata];md=Cs(CS_ARCH_X86,CS_MODE_64)
 sites=[]
 for site in c["sites"]:
  ix=bisect.bisect_right(starts,site)-1
  a,b=pdata[ix];assert a<=site<b
  code=raw[p.get_offset_from_rva(a):p.get_offset_from_rva(a)+(b-a)]
  instr=[{"rva":hex(i.address-base),"instruction":i.mnemonic+" "+i.op_str} for i in md.disasm(code,base+a)]
  k=next(j for j,v in enumerate(instr) if v["rva"]==hex(site))
  before=instr[max(0,k-10):k]
  after=instr[k:k+3]
  assert instr[k]["instruction"].startswith("call qword ptr [rip +"),(year,site)
  assert any(v["instruction"]=="mov r8d, "+c["immediate"] for v in before),(year,site)
  assert any(v["instruction"].startswith("mov r9d, dword ptr [rip +") for v in before)
  assert any(v["instruction"].startswith("lea rdx, ") for v in before)
  assert any(v["instruction"].startswith("mov rcx, ") for v in before)
  assert instr[k+1]["instruction"]=="test eax, eax"
  assert any(v["instruction"]=="sete al" for v in before)
  sites.append({"site":hex(site),"function_rva":hex(a),"precall_evidence":before,
                "call_and_return_check":after,"r8_immediate":c["immediate"]})
  print("PASS",year,hex(site),"version_constant",c["immediate"],"arg_regs=rcx,rdx,r8,r9","result checked")
 out[year]={"aelib_sha256":hashlib.sha256(raw).hexdigest(),"sites":sites}
dest=root/"datasets"/"ae-aelib-bee-birth-argument-gates-2025-2026.json"
dest.write_text(json.dumps({"scope":"Offline bounded native argument setup; no semantic proof of contents of string/map argument","versions":out},indent=2)+"\n",encoding="utf-8")
print("OUTPUT",dest)
