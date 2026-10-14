from pathlib import Path
import re,json,subprocess,hashlib,struct,pefile,capstone
roots={"2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files"),
"2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")}
cases={
"BEE_PaintStrokesGroup":{"canonical_owner":"BEE_StrokesGroupBase","children":["BEE_StreamGroupName_PAINT_ATOM"]},
"BEE_TextAnimatorStreamGroup":{"canonical_owner":"BEE_TextAnimatorStreamGroup","children":["BEE_StreamGroupName_TEXT_SELECTORS","BEE_StreamGroupName_TEXT_ANIMATOR_PROPERTIES"]},
"BEE_TextSelectorsStreamGroup":{"canonical_owner":"BEE_TextSelectorsStreamGroup","children":["BEE_StreamGroupName_TEXT_SELECTOR","BEE_StreamGroupName_TEXT_WIGGLY_SELECTOR","BEE_StreamGroupName_TEXT_LEVELS_SELECTOR","BEE_StreamGroupName_TEXT_EXPRESSIBLE_SELECTOR"]},
"BEE_TextAnimatorPropertiesStreamGroup":{"canonical_owner":"BEE_TextAnimatorPropertiesStreamGroup","children":["BEE_StreamName_TEXT_POSITION","BEE_StreamName_TEXT_SCALE","BEE_StreamName_TEXT_OPACITY"]}
}
def symbols(path):
 s=subprocess.run(["dumpbin","/exports",str(path)],capture_output=True,text=True,errors="replace",check=True).stdout
 out={}
 for ln in s.splitlines():
  m=re.match(r"\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\S+)",ln)
  if m:out[int(m.group(1),16)]=m.group(2)
 return out
def find(e,x):
 vals=[r for r,n in e.items() if n.startswith(x)]
 assert len(vals)==1,(x,vals)
 return vals[0]
cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);cs.detail=True
res={}
for yr,root in roots.items():
 path=root/"BEE.dll";pe=pefile.PE(str(path));base=pe.OPTIONAL_HEADER.ImageBase;ex=symbols(path)
 assert len(ex)>10000
 pd={x.struct.BeginAddress:x.struct.EndAddress for x in pe.DIRECTORY_ENTRY_EXCEPTION}
 iat={x.address-base:(d.dll.decode(errors='replace'),x.name.decode(errors='replace') if x.name else str(x.ordinal)) for d in pe.DIRECTORY_ENTRY_IMPORT for x in d.imports}
 yout={}
 for klass,spec in cases.items():
  vt=find(ex,"??_7"+klass+"@@6B@")
  canptr=struct.unpack("<Q",pe.get_data(vt+56*8,8))[0]-base
  fillptr=struct.unpack("<Q",pe.get_data(vt+57*8,8))[0]-base
  assert fillptr==find(ex,"?FillInCanonicalUILayout@"+spec["canonical_owner"]+"@@")
  b=pe.get_data(canptr,6)
  assert b[:2]==b"\xff\x25"
  iatptr=canptr+6+struct.unpack("<i",b[2:])[0]
  assert iat[iatptr][0].lower()=="tdb.dll" and iat[iatptr][1].startswith("?CanStore@TDB_StreamGroup@@")
  children={}
  raw=list(cs.disasm(pe.get_data(fillptr,pd[fillptr]-fillptr),base+fillptr))
  for name in spec["children"]:
   rv=find(ex,"?"+name+"@@")
   refs=[hex(i.address-base) for i in raw for o in i.operands if o.type==capstone.x86.X86_OP_MEM and o.mem.base==capstone.x86.X86_REG_RIP and i.address+i.size+o.mem.disp-base==rv]
   assert refs,(yr,klass,name)
   children[name]=refs
  calls=[]
  for i in raw:
   if i.mnemonic!='call':continue
   for o in i.operands:
    if o.type==capstone.x86.X86_OP_MEM and o.mem.base==capstone.x86.X86_REG_RIP:
     at=i.address+i.size+o.mem.disp-base
     if at in iat and iat[at][0].lower()=="tdb.dll" and iat[at][1].startswith("?GetCanonicalStream@TDB_StreamBase@@"):calls.append(hex(i.address-base))
  assert len(calls)>=len(spec["children"]),(yr,klass,"GetCanonicalStream missing")
  yout[klass]={"vtable_rva":hex(vt),"canstore_slot":56,"canstore_import_thunk_rva":hex(canptr),
  "canonical_ui_slot":57,"canonical_fill_rva":hex(fillptr),"canonical_children_symbol_references":children,
  "canonical_get_stream_calls":calls}
  print(yr,klass,"PASS canonical kinds",len(children),"calls",len(calls))
 res[yr]={"BEE_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"classes":yout}
out=Path(r"D:\Developer\ShapeLayerAE\labs\paint_native_properties_audit\native_paint_text_group_canonical_policy_2025_2026.json")
out.write_text(json.dumps(res,indent=2)+"\n",encoding="utf-8")
print("PASS 2 versions x 4 classes; saved",out)
