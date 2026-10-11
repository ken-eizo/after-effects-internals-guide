import pefile,struct
p=pefile.PE(r"D:\Developer\ShapeLayerAE\build\vector_bridge\Release\VectorBridgeConsumer.aex")
for typ in p.DIRECTORY_ENTRY_RESOURCE.entries:
 if str(typ.name)!="PIPL":continue
 info=typ.directory.entries[0].directory.entries[0].data.struct
 b=p.get_data(info.OffsetToData,info.Size)
 print("total",len(b),"header",b[:10].hex(' '))
 pos=10
 for i in range(13):
  vendor,key,ident,size=struct.unpack_from("<4s4sII",b,pos)
  pos+=16
  value=b[pos:pos+size]
  pos+=(size+3)&~3
  print(i, vendor.decode(errors="replace"),key.decode(errors="replace"),ident,size,value.hex(" "),struct.unpack("<I",value)[0] if size==4 else "")
 print("finished",pos)
