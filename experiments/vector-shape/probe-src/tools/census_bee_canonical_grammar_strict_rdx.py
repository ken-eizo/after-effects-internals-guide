from pathlib import Path
import re,subprocess,hashlib,json,collections
import pefile,capstone
roots={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")}
outroot=Path(__file__).resolve().parents[4]/"datasets"
def symbols(path):
 txt=subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True).stdout
 x={}
 for ln in txt.splitlines():
  m=re.match(r"\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\S+)",ln)
  if m:x[int(m.group(1),16)]=m.group(2)
 return x
result={}
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);cs.detail=True
for year,root in roots.items():
 p=root/"BEE.dll";pe=pefile.PE(str(p));base=pe.OPTIONAL_HEADER.ImageBase
 ex=symbols(p)
 assert len(ex)>10000
 imports={x.address-base:(d.dll.decode(errors="replace"),x.name.decode(errors="replace") if x.name else str(x.ordinal))
 for d in pe.DIRECTORY_ENTRY_IMPORT for x in d.imports}
 pdata={x.struct.BeginAddress:x.struct.EndAddress for x in pe.DIRECTORY_ENTRY_EXCEPTION}
 records={}
 candidates=[(rv,sym) for rv,sym in ex.items() if sym.startswith("?FillInCanonicalUILayout@")]
 assert len(candidates)>=90
 for rv,sym in candidates:
  end=pdata.get(rv,rv+0x800)
  if not (0<end-rv<100000):
   continue
  insns=list(cs.disasm(pe.get_data(rv,end-rv),base+rv))
  # Native TDB child canonical lookup: identify the actual GetCanonicalStream import call,
  # then extract the most recent RIP-relative reference to an exported BEE derived MatchName.
  # IMPORTANT: Vector Shape classes do not use BEE_StreamName_ globals.
  # They use ?StreamName_*@BEE_VectorStream@@6... names, and were undercounted.
  child_calls=[]
  match_lookups=0
  for idx,ins in enumerate(insns):
   if ins.mnemonic!='call':continue
   targets=[]
   for op in ins.operands:
    if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP:
     targets.append(ins.address+ins.size+op.mem.disp-base)
   if not any(target in imports and imports[target][0].lower()=="tdb.dll"
    and imports[target][1].startswith("?GetCanonicalStream@TDB_StreamBase@@") for target in targets):
    continue
   match_lookups+=1
   match=None
   # x64 ABI: GetCanonicalStream's second argument is in RDX.
   # Search back only until the most recent RDX definition or preceding CALL.
   # Earlier labels may refer to unrelated operations and MUST NOT be guessed.
   for prev in reversed(insns[max(0,idx-20):idx]):
    if prev.mnemonic=='call':break
    if not prev.operands or prev.operands[0].type!=capstone.x86.X86_OP_REG:continue
    dst=cs.reg_name(prev.operands[0].reg)
    if dst not in ('rdx','edx','dx','dl','dh'):continue
    if prev.mnemonic=='lea' and dst=='rdx':
     for op in prev.operands[1:]:
      if op.type!=capstone.x86.X86_OP_MEM or op.mem.base!=capstone.x86.X86_REG_RIP:continue
      t=prev.address+prev.size+op.mem.disp-base
      name=ex.get(t,'')
      if name.startswith(('?BEE_StreamGroupName_','?BEE_StreamName_','?StreamName_','?StreamGroupName_')):
       match={'child_symbol':name.split('@@')[0],'match_symbol_rva':hex(t),
       'reference_rva':hex(prev.address-base),'canonical_lookup_call_rva':hex(ins.address-base),
       'proof':'direct_lea_rdx_before_GetCanonicalStream_without_intervening_call'}
    break
   if match:child_calls.append(match)
  typename=sym.split("?FillInCanonicalUILayout@",1)[1].split("@@")[0]
  records[typename]={"method_symbol":sym,"method_rva":hex(rv),"method_size":end-rv,"canonical_lookup_calls":match_lookups,
   "identified_canonical_children":child_calls,"unmatched_canonical_lookup_count":match_lookups-len(child_calls)}
 count=sum(len(v["identified_canonical_children"]) for v in records.values())
 families={}
 for family in ("Paint","Text","Vector","Layer"):
  fam=[(n,v) for n,v in records.items() if family.lower() in n.lower()]
  families[family]={"method_count":len(fam),"recognized_canonical_edges":sum(len(v["identified_canonical_children"]) for _,v in fam)}
 result[year]={"BEE_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"method_count":len(records),
  "identified_canonical_edges":count,"families":families,"groups":records}
 print(year,"methods",len(records),"direct recognized edges",count,"families",families)
 for key in ('BEE_StrokesGroupBase','BEE_TextAnimatorStreamGroup','BEE_TextSelectorsStreamGroup','VectorsStreamGroup@BEE_VectorStream'):
  if key in records:print("  ",key,records[key]["canonical_lookup_calls"],[x["child_symbol"] for x in records[key]["identified_canonical_children"]][:22])
 assert len(records)>=90
 assert 'BEE_StrokesGroupBase' in records and any("PAINT_ATOM" in x["child_symbol"] for x in records["BEE_StrokesGroupBase"]["identified_canonical_children"])
 assert 'BEE_TextSelectorsStreamGroup' in records and len(records['BEE_TextSelectorsStreamGroup']['identified_canonical_children'])>=4
out=outroot/"ae-bee-canonical-grammar-strict-rdx-2025-2026.json"
out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
print("PASS two AE versions; dataset",out)
