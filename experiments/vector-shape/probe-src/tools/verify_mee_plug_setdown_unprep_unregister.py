"""F-VECTOR-107: native general plugin setdown, PLUG unprep/unregister and unload boundary.

Original SHA-pinned Windows AE2025/26 MEE + PLUG DLLs, static-only.
Do not execute Adobe private code or mutate user projects.
"""
from pathlib import Path
import hashlib,json,struct
import pefile,capstone
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP

ROOT=Path(r"D:\Developer\After Effects Internals Guide")
VERS={
"2025":{
 "mee":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\MEE.dll",
 "mee_sha":"f7ca4f0975c7a3562c8192057f08c8a27a2c3c40e625bbc5a521eccd17e3b953",
 "plug":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\PLUG.dll",
 "plug_sha":"460e5148e1066bfd5602fc780dcecbcf946d063dd91400f75f0fce6d95aa943c",
 "setdown":0x54960,"unprep":0x8b70,"unregister":0x8d80,"plug_death":0x4f30},
"2026":{
 "mee":r"D:\Adobe\Adobe After Effects 2026\Support Files\MEE.dll",
 "mee_sha":"0196b1f45339ac9621f9d334a86ac7341c9197b0e971993a4a34f0789afcf6c1",
 "plug":r"D:\Adobe\Adobe After Effects 2026\Support Files\PLUG.dll",
 "plug_sha":"d9021a1f12e479fc162b3ea282c96644acd58f28ca23944f0caa9ecfcd7bef3f",
 "setdown":0x49ce0,"unprep":0x1cdd0,"unregister":0x1cfd0,"plug_death":0x19970}
}
CS=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);CS.detail=True
def openpe(path,expected):
 raw=Path(path).read_bytes();sha=hashlib.sha256(raw).hexdigest()
 assert sha==expected,(path,"Adobe installed DLL changed",sha)
 p=pefile.PE(data=raw);b=p.OPTIONAL_HEADER.ImageBase
 ex={x.address:x.name.decode(errors="replace") for x in p.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
 im={j.address-b:(imp.dll.decode(errors="replace").lower(),j.name.decode(errors="replace") if j.name else "")
     for imp in p.DIRECTORY_ENTRY_IMPORT for j in imp.imports}
 fn={x.struct.BeginAddress:x.struct.EndAddress for x in p.DIRECTORY_ENTRY_EXCEPTION}
 return dict(p=p,b=b,ex=ex,im=im,fn=fn,sha=sha)
def sym(o,prefix,expected_rva):
 assert o["ex"].get(expected_rva,"").startswith(prefix),(prefix,hex(expected_rva),o["ex"].get(expected_rva))
def block(o,rva):
 assert rva in o["fn"]
 seq=list(CS.disasm(o["p"].get_data(rva,o["fn"][rva]-rva),o["b"]+rva))
 assert seq and seq[0].address-o["b"]==rva
 return seq
def iat(o,op):
 if op.mnemonic!="call" or not op.operands:return ("","")
 v=op.operands[0]
 if v.type==X86_OP_MEM and v.mem.base==X86_REG_RIP:
  return o["im"].get(op.address+op.size+v.mem.disp-o["b"],("",""))
 return ("","")
def impcalls(o,code,mod,prefix):
 return [z for z in code if iat(o,z)[0]==mod and iat(o,z)[1].startswith(prefix)]
def one(x,msg):
 assert len(x)==1,(msg,len(x))
 return x[0]
def at(o,z):return hex(z.address-o["b"])
def ins(code,mnem,s):
 return [z for z in code if z.mnemonic==mnem and z.op_str==s]
receipts={}
for year,c in VERS.items():
 m=openpe(c["mee"],c["mee_sha"])
 p=openpe(c["plug"],c["plug_sha"])
 sym(m,"?SetdownGeneralPlugins@@",c["setdown"])
 sym(p,"?PLUG_UnprepRoutine@@",c["unprep"])
 sym(p,"?PLUG_UnregisterRoutine@@",c["unregister"])
 sym(p,"?PLUG_Death@@",c["plug_death"])
 setcode=block(m,c["setdown"])
 # Confirm conditional per-record callback: both layouts use the same
 # native offsets relative to the beginning of the plugin record.
 cb=one(ins(setcode,"call","rax"),"Setdown indirect registered callback")
 if year=="2025":
  assert any(z.mnemonic=="mov" and z.op_str=="rax, qword ptr [rbx - 0x58]" for z in setcode)
  ref=one(ins(setcode,"mov","rcx, qword ptr [rbx - 0xa0]"),"callback refcon+0x10")
  guard=one(ins(setcode,"cmp","byte ptr [rbx], 0"),"prepared flag+0xb0")
  clear=one(ins(setcode,"mov","byte ptr [rbx], 0"),"prepared flag zero")
 else:
  assert any(z.mnemonic=="mov" and z.op_str=="rax, qword ptr [rbx + 0x58]" for z in setcode)
  ref=one(ins(setcode,"mov","rcx, qword ptr [rbx + 0x10]"),"callback refcon+0x10")
  guard=one(ins(setcode,"cmp","byte ptr [rbx + 0xb0], 0"),"prepared flag+0xb0")
  clear=one(ins(setcode,"mov","byte ptr [rbx + 0xb0], 0"),"prepared flag zero")
 unp=one(impcalls(m,setcode,"plug.dll","?PLUG_UnprepRoutine@@"),"PLUG Unprep imported")
 assert any(z.mnemonic=="add" and z.op_str=="rbx, 0xb8" for z in setcode)
 assert ref.address<cb.address<guard.address<clear.address<unp.address

 # PLUG_UnprepRoutine performs lock / descriptor operations and indirect
 # PLUG_RoutineDesc vtable method: not a direct FreeLibrary import.
 unprep=block(p,c["unprep"])
 locks=impcalls(p,unprep,"dvacore.dll","?Lock@RecursiveMutex@")
 unlocks=impcalls(p,unprep,"dvacore.dll","?Unlock@RecursiveMutex@")
 assert locks and unlocks
 lock=locks[0];unlock=unlocks[-1]
 routine=one(ins(unprep,"call","qword ptr [rax + 0x30]"),"Unprep routine virtual method")
 assert lock.address<routine.address<unlock.address
 assert not impcalls(p,unprep,"kernel32.dll","FreeLibrary")
 assert not impcalls(m,setcode,"kernel32.dll","FreeLibrary")
 # AEGP termination has distinct register removal apart from Setdown.
 term_addr=one([r for r,name in m["ex"].items() if name.startswith("?MEE_AEGP_Terminate@@")],"MEE_AEGP_Terminate")
 term=block(m,term_addr)
 unregister=one(impcalls(m,term,"plug.dll","?PLUG_UnregisterRoutine@@"),"AEGP PLUG unregister")
 term_unprep=one(impcalls(m,term,"plug.dll","?PLUG_UnprepRoutine@@"),"AEGP PLUG unprep")
 assert term_unprep.address<unregister.address
 # PLUG_Death also unregisters descriptors at a later module stage,
 # distinct from invoking the general plugin setdown callback.
 plugdeath=block(p,c["plug_death"])
 directunreg=[z for z in plugdeath if z.mnemonic=="call" and z.operands and
      z.operands[0].type==X86_OP_IMM and
      z.operands[0].imm-p["b"]==c["unregister"]]
 assert len(directunreg)==1
 receipts[year]=dict(
  original_MEE_sha256=m["sha"],original_PLUG_sha256=p["sha"],
  MEE_SetdownGeneralPlugins=dict(entry=hex(c["setdown"]),record_stride="0xb8",
   callback_pointer_offset="0x58",callback_refcon_offset="0x10",prep_flag_offset="0xb0",
   callback_call=at(m,cb),prepared_flag_test=at(m,guard),
   prepared_flag_clear=at(m,clear),PLUG_UnprepRoutine_imported_call=at(m,unp)),
  PLUG_UnprepRoutine=dict(entry=hex(c["unprep"]),recursive_mutex_lock=at(p,lock),
    descriptor_virtual_call_0x30=at(p,routine),recursive_mutex_unlock=at(p,unlock),
    direct_FreeLibrary_import_call=False),
  MEE_AEGP_Terminate=dict(entry=hex(term_addr),
     PLUG_UnprepRoutine=at(m,term_unprep),PLUG_UnregisterRoutine=at(m,unregister)),
  PLUG_Death=dict(entry=hex(c["plug_death"]),
    PLUG_UnregisterRoutine_direct_call=at(p,directunreg[0]),
    aelib_module_death_stage=14),
  limitations=[
    "No physical module unloading time proven",
    "An indirect callback can itself release module state; not inspected",
    "PLUG_UnprepRoutine can call further private helpers and PLUG_RoutineDesc virtual dispatch",
    "No foreign native C++ TDB_StreamBase registration or AEP roundtrip",
    "No Adobe code executed; native compiled success/conditional control flow only"
  ])
 print("PASS",year,"MEE callback → flag clear → PLUG_Unprep; AEGP Terminate unregister; PLUG Death unregister",flush=True)

out=ROOT/"datasets"/"ae-mee-plug-general-plugin-setdown-unprep-unregister-2025-2026.json"
out.write_text(json.dumps({"status":"PASS strict 2025/2026 original SHA pinned static PE",
"evidence":"E2-L real DLL code/exports/IAT; zero Adobe private API calls",
"versions":receipts},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("SAVED",out)
