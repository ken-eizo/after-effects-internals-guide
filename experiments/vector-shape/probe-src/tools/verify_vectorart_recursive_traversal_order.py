"""Read-only PE evidence: BEE native VectorArt materializer traverses authored
children in ascending indexed order, distinct from final rendering/compositing.
Requires exact installed 2025 / 2026 builds.
"""
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_64
import pefile,hashlib,json
cfg={
 "2025":(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\BEE.dll",0x6ec3c0,0x6ec63e),
 "2026":(r"D:\Adobe\Adobe After Effects 2026\Support Files\BEE.dll",0x710790,0x7109ea)}
allres={}
for year,(path,begin,end) in cfg.items():
 raw=Path(path).read_bytes();pe=pefile.PE(data=raw);base=pe.OPTIONAL_HEADER.ImageBase
 code=list(Cs(CS_ARCH_X86,CS_MODE_64).disasm(raw[pe.get_offset_from_rva(begin):pe.get_offset_from_rva(end)],base+begin))
 ins=[(hex(x.address-base),x.mnemonic+" "+x.op_str) for x in code]
 def unique(pattern):
  m=[(r,asm) for r,asm in ins if asm==pattern]
  assert len(m)==1,(year,pattern,m)
  return m[0][0]
 def find(pattern):
  m=[(r,asm) for r,asm in ins if asm==pattern]
  assert m,(year,pattern)
  return m
 initialization=unique("xor esi, esi")
 child_count=unique("call qword ptr [rax + 0x168]")
 compare=unique("cmp esi, eax")
 get_child=unique("call qword ptr [rax + 0x190]")
 positions=find("mov edx, esi")
 position=next(r for r,asm in positions if int(child_count,16)<int(r,16)<int(get_child,16))
 inc=unique("inc esi")
 order=[initialization,child_count,compare,position,get_child,inc]
 assert [int(x,16) for x in order]==sorted(int(x,16) for x in order),order
 assert any("call 0x1806ec3c0" in x for _,x in ins) if year=="2025" else any("call 0x180710790" in x for _,x in ins)
 # The evaluator helper called for individual non-group child streams:
 evaluator="0x6ecd40" if year=="2025" else "0x711040"
 assert any(asm=="call 0x180"+evaluator[2:] for _,asm in ins)
 allres[year]={"BEE_SHA256":hashlib.sha256(raw).hexdigest(),
  "recursive_traversal_rva":hex(begin),"recursive_helper_bytes":end-begin,
  "loop_counter_initialization":initialization,
  "native_virtual_child_count_slot":0x168,
  "native_virtual_child_index_slot":0x190,
  "loop_comparison":compare,
  "child_index_argument_from_increasing_counter":position,
  "virtual_child_lookup_site":get_child,
  "counter_increment_site":inc,
  "evaluator_helper_rva":evaluator,
  "group_branch_recurses":True,
  "proven_stream_child_iteration":"ascending index 0,1,2,... until count",
  "render_stack_compositing_order_proven":False,
  "AE_Pen_and_custom_type_supported":False}
 print("PASS",year, "VectorArt source traversal ascending indexed children",order,flush=True)
target=Path(r"D:\Developer\ShapeLayerAE\results\bee_native_vectorart_indexed_child_traversal_verified_2025_2026.json")
target.write_text(json.dumps({"scope":"E2-L actual BEE.dll machine-code traversal order, *not* proof of final fill/stroke draw order","versions":allres},indent=2)+"\n")
print("SAVED",target)
