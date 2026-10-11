"""Check ACTUAL compiled PiPL resource against C++ flags and PF_VERSION.
CompNodeAE VectorBridgeConsumer v1.0: avoids AE error 25::16 and version 80001.
"""
from pathlib import Path
import pefile,struct,re,json,hashlib
ROOT=Path(r"D:\Developer\ShapeLayerAE\labs\vector_bridge")
AEX=Path(r"D:\Developer\ShapeLayerAE\build\vector_bridge\Release\VectorBridgeConsumer.aex")
p=pefile.PE(str(AEX))
resources=[entry for entry in p.DIRECTORY_ENTRY_RESOURCE.entries if str(entry.name).upper()=="PIPL"]
assert len(resources)==1,"missing PiPL resource"
entries=resources[0].directory.entries
assert len(entries)==1
data_struct=entries[0].directory.entries[0].data.struct
blob=p.get_data(data_struct.OffsetToData,data_struct.Size)
num=struct.unpack_from("<I",blob,6)[0]
pos=10
props={}
for _ in range(num):
    vendor,key,ident,size=struct.unpack_from("<4s4sII",blob,pos)
    pos+=16
    content=blob[pos:pos+size]
    pos+=(size+3)&~3
    assert vendor==b"MIB8",(vendor,key)
    props[key.decode("ascii")]=content
assert pos==len(blob)
found={key:struct.unpack("<I",props[key])[0] for key in ("REVe","OLGe","2LGe")}
assert found=={"REVe":524289,"OLGe":0,"2LGe":134217728},found
cpp=(ROOT/"VectorBridgeConsumer.cpp").read_text(encoding="utf-8")
assert "PF_VERSION(1,0,0,PF_Stage_DEVELOP,1)" in cpp
assert "out_data->out_flags=PF_OutFlag_NONE;" in cpp
assert "out_data->out_flags2=PF_OutFlag2_SUPPORTS_THREADED_RENDERING;" in cpp
print("PASS: PiPL resource/flags align with C++ declarations, no 25::16 mismatch expected.")
print(json.dumps({"resource_bytes":len(blob),"number_properties":num,"piPL":found,
"consumer_sha256":hashlib.sha256(AEX.read_bytes()).hexdigest()},indent=2))
