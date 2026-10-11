"""Two-release machine-code proof of the native DynamicStreamEffectsParser
group creation/registration pipeline. No host APIs called or patched.
"""
from pathlib import Path
import pefile,json,hashlib,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
from capstone.x86_const import X86_OP_MEM,X86_REG_RIP
bins={
"2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
        0x2f6800,0xe3960,0x2f6c01,0x2f6c21,0x2f6c2d),
"2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",
        0x2ff440,0xe9d20,0x2ff81b,0x2ff83b,0x2ff847)}
proof={}
for year,(file,end_start,creator,gate_site,create_site,register_site) in bins.items():
 data=Path(file).read_bytes();p=pefile.PE(data=data)
 base=p.OPTIONAL_HEADER.ImageBase
 syms={e.name.decode(errors="replace"):e.address for e in p.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 obj=next((n for n in syms if n.startswith("??_7DynamicStreamEffectsParser@BEE@ae@@6B@")))
 off=syms[obj]
 slots={}
 for name,offset in (("allow",0x98),("hidden",0xa0),("create",0xb0)):
  ptr=struct.unpack_from("<Q",data,p.get_offset_from_rva(off)+offset)[0]
  r=ptr-base
  slots[name]={"rva":hex(r),"symbol":next((n for n,a in syms.items() if a==r),"")}
 assert slots["create"]["rva"]==hex(creator)
 assert "CreateEffectGroup@DynamicStreamEffectsParser" in slots["create"]["symbol"]
 assert "AllowMultipleEffects@DynamicStreamEffectsParser" in slots["allow"]["symbol"]
 body=data[p.get_offset_from_rva(creator):p.get_offset_from_rva(creator)+5]
 assert body[:3]==bytes.fromhex("33c0c3"),(year,body.hex())
 cs=Cs(CS_ARCH_X86,CS_MODE_64);cs.detail=True
 region=list(cs.disasm(data[p.get_offset_from_rva(end_start):p.get_offset_from_rva(register_site+6)],base+end_start))
 lookup={i.address-base:i for i in region}
 def op(rva,frag):
  x=lookup[rva]; assert frag in x.op_str,(year,hex(rva),x.mnemonic,x.op_str);return x
 assert op(gate_site,"[rax + 0x98]").mnemonic=="call"
 assert op(create_site,"[rax + 0xb0]").mnemonic=="call"
 assert lookup[create_site+6].mnemonic=="mov" and lookup[create_site+6].op_str=="rdx, rax"
 assert lookup[create_site+9].mnemonic=="mov" and lookup[create_site+9].op_str=="rcx, rsi"
 call=lookup[register_site];assert call.mnemonic=="call"
 assert call.operands[0].type==X86_OP_MEM and call.operands[0].mem.base==X86_REG_RIP
 iat=call.address+call.size+call.operands[0].mem.disp
 imports={i.address:lib.dll.decode(errors="replace")+"!"+i.name.decode(errors="replace")
          for lib in p.DIRECTORY_ENTRY_IMPORT for i in lib.imports if i.name}
 target=imports.get(iat,"")
 assert "TDB.dll!?RegisterCanonicalInstance@TDB_StreamFactory@@" in target,(year,target)
 proof[year]={"sha256":hashlib.sha256(data).hexdigest(),"vtable_rva":hex(off),
   "slots":slots,"EndEffect":hex(end_start),
   "gate_call":hex(gate_site),"creator_call":hex(create_site),
   "canonical_instance_register_call":hex(register_site),
   "register_import":target,"base_creator_returns_null":True,
   "in_host_custom_group_created":False}
 print("PASS",year,": gate -> virtual creator -> canonical register, base returns nullptr",flush=True)
dst=Path(r"D:\Developer\ShapeLayerAE\results\bee_dynamic_effect_native_group_creation_chain_verified_2025_2026.json")
dst.write_text(json.dumps({"evidence":"E2-L pinned x64 BEE native code/RTTI exports, no host execution","versions":proof},indent=2)+"\n",encoding="utf-8")
print("SAVED",dst)
