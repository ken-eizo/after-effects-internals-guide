var CACHE = "D:/Developer/After Effects Internals Guide/experiments/observatory/runs/EXP-CACHE-002/";
var RG = "D:/Developer/After Effects Internals Guide/experiments/observatory/runs/EXP-RG-001/";
var SCRIPT = "D:/Developer/After Effects Internals Guide/experiments/observatory/runs/EXP-SCRIPT-001/";
var LOGPATH = CACHE + "fixture-script.log";
var RECEIPT = CACHE + "receipt-matrix.tsv";
var PASSFILE = RG + "current-pass.txt";
var HOSTTRACE = RG + "host-trace.log";
var TRACECONTROL = RG + "trace-control.tsv";
var ARTSTAGE = RG + "artisan-stage.tsv";
var REFLECT = SCRIPT + "runtime-reflection.tsv";
var ENV = CACHE + "environment.txt";
var SESSION = "D:/Developer/After Effects Internals Guide/datasets/aeig-l5-operator-session.env";
function log(s){ var f=new File(LOGPATH); f.open("a"); f.writeln((new Date()).getTime()+"\t"+s); f.close(); }
function writeText(path,s){ var f=new File(path); f.open("w"); f.write(s); f.close(); }
function readKV(path){
  var f=new File(path); if(!f.exists) return null;
  if(!f.open("r")) return null; var txt=f.read(); f.close();
  var o={}, lines=txt.split(/\r?\n/), i, q, k;
  for(i=0;i<lines.length;i++){ q=lines[i].indexOf("="); if(q>0){ k=lines[i].substring(0,q); o[k]=lines[i].substring(q+1); } }
  return o;
}
function clean(s){ return String(s).replace(/[\t\r\n]+/g," "); }
function emitReflect(label,kind,info){
  var f=new File(REFLECT); f.open("a");
  var name="", type="", data="", ro="";
  try{name=info.name;}catch(e){}
  try{type=info.type;}catch(e){}
  try{data=info.dataType;}catch(e){}
  try{ro=info.isReadOnly;}catch(e){}
  f.writeln([clean(label),clean(kind),clean(name),clean(type),clean(data),clean(ro)].join("\t")); f.close();
}
function dumpReflect(obj,label){
  try{
    var r=obj.reflect, i;
    for(i=0;i<r.properties.length;i++) emitReflect(label,"property",r.properties[i]);
    for(i=0;i<r.methods.length;i++) emitReflect(label,"method",r.methods[i]);
  }catch(e){ log("REFLECT_ERR="+label+" "+e); }
}
function renderPass(comp,label,path){
  writeText(PASSFILE,label);
  log("PASS_BEGIN="+label);
  var rq=app.project.renderQueue.items.add(comp);
  if(label=="A"){
    dumpReflect(app.project.renderQueue,"RenderQueue");
    dumpReflect(rq,"RenderQueueItem");
    try{dumpReflect(rq.outputModule(1),"OutputModule");}catch(e){}
  }
  rq.timeSpanStart=0; rq.timeSpanDuration=comp.frameDuration;
  var om=rq.outputModule(1); om.applyTemplate("Lossless"); om.file=new File(path);
  app.project.renderQueue.render();
  log("PASS_END="+label+" status="+rq.status);
  try{rq.remove();}catch(e){log("RQ_REMOVE_ERR="+e);}
}
var session=readKV(SESSION);
if(!session || session.schema!="AEIG-L5-SESSION-v1" || !session.session_id || !session.issued_unix_ms || !session.static_rc_fingerprint || !session.canonical_aex_sha256){
  alert("AEIG operator session metadata is missing or invalid. Run AEIG-L5-PREPARE.cmd first.");
  throw new Error("AEIG operator session metadata missing/invalid");
}
var comp=null;
var env=[];
env.push("aeig.session_id="+session.session_id);
env.push("aeig.issued_unix_ms="+session.issued_unix_ms);
env.push("aeig.static_rc_fingerprint="+session.static_rc_fingerprint);
env.push("aeig.canonical_aex_sha256="+session.canonical_aex_sha256);
try{env.push("app.version="+app.version);}catch(e){}
try{env.push("app.buildNumber="+app.buildNumber);}catch(e){}
try{env.push("app.buildName="+app.buildName);}catch(e){}
try{env.push("os="+$.os);}catch(e){}
try{env.push("locale="+app.isoLanguage);}catch(e){}
try{env.push("gpuAccelType="+app.project.gpuAccelType);}catch(e){}
writeText(ENV,env.join("\n")+"\n");
writeText(REFLECT,"label\tkind\tname\ttype\tdataType\tisReadOnly\n");
log("SESSION_ID="+session.session_id+" RC="+session.static_rc_fingerprint+" ISSUED="+session.issued_unix_ms);
log("SCRIPT_ENTER AE="+app.version+" items_before="+app.project.numItems);
dumpReflect(app,"Application");
dumpReflect(app.project,"Project");
try {
  comp=app.project.items.addComp("AEIG_L5_FIXTURE",64,64,1,1,24);
  dumpReflect(comp,"CompItem");
  log("renderers="+comp.renderers.join(" | "));
  comp.renderer="AEIG Receipt Probe"; log("renderer="+comp.renderer);
  var layer=comp.layers.addSolid([0.2,0.4,0.6],"AEIG_SOLID",32,32,1,1);
  layer.threeDLayer=true; log("threeDLayer="+layer.threeDLayer);
  dumpReflect(layer,"AVLayer");
  var fx=layer.property("ADBE Effect Parade"); dumpReflect(fx,"EffectParade");
  var e1=fx.addProperty("ADBE Gaussian Blur 2"); e1.property(1).setValue(10); dumpReflect(e1,"GaussianBlur"); log("fx1="+e1.matchName+" blur="+e1.property(1).value);
  var e2=fx.addProperty("ADBE Fill"); dumpReflect(e2,"Fill"); log("fx2="+e2.matchName);
  var e3=fx.addProperty("ADBE Tint"); dumpReflect(e3,"Tint"); log("fx3="+e3.matchName);
  log("numEffects="+fx.numProperties);
  layer=comp.layer("AEIG_SOLID"); fx=layer.property("ADBE Effect Parade"); e1=fx.property(1);
  e1.property(1).setValue(9); log("WARMUP blur="+e1.property(1).value);
  renderPass(comp,"WARMUP",CACHE+"fixture-output-WARMUP.avi");
  try{ (new File(CACHE+"fixture-output-WARMUP.avi")).remove(); }catch(e){}
  layer=comp.layer("AEIG_SOLID"); fx=layer.property("ADBE Effect Parade"); e1=fx.property(1);
  e1.property(1).setValue(10); log("POST_WARMUP blur="+e1.property(1).value);
  writeText(RECEIPT,""); writeText(HOSTTRACE,""); writeText(TRACECONTROL,""); writeText(ARTSTAGE,"");
  log("CANONICAL_CAPTURE_RESET_AFTER_WARMUP");
  comp.renderer="ADBE Advanced 3d"; comp.renderer="AEIG Receipt Probe"; log("REBIND_A renderer="+comp.renderer);
  renderPass(comp,"A",CACHE+"fixture-output-A.avi");
  layer=comp.layer("AEIG_SOLID"); fx=layer.property("ADBE Effect Parade"); e1=fx.property(1);
  e1.property(1).setValue(75);
  log("MUTATION blur="+e1.property(1).value);
  comp.renderer="ADBE Advanced 3d"; comp.renderer="AEIG Receipt Probe"; log("REBIND_B renderer="+comp.renderer);
  renderPass(comp,"B",CACHE+"fixture-output-B.avi");
} catch(e) {
  log("ERR="+e.toString()+" line="+e.line);
}
try { if(comp) comp.remove(); } catch(e2) { log("COMP_REMOVE_ERR="+e2); }
writeText(PASSFILE,"DONE");
log("receipt_exists="+(new File(RECEIPT)).exists);
log("reflection_exists="+(new File(REFLECT)).exists);
log("items_after="+app.project.numItems);
log("SCRIPT_EXIT");
