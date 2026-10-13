"""Trace BEE_Layer::CloneAndAttach clone-object creator import across AE2025/26.
Offline only; IAT and CRT thunks are interpreted, no Adobe process calls.
"""
from pathlib import Path
import pefile,struct,json,hashlib
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
config={"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x2e20e0,0x2e20fe,0xceacd4),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x2eb090,0x2eb0a3,0xd3be04)}
out={}
for year,(path,entry,site,thunk) in config.items():
 data=Path(path).read_bytes();p=pefile.PE(data=data,fast_load=True)
 p.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"],
   pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT"],
   pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"]])
 base=p.OPTIONAL_HEADER.ImageBase
 syms={}
 for attr in ("DIRECTORY_ENTRY_IMPORT","DIRECTORY_ENTRY_DELAY_IMPORT"):
  for dll in getattr(p,attr,[]):
   for imp in dll.imports:
    if imp.name:syms[imp.address-base]=dll.dll.decode(errors="replace")+"!"+imp.name.decode(errors="replace")
 dec=Cs(CS_ARCH_X86,CS_MODE_64);dec.detail=True
 inst=list(dec.disasm(data[p.get_offset_from_rva(entry):p.get_offset_from_rva(entry)+50],base+entry))
 cl=next(i for i in inst if i.address-base==site)
 assert cl.mnemonic=="call" and cl.operands[0].type==X86_OP_MEM
 assert cl.operands[0].mem.base==X86_REG_RIP
 iat=site+cl.size+cl.operands[0].mem.disp
 thunkbytes=data[p.get_offset_from_rva(thunk):p.get_offset_from_rva(thunk)+6]
 assert thunkbytes[:2]==b"\xff\x25"
 secondiat=thunk+6+struct.unpack("<i",thunkbytes[2:])[0]
 payload={"BEE_SHA256":hashlib.sha256(data).hexdigest(),
 "clone_entry":hex(entry),"original_object_clone_import_site":hex(site),
 "original_object_clone_IAT":hex(iat),"clone_import":syms.get(iat),
 "postclone_thunk":hex(thunk),"postclone_IAT":hex(secondiat),
 "postclone_import":syms.get(secondiat),
 "dll_import_count":len(syms)}
 out[year]=payload
 print(year,payload,flush=True)
dest=Path(r"D:\Developer\ShapeLayerAE\results\bee_clone_and_attach_import_contract_2025_2026.json")
dest.write_text(json.dumps({"evidence":"E2-L native PE x64 imports, not in-host foreign clone","versions":out},indent=2)+"\n")
print("SAVED",dest,flush=True)
