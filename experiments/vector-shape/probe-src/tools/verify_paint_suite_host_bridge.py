from pathlib import Path
import re,struct,hashlib,json,subprocess,pefile,capstone,bisect
VERSIONS={
 "2025":Path(r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files"),
 "2026":Path(r"D:\Adobe\Adobe After Effects 2026\Support Files")
}
LEA_RE=re.compile(rb'[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]([\x00-\xff]{4})')
def all_exports(p):
 t=subprocess.run(['dumpbin','/exports',str(p)],capture_output=True,text=True,errors='replace',check=True).stdout
 ex={}
 for line in t.splitlines():
  m=re.match(r'\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\S+)',line)
  if m:ex[int(m.group(1),16)]=m.group(2)
 return ex
def ref(ins,base):
 for op in ins.operands:
  if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP:
   return ins.address+ins.size+op.mem.disp-base
 return None
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
out={}
for year,root in VERSIONS.items():
 host=root/'AfterFXLib.dll'; aex=root/'Required'/'Paint.aex'; paint_bucket=root/'Plug-ins'/'Effects'/'PaintBucket.aex'
 assert all(x.exists() for x in (host,aex,paint_bucket)),year
 hp=pefile.PE(str(host));bp=hp.OPTIONAL_HEADER.ImageBase
 exports=all_exports(host)
 eps=[rva for rva,name in exports.items() if name.startswith('?PaintEffectEntryPoint@@')]
 assert len(eps)==1,(year,eps)
 ep=eps[0]
 data=host.read_bytes();soff=data.find(b'Paint Suite\x00')
 assert soff>0,year
 suite_rva=hp.get_rva_from_offset(soff)
 cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);cs.detail=True
 xrefs=[]
 for sec in hp.sections:
  if sec.Name.rstrip(b'\x00')!=b'.text':continue
  blob=sec.get_data()
  for m in LEA_RE.finditer(blob):
   disp=struct.unpack('<i',m.group(1))[0]
   at=sec.VirtualAddress+m.start()
   if at+7+disp==suite_rva:xrefs.append(at)
 assert len(xrefs)>=1,(year,xrefs)
 pdata=sorted((x.struct.BeginAddress,x.struct.EndAddress) for x in hp.DIRECTORY_ENTRY_EXCEPTION)
 starts=[r for r,_ in pdata]
 evidence=[]
 for at in xrefs:
  j=bisect.bisect_right(starts,at)-1
  assert j>=0
  func_start,func_end=pdata[j]
  insns=list(cs.disasm(hp.get_data(func_start,func_end-func_start),bp+func_start))
  idx=[i for i,v in enumerate(insns) if v.address-bp==at][0]
  neighborhood=insns[max(0,idx-10):idx+7]
  suite_ref=[v for v in neighborhood if v.address-bp==at]
  assert suite_ref and ref(suite_ref[0],bp)==suite_rva
  tabs=[]
  for v in neighborhood:
   if v.mnemonic=='lea' and v.op_str.startswith('rax, ') and (target:=ref(v,bp)) is not None:
    raw=hp.get_data(target,8)
    if len(raw)==8 and struct.unpack('<Q',raw)[0]==bp+ep:
     tabs.append((v.address-bp,target))
  assert tabs,(year,hex(at),'no host dispatch table with PaintEffectEntryPoint')
  c=[v for v in insns[idx:idx+6] if v.mnemonic=='call']
  assert c,(year,'no adjacent host register call')
  evidence.append({
   'host_registration_function':hex(func_start),
   'suite_name_reference_rva':hex(at),
   'suite_name_literal_rva':hex(suite_rva),
   'function_table_lea_rva':hex(tabs[-1][0]),
   'function_table_rva':hex(tabs[-1][1]),
   'function_table_first_pointer_rva':hex(struct.unpack('<Q',hp.get_data(tabs[-1][1],8))[0]-bp),
   'nearby_registration_call_rva':hex(c[0].address-bp),
   'nearby_call_operand':c[0].op_str
  })
 ap=pefile.PE(str(aex));ab=ap.OPTIONAL_HEADER.ImageBase
 symbols={e.name.decode():e.address for e in ap.DIRECTORY_ENTRY_EXPORT.symbols if e.name}
 a_pdata={x.struct.BeginAddress:x.struct.EndAddress for x in ap.DIRECTORY_ENTRY_EXCEPTION}
 name_off=aex.read_bytes().find(b'Paint Suite\x00')
 assert name_off>0
 a_name_rva=ap.get_rva_from_offset(name_off)
 wrappers=[]
 for key in ('EffectMainExtra','EffectMainExtra2'):
  assert key in symbols
  rva=symbols[key]
  insns=list(cs.disasm(ap.get_data(rva,a_pdata.get(rva,rva+0x80)-rva),ab+rva))
  calls=[v.operands[0].imm-ab for v in insns if v.mnemonic=='call' and v.operands and v.operands[0].type==capstone.x86.X86_OP_IMM]
  assert calls
  wrappers.append({'export':key,'rva':hex(rva),'common_callback_rva':hex(calls[0])})
 assert wrappers[0]['common_callback_rva']==wrappers[1]['common_callback_rva']
 common=int(wrappers[0]['common_callback_rva'],16)
 insns=list(cs.disasm(ap.get_data(common,a_pdata.get(common,common+0x700)-common),ab+common))
 suite_uses=[hex(i.address-ab) for i in insns if ref(i,ab)==a_name_rva]
 assert suite_uses,(year,'AEX no suite name use')
 dlls={d.dll.decode().lower() for d in ap.DIRECTORY_ENTRY_IMPORT}
 assert 'bee.dll' not in dlls and 'tdb.dll' not in dlls
 assert b'Paint Suite' not in paint_bucket.read_bytes()
 out[year]={
  'host':{'path':str(host),'sha256':digest(host),'paint_effect_entrypoint_rva':hex(ep),'suite_registrations':evidence},
  'paint_tool_effect_aex':{'path':str(aex),'sha256':digest(aex),'imports':sorted(dlls),'wrappers':wrappers,'suite_name_reference_in_effect_callback':suite_uses},
  'not_paint_bucket':{'path':str(paint_bucket),'sha256':digest(paint_bucket)}
 }
 print(year,'PASS PaintSuite registration xrefs',len(evidence),'host table points to PaintEffectEntryPoint',hex(ep),'Paint.aex delegating',suite_uses)
 print('  host',evidence)
doc=Path(r'D:\Developer\ShapeLayerAE\labs\paint_native_properties_audit\paint_suite_host_bridge_verified_2025_2026.json')
doc.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf8')
print('PASS 2/2. Evidence saved:',doc)
