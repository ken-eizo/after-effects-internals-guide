"""Strict offline verifier: BEE Project font data shutdown before Undo history cleanup.

EXP-SHAPE-104. Inspects ORIGINAL SHA-pinned installed Windows AE2025/2026
BEE.dll imports, function boundaries and x64 machine code; never loads or
calls Adobe DLLs or touches any user After Effects project.
"""
from pathlib import Path
import pefile,capstone,hashlib,json
from capstone.x86_const import X86_OP_IMM,X86_OP_MEM,X86_REG_RIP

ROOT=Path(r"D:\Developer\After Effects Internals Guide")
VERS={
 "2025":{"file":r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",
         "sha":"98c682351e30f38cb7021eaa142f5ec473aea92885e14915d87c157cda971730",
         "project_dtor":0x3ff0c0,"font_cleanup":0x3feff0,"project_undo_field":0x368,
         "font_call":0x3ff016,"recycle_call":0x3ff054,"undo_dtor_call":0x3ff44a,
         "project_font_cleanup_call":0x3ff441, "add_missing":0x4018f0,"growth":0x3fab60},
 "2026":{"file":r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",
         "sha":"5fd8d318456228b9fd2a6733a5758f6b84206b7a8effcba5202957cd27ac680e",
         "project_dtor":0x40f330,"font_cleanup":0x40f260,"project_undo_field":0x370,
         "font_call":0x40f286,"recycle_call":0x40f2c4,"undo_dtor_call":0x40f68a,
         "project_font_cleanup_call":0x40f681,"add_missing":0x411d50,"growth":0x40a9e0}}
C=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);C.detail=True
def unique(a,label):
 assert len(a)==1,(label,len(a),[hex(z.address) for z in a[:8]])
 return a[0]
def which_call(o,z):
 if z.mnemonic!="call" or not z.operands:return None
 v=z.operands[0]
 if v.type==X86_OP_IMM:return ("direct",v.imm-o["base"])
 if v.type==X86_OP_MEM and v.mem.base==X86_REG_RIP:
  return ("iat",z.address+z.size+v.mem.disp-o["base"])
 return None

out={}
for year,config in VERS.items():
 path=Path(config["file"]);blob=path.read_bytes()
 sha=hashlib.sha256(blob).hexdigest()
 assert sha==config["sha"],("Unexpected original Adobe BEE image",year,sha)
 p=pefile.PE(data=blob);b=p.OPTIONAL_HEADER.ImageBase
 pdata={x.struct.BeginAddress:x.struct.EndAddress for x in p.DIRECTORY_ENTRY_EXCEPTION}
 iat={v.address-b:(d.dll.decode(errors="replace").lower(),
                   v.name.decode(errors="replace") if v.name else "")
      for d in p.DIRECTORY_ENTRY_IMPORT for v in d.imports}
 def body(rva):
  assert rva in pdata and 0<pdata[rva]-rva<7000,(year,hex(rva))
  z=list(C.disasm(p.get_data(rva,pdata[rva]-rva),b+rva))
  assert z and z[0].address-b==rva
  return z
 def rva(z):return hex(z.address-b)
 # The same containing holder's +0x118 is read by Project::AddMissingFont.
 # That is an explicit native producer for the cleanup function.
 add=body(config["add_missing"])
 grow=body(config["growth"])
 name="?AddMissingFont@BEE_Project@@QEAAXAEBVTXT_UsedFontData@@@Z"
 exports={z.address:z.name.decode(errors="replace") for z in p.DIRECTORY_ENTRY_EXPORT.symbols if z.name}
 assert exports.get(config["add_missing"])==name, (year,exports.get(config["add_missing"]))
 get_add_holder=unique([z for z in add if z.mnemonic=="mov" and
                z.op_str==f"rbx, qword ptr [rcx + 0x{config['project_undo_field']:x}]"],
                "AddMissingFont uses same Project holder as UndoContext")
 add_tail=unique([z for z in add if z.mnemonic=="lea" and z.op_str=="rcx, [rbx + 0x118]"],
                 "missing font vector object at holder+0x118")
 add_end=unique([z for z in add if z.mnemonic=="mov" and z.op_str=="rax, qword ptr [rbx + 0x120]"],"vector end")
 add_capacity=unique([z for z in add if z.mnemonic=="cmp" and z.op_str=="rax, qword ptr [rbx + 0x128]"],"vector capacity")
 add_ctor=unique([z for z in add if which_call({"base":b},z)
            and which_call({"base":b},z)[0]=="iat"
            and iat.get(which_call({"base":b},z)[1])==
            ("txt.dll","??0TXT_UsedFontData@@QEAA@AEBV0@@Z")],
            "append copies native TXT_UsedFontData")
 add_incr=unique([z for z in add if z.mnemonic=="add" and z.op_str=="qword ptr [rbx + 0x120], 0x88"],"append 136-byte record")
 assert get_add_holder.address<add_end.address<add_capacity.address<add_ctor.address<add_incr.address
 assert add_capacity.address<add_tail.address
 growth_jmp=unique([z for z in add if z.mnemonic=="jmp" and z.operands and
                     z.operands[0].type==X86_OP_IMM and z.operands[0].imm-b==config["growth"]],"full capacity grow")
 assert add_tail.address<growth_jmp.address
 def native_calls(ops,dll,name_prefix):
  return [z for z in ops if which_call({"base":b},z)
          and which_call({"base":b},z)[0]=="iat"
          and (x:=iat.get(which_call({"base":b},z)[1])) is not None
          and x[0]==dll and x[1].startswith(name_prefix)]
 allocate=unique(native_calls(grow,"dvacore.dll","?Allocate@MemoryRecycler@"),"allocate font vector growth")
 copy=[z for z in native_calls(grow,"txt.dll","??0TXT_UsedFontData@@QEAA@AEBV0@@Z")]
 move=native_calls(grow,"txt.dll","??0TXT_UsedFontData@@QEAA@$$QEAV0@@Z")
 destroy=unique(native_calls(grow,"txt.dll","??1TXT_UsedFontData@@QEAA@XZ"),"destroy original moved font")
 grow_recycle=unique(native_calls(grow,"dvacore.dll","?Recycle@MemoryRecycler@"),"recycle old font vector")
 assert len(copy)==1 and len(move)>=1
 assert allocate.address<copy[0].address<move[0].address<destroy.address<grow_recycle.address

 dtor=body(config["project_dtor"])
 font=body(config["font_cleanup"])
 # Project's original pointer field and adjacent +0x118 / +0x10 subobjects.
 undo_field=hex(config["project_undo_field"])
 get_holder=unique([z for z in dtor if z.mnemonic=="mov" and
                   z.op_str==f"rdi, qword ptr [rbx + 0x{config['project_undo_field']:x}]"],
                   "project context holder pointer")
 cleanup_this=unique([z for z in dtor if z.mnemonic=="lea" and z.op_str=="rcx, [rdi + 0x118]"],"holder font subobject")
 cleanup_call=unique([z for z in dtor if which_call({"base":b},z)==("direct",config["font_cleanup"])],"Project calls font helper")
 ctx_this=unique([z for z in dtor if z.mnemonic=="lea" and z.op_str=="rcx, [rdi + 0x10]"],"project UndoContext subobject")
 undo_call=unique([z for z in dtor if z.address-b==config["undo_dtor_call"] and z.mnemonic=="call"],"UndoContext dtor")
 assert get_holder.address<cleanup_this.address<cleanup_call.address<ctx_this.address<undo_call.address
 assert cleanup_call.address-b==config["project_font_cleanup_call"]

 # Verify exact TXT.dll imported destructor, stride, buffer recycling, and
 # standard 3-pointer range state cleared after disposal.
 fonts=unique([z for z in font if which_call({"base":b},z)
           and which_call({"base":b},z)[0]=="iat"
           and iat.get(which_call({"base":b},z)[1])==
           ("txt.dll","??1TXT_UsedFontData@@QEAA@XZ")], "TXT_UsedFontData destructor")
 assert fonts.address-b==config["font_call"]
 advance=unique([z for z in font if z.mnemonic=="add" and z.op_str=="rbx, 0x88"],"136-byte native font record")
 assert fonts.address<advance.address
 loop_end=unique([z for z in font if z.mnemonic=="cmp" and z.op_str=="rbx, rdi" and
                  advance.address<z.address<advance.address+12],"record iteration")
 loop_back=unique([z for z in font if z.mnemonic=="jne" and loop_end.address<z.address<loop_end.address+12],"loop back")
 assert loop_back.operands[0].type==X86_OP_IMM and loop_back.operands[0].imm==fonts.address-3
 recycle=unique([z for z in font if which_call({"base":b},z)
         and which_call({"base":b},z)[0]=="iat"
         and iat.get(which_call({"base":b},z)[1])==
          ("dvacore.dll","?Recycle@MemoryRecycler@allocator@dvacore@@YAXPEAX_K@Z")],"vector backing allocator")
 assert recycle.address-b==config["recycle_call"] and recycle.address>loop_back.address
 reset=[]
 for offset in (""," + 8"," + 0x10"):
  operand=f"qword ptr [rsi{offset}], rax"
  z=unique([j for j in font if j.mnemonic=="mov" and j.op_str==operand],
           "empty triple-pointer vector "+operand)
  assert z.address>recycle.address
  reset.append(rva(z))
 # Project destructor frees containing holder only after Undo history destructor.
 allocsize=unique([z for z in dtor if z.mnemonic=="mov" and z.op_str=="edx, 0x130" and z.address>undo_call.address],"holder size 0x130")
 exprdtor=[z for z in dtor if z.mnemonic=="call" and which_call({"base":b},z)
           and which_call({"base":b},z)[0]=="direct"
           and which_call({"base":b},z)[1] in (0x31ed0,0x316d0)]
 assert len(exprdtor)>=2 and all(z.address>allocsize.address for z in exprdtor)
 out[year]={
  "original_BEE_sha256":sha,
  "missing_font_append":{
   "BEE_Project_AddMissingFont":hex(config["add_missing"]),
   "same_Project_holder_offset":hex(config["project_undo_field"]),
   "vector_start_end_capacity_offsets":["0x118","0x120","0x128"],
   "TXT_UsedFontData_copy_constructor":rva(add_ctor),
   "appended_record_stride_bytes":0x88,
   "growth_fallback_jump":rva(growth_jmp),
   "growth_helper":hex(config["growth"]),
   "growth_Allocate":rva(allocate),
   "growth_copy_constructor":rva(copy[0]),
   "growth_move_constructors":[rva(z) for z in move],
   "growth_original_destructor":rva(destroy),
   "growth_Recycle":rva(grow_recycle)
  },
  "project_destructor":{"entry":hex(config["project_dtor"]),
    "context_holder_offset":undo_field,"font_vector_subobject_offset":"0x118",
    "font_vector_cleanup_call":rva(cleanup_call),
    "undo_context_subobject_offset":"0x10",
    "UndoContext_destructor_call":rva(undo_call),
    "holder_release_size_bytes":0x130,
    "subsequent_expression_engine_destructor_calls":[rva(z) for z in exprdtor]},
  "font_vector_cleanup":{"entry":hex(config["font_cleanup"]),
    "native_element_type":"TXT_UsedFontData",
    "record_stride_bytes":0x88,
    "TXT_DLL_destructor_call":rva(fonts),
    "record_iterator_advance":rva(advance),
    "native_memory_recycler":rva(recycle),
    "reset_vector_start_end_capacity":reset},
  "scope":"E2-L static original installed machine code, not live AE teardown",
  "notes":"The +0x118 holder subobject is font records; not a second UndoContext, task registry, or unknown handler."}
 print("PASS",year,"AddMissingFont -> shared holder+0x118 vector (copy/move/reallocate) -> Project font cleanup -> UndoContext cleanup -> ExpressionEngine",flush=True)
outfile=ROOT/"datasets"/"ae-bee-project-font-vector-pre-undo-shutdown-2025-2026.json"
outfile.write_text(json.dumps({"evidence":"E2-L strict SHA pinned BEE.dll PE static disassembly; no Adobe code executed",
                              "versions":out},indent=2)+"\n",encoding="utf8")
print("DATASET",outfile)
