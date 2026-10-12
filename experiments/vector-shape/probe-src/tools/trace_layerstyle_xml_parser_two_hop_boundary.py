"""Trace 2-hop direct caller boundary of native BEE LayerStyle XML
parser entry wrappers. Constrain result to actual .pdata code regions.
Read-only installed Adobe binary PE inspection, not injection.
"""
from pathlib import Path
import struct,bisect,json,hashlib
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
cfg={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
             (0x28fa80,0x2959e0)),
     "2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",
             (0x298cb0,0x29e630))}
res={}
for ver,(file,targets) in cfg.items():
 b=Path(file).read_bytes();p=pefile.PE(data=b);base=p.OPTIONAL_HEADER.ImageBase
 fns=sorted((i.struct.BeginAddress,i.struct.EndAddress) for i in p.DIRECTORY_ENTRY_EXCEPTION)
 starts=[x[0] for x in fns]
 syms={x.address:x.name.decode(errors="replace") for x in p.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
 md=Cs(CS_ARCH_X86,CS_MODE_64)
 nodes=[]
 for tar in targets:
  i=bisect.bisect_right(starts,tar)-1;assert i>=0 and tar<fns[i][1]
  begin,end=fns[i]
  ins=[(hex(x.address-base),x.mnemonic,x.op_str) for x in md.disasm(b[p.get_offset_from_rva(begin):p.get_offset_from_rva(end)],base+begin)]
  hits=[]
  for sec in p.sections:
   if not sec.Characteristics & 0x20000000:continue
   data=sec.get_data()
   for opcode in (0xe8,0xe9):
    off=0
    while True:
     k=data.find(bytes([opcode]),off)
     if k<0:break
     off=k+1
     if k+5>len(data):break
     site=sec.VirtualAddress+k
     if site+5+struct.unpack_from("<i",data,k+1)[0]!=tar:continue
     j=bisect.bisect_right(starts,site)-1
     sp=fns[j] if j>=0 and site<fns[j][1] else None
     hits.append({"site":hex(site),"kind":"CALL" if opcode==0xe8 else "JMP",
       "own_function":hex(sp[0]) if sp else None,
       "export":syms.get(sp[0],"") if sp else ""})
  nodes.append({"wrapper_rva":hex(tar),"instructions":ins,"xrefs":hits})
  print(ver,hex(tar),"xref",len(hits),"caller locations",[(h["site"],h["own_function"],h["export"][:50]) for h in hits[:25]],flush=True)
 res[ver]={"sha256":hashlib.sha256(b).hexdigest(),"wrappers":nodes}
dest=Path(r"D:\Developer\ShapeLayerAE\results\bee_layerstyle_xml_parser_2hop_entry_boundary_2025_2026.json")
dest.write_text(json.dumps({"evidence":"E2-L two-hop direct relative call/jmp PE scan; no indirect dispatch proof","versions":res},indent=2)+"\n")
print("SAVED",dest)
