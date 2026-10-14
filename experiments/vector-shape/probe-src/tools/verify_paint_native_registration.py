from pathlib import Path
import hashlib,json,re,subprocess,pefile,capstone
versions={
 '2025':Path(r'C:\Program Files\Adobe\Adobe After Effects 2025\Support Files'),
 '2026':Path(r'D:\Adobe\Adobe After Effects 2026\Support Files')
}
def exports(path):
 raw=subprocess.run(['dumpbin','/exports',str(path)],capture_output=True,text=True,errors='replace',check=True).stdout
 m={}
 for line in raw.splitlines():
  x=re.match(r'\s*\d+\s+[0-9A-F]+\s+([0-9A-F]{8})\s+(\S+)',line)
  if x:m[int(x.group(1),16)]=x.group(2)
 return m
def match(ex,token):
 return [(a,n) for a,n in ex.items() if token in n]
res={}
for year,root in versions.items():
 bp=root/'BEE.dll'; ap=root/'Required'/'Paint.aex'
 pe=pefile.PE(str(bp))
 ex=exports(bp)
 assert len(ex)>10000, ('incomplete exports',len(ex))
 pdata={x.struct.BeginAddress:x.struct.EndAddress for x in pe.DIRECTORY_ENTRY_EXCEPTION}
 imports={}
 for dll in pe.DIRECTORY_ENTRY_IMPORT:
  for imp in dll.imports:
   imports[imp.address-pe.OPTIONAL_HEADER.ImageBase]=(dll.dll.decode(errors='replace'),imp.name.decode(errors='replace') if imp.name else str(imp.ordinal))
 cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);cs.detail=True
 base=pe.OPTIONAL_HEADER.ImageBase
 avlayer=match(ex,'?RegisterStreams@BEE_AVLayer@@')
 assert len(avlayer)==1,avlayer
 start=avlayer[0][0]
 def disasm(start):
  end=pdata.get(start,start+0x100)
  assert 0<end-start<0x400000,(start,end)
  return list(cs.disasm(pe.get_data(start,end-start),base+start))
 calls=[]
 for ins in disasm(start):
  if ins.mnemonic in ('call','jmp') and len(ins.operands)>0 and ins.operands[0].type==capstone.x86.X86_OP_IMM:
   calls.append(ins.operands[0].imm-base)
 print(year,'AVLayer registrar',hex(start),'calls',list(map(hex,calls)))
 wanted=['BEE_PaintAtom','BEE_PaintStrokesGroup','BEE_PaintEffect','BEE_PaintProperties','BEE_PaintTransform']
 edges=[]
 for target in calls:
  hits=[]
  instructions=disasm(target)
  for idx,ins in enumerate(instructions):
   for op in ins.operands:
    ref=None
    if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP:ref=ins.address+ins.size+op.mem.disp-base
    if ref is None:continue
    name=ex.get(ref,'')
    if name.startswith('?Create@BEE_Paint') or name.startswith('?Create@BEE_Strokes'):
     registrations=[]
     group=[]
     for q in instructions[idx+1:idx+16]:
      if q.address-ins.address>110:break
      for o in q.operands:
       if o.type==capstone.x86.X86_OP_MEM and o.mem.base==capstone.x86.X86_REG_RIP:
        rva=q.address+q.size+o.mem.disp-base
        nam=ex.get(rva,'')
        if ('BEE_StreamGroupName_PAINT' in nam or 'BEE_StreamName_PAINT' in nam):group.append({'rva':hex(rva),'symbol':nam})
        if q.mnemonic=='call' and rva in imports:
         d,n=imports[rva]
         if d=='TDB.dll' and '?Register@TDB_ScRegisterStreams@@' in n:registrations.append({'rva':hex(q.address-base),'iat':hex(rva),'dll':d,'symbol':n})
     hits.append({'constructor_rva':hex(ref),'constructor_symbol':name,'lea_rva':hex(ins.address-base),'names':group,'register_calls':registrations})
  if hits: edges.append({'helper_rva':hex(target),'hits':hits})
 allhits=[h for e in edges for h in e['hits']]
 for w in wanted:
  a=[h for h in allhits if '?Create@'+w+'@@' in h['constructor_symbol'] and h['register_calls'] and h['names']]
  assert a, (year,w,'creator registration missing')
  print(' ',w,'helper',next(e['helper_rva'] for e in edges if a[0] in e['hits']),'create',a[0]['constructor_rva'],'name',a[0]['names'][0]['symbol'].split('@@')[0],'call',a[0]['register_calls'][0]['rva'])
 ape=pefile.PE(str(ap))
 dlls={x.dll.decode().lower() for x in ape.DIRECTORY_ENTRY_IMPORT}
 ae_exports=[x.name.decode() for x in ape.DIRECTORY_ENTRY_EXPORT.symbols if x.name]
 assert 'EffectMainExtra' in ae_exports and 'PluginDataEntryFunction' in ae_exports
 assert 'bee.dll' not in dlls and 'tdb.dll' not in dlls
 res[year]={'version':year,'BEE':{'path':str(bp),'sha256':hashlib.sha256(bp.read_bytes()).hexdigest(),'avlayer_register':hex(start),'helper_edges':edges},'PaintAEX':{'path':str(ap),'sha256':hashlib.sha256(ap.read_bytes()).hexdigest(),'size_bytes':ap.stat().st_size,'imports':sorted(dlls),'exports':ae_exports}}
out=Path(r'D:\Developer\ShapeLayerAE\labs\paint_native_properties_audit\paint_registration_verified_2025_2026.json')
out.write_text(json.dumps(res,indent=2,ensure_ascii=False),encoding='utf8')
print('PASS',len(res),'versions saved',out)
