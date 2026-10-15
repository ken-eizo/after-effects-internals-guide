"""F-VECTOR-106: aelib staged native initialization / reverse teardown.

Strict offline original Windows AE 2025/2026 DLLs. No Adobe APIs executed.
Read-only PE IAT, .pdata and x64 instruction/vectored jump tables.
"""
from pathlib import Path
import hashlib,json,re,struct,subprocess
import pefile,capstone
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP

ROOT=Path(r"D:\Developer\After Effects Internals Guide")
VERS={
 "2025":{"path":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\aelib.dll"),
  "sha":"48331b6c193e8abf495e8119861e63fe06d356be0630ab51e9f9b24e69bec8ff",
  "init":0x6d9b0,"init_table":0x6ed34,"term":0x6edc0,"term_table":0x6f1dc,
  "terminate":0x83220,"backward":0x186d0,"forward":0x18f00},
 "2026":{"path":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files\aelib.dll"),
  "sha":"def5e8a82d84fc12b5043251970331dfdc1d87407a0a4188d9976ca1a3a479bb",
  "init":0x6fd80,"init_table":0x710c4,"term":0x71150,"term_table":0x71570,
  "terminate":0x86b60,"backward":0x15e70,"forward":0x164f0}
}
MODULES={15:("TDB.dll","?TDB_Birth@@","?TDB_Death@@"),
         25:("OM.dll","?OM_Birth@@","?OM_Death@@"),
         27:("FLT.dll","?FLT_Birth@@","?FLT_Death@@"),
         29:("BEE.dll","?BEE_Birth@@","?BEE_Death@@")}
CS=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
CS.detail=True

def one(a,name):
 assert len(a)==1,(name,len(a),a[:6])
 return a[0]
def load(v,c):
 raw=c["path"].read_bytes()
 sha=hashlib.sha256(raw).hexdigest()
 assert sha==c["sha"],("Original Adobe aelib DLL changed",v,sha)
 p=pefile.PE(data=raw)
 b=p.OPTIONAL_HEADER.ImageBase
 funcs={x.struct.BeginAddress:x.struct.EndAddress for x in p.DIRECTORY_ENTRY_EXCEPTION}
 imp={sym.address-b:(mod.dll.decode(errors="replace").lower(),
       sym.name.decode(errors="replace") if sym.name else "")
       for mod in p.DIRECTORY_ENTRY_IMPORT for sym in mod.imports}
 ex={x.address:x.name.decode(errors="replace") for x in p.DIRECTORY_ENTRY_EXPORT.symbols if x.name}
 return {"pe":p,"base":b,"funcs":funcs,"imp":imp,"ex":ex,"sha":sha}
def dis(o,rva,sz):
 rows=list(CS.disasm(o["pe"].get_data(rva,sz),o["base"]+rva))
 assert rows and rows[0].address-o["base"]==rva
 return rows
def fn(o,rva):
 return dis(o,rva,o["funcs"][rva]-rva)
def calltarget(o,i):
 if i.mnemonic not in ("call","jmp"):return None
 op=i.operands[0]
 if op.type==X86_OP_MEM and op.mem.base==X86_REG_RIP:
  return i.address+i.size+op.mem.disp-o["base"]
 if op.type==X86_OP_IMM:return op.imm-o["base"]
def stage_table(o,start):
 p=o["pe"]
 a=[struct.unpack("<i",p.get_data(start+4*i,4))[0] for i in range(35)]
 assert len(a)==35 and all(0x1000<=j<0x140000 for j in a),a
 return a
def import_calls(o,code,mod,prefix):
 return [z for z in code if z.mnemonic=="call" and
         (target:=calltarget(o,z)) is not None and
         o["imp"].get(target,("",""))[0]==mod.lower() and
         o["imp"][target][1].startswith(prefix)]
def body_of_case(o,table,stage,fn_end):
 a=table[stage-1]
 others=[x for x in table if x>a]
 end=min(others) if others else fn_end
 assert 0<end-a<1600,(stage,hex(a),hex(end))
 return dis(o,a,end-a)
def exact_export(o,prefix,rva):
 names=[n for x,n in o["ex"].items() if n.startswith(prefix) and x==rva]
 assert len(names)==1,(prefix,hex(rva),names)
def direct_call(o,src,dst):
 hits=[z for z in fn(o,src) if z.mnemonic=="call" and calltarget(o,z)==dst]
 return one(hits,"direct call at "+hex(src)+" -> "+hex(dst))

data={}
for v,c in VERS.items():
 o=load(v,c)
 exact_export(o,"??EInitIterator@aelib@@",c["init"])
 exact_export(o,"??FTerminateIterator@aelib@@",c["term"])
 exact_export(o,"?Terminate@aelib@@",c["terminate"])
 exact_export(o,"?backward@TerminateIterator@aelib@@",c["backward"])
 exact_export(o,"?forward@InitIterator@aelib@@",c["forward"])
 init=fn(o,c["init"]);term=fn(o,c["term"])
 assert any(z.mnemonic=="cmp" and ("0x22" in z.op_str) for z in init)
 assert any(z.mnemonic=="cmp" and z.op_str=="r14d, 0x22" for z in term)
 assert any(z.mnemonic=="lea" and z.op_str=="r14d, [rax - 1]" for z in term)
 assert any(z.mnemonic=="mov" and z.op_str=="dword ptr [rsi], r14d" for z in term)
 assert any(z.mnemonic=="lea" and ("+ 1" in z.op_str) for z in init),("init must increment stage",v)
 ti=stage_table(o,c["init_table"]);td=stage_table(o,c["term_table"])
 assert len(set(ti))>=25 and len(set(td))>=25
 assert all(ti[i]<ti[i+1] for i in (14,24,26,28) if i+1<35)
 assert all(td[i]<td[i+1] for i in (14,24,26,28) if i+1<35)
 iterator=direct_call(o,c["backward"],c["term"])
 fwd=direct_call(o,c["forward"],c["init"])
 outer=direct_call(o,c["terminate"],c["term"])
 outerbody=fn(o,c["terminate"])
 assert any(z.mnemonic=="test" and z.op_str=="eax, eax" for z in outerbody if z.address>outer.address),v
 assert any(z.mnemonic in ("jne","jnz") and z.address>outer.address for z in outerbody),v
 assert any(z.mnemonic=="cmp" and z.op_str=="eax, edi" for z in fn(o,c["backward"])),v
 assert any(z.mnemonic in ("jl","jge") for z in fn(o,c["backward"])),v

 moddata={}
 for stage,(mod,birth,death) in MODULES.items():
  b=one(import_calls(o,body_of_case(o,ti,stage,c["term"]-1),mod,birth),
        v+" stage "+str(stage)+" "+birth)
  d=one(import_calls(o,body_of_case(o,td,stage,o["funcs"][c["term"]]),mod,death),
        v+" stage "+str(stage)+" "+death)
  moddata[mod.split(".")[0]]=dict(stage=stage,
     birth_case_entry=hex(ti[stage-1]),birth_call=hex(b.address-o["base"]),
     death_case_entry=hex(td[stage-1]),death_call=hex(d.address-o["base"]),
     birth_import=o["imp"][calltarget(o,b)][1],
     death_import=o["imp"][calltarget(o,d)][1])
 # The "general plugin setdown" is stage 32, earlier than native BEE death
 # in a full descending shutdown.
 st=32
 sc=body_of_case(o,td,st,o["funcs"][c["term"]])
 sd=one(import_calls(o,sc,"mee.dll","?SetdownGeneralPlugins@@"),
        v+" SetdownGeneralPlugins stage32")
 aegpd=one(import_calls(o,sc,"mee.dll","?MEE_AEGP_Death@@"),
           v+" AEGP death stage32")
 aegpt=one(import_calls(o,sc,"mee.dll","?MEE_AEGP_Terminate@@"),
           v+" AEGP termination stage32")
 assert aegpd.address<aegpt.address<sd.address
 assert st>max(MODULES)
 assert 32>29>27>25>15

 data[v]=dict(original_aelib_sha256=o["sha"],
  native_init_iterator=c["init"],native_term_iterator=c["term"],
  native_init_case_table=hex(c["init_table"]),
  native_term_case_table=hex(c["term_table"]),
  termination_iterator_decrements_to_previous_stage=True,
  init_forward_direct_call=hex(fwd.address-o["base"]),
  terminate_backward_direct_call=hex(iterator.address-o["base"]),
  aelib_Terminate_direct_dispatch=hex(outer.address-o["base"]),
  full_shutdown_stage_execution="descending module stage numbers: 35 to 1, subject to initialized stage and mode/branch guards",
  modules=moddata,
  general_plugin_setdown=dict(stage=32,aegp_death=hex(aegpd.address-o["base"]),
                              aegp_terminate=hex(aegpt.address-o["base"]),
                              general_plugins_setdown=hex(sd.address-o["base"])),
  limitations=["No runtime host shutdown performed","This ordering is conditional on visited stages",
               "SetdownGeneralPlugins does not prove physical unloading of plugin DLL",
               "Does not prove live Stream or Undo task objects all released before factory unregister",
               "This is an Adobe first-party internal dispatcher, not a public extension API"])
 print("PASS",v,"forward init stage 15/TDB,25/OM,27/FLT,29/BEE;",
       "reverse termination + stage32 plugin setdown before BEE",flush=True)
 for name,m in moddata.items():
  print("  ",name,m["stage"],m["birth_call"],m["death_call"],flush=True)
 print("  plugin-setdown",hex(sd.address-o["base"]))

dst=ROOT/"datasets"/"ae-aelib-native-staged-birth-reverse-death-2025-2026.json"
dst.write_text(json.dumps({"evidence":"E2-L original installed aelib.dll, SHA-pinned x64 switch dispatch, RIP-IAT, native iterator & main termination",
 "source":"Read-only PE inspection. Native Adobe functions never executed.",
 "versions":data},indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("RECEIPT",dst)
