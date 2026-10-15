"""AEIG navigation taxonomy: choose the FUNCTION/host contract, never a shared drawing API.
This is a documentation classification, not a claim of Adobe endorsement.
"""
from dataclasses import dataclass
from pathlib import PurePosixPath

@dataclass(frozen=True)
class Classification:
    section: str
    topic: str
    authority: str
    owner: str

# "Official" means a public Adobe SDK feature/API family; "observed" is
# native/first-party implementation, and "research" is an AEIG analytical term.
EFFECT_UI="Effect UI & Events"
INTERNAL="Observed Native Implementation (AEIG Research)"
RENDER="Observed Render, Cache & Execution (AEIG Research)"
PROJECT="Observed Project, Media & Persistence (AEIG Research)"
RESEARCH="Research & Evidence"
REFERENCE="Reference"
def C(section,topic,authority,owner):
    return Classification(section,topic,authority,owner)

# The same PF_Cmd_EVENT and Drawbot suite may serve BOTH Custom ECW UI
# and Custom Comp UI. They must never be automatically grouped by Drawbot.
SPECIAL={
 "ui-system/effect-controls-custom-ui/index.md":C(EFFECT_UI,"Custom ECW UI — PF_Window_EFFECT","official","Custom ECW UI"),
 "ui-system/effect-controls-custom-ui/cross-platform-compatibility.md":C(EFFECT_UI,"Custom ECW UI — PF_Window_EFFECT","official","Custom ECW UI"),
 "ui-system/effect-controls-custom-ui/composite-widget-architecture.md":C(EFFECT_UI,"Custom ECW UI — PF_Window_EFFECT","official","Custom ECW UI"),
 "ui-system/effect-controls-custom-ui/performance-and-resilience.md":C(EFFECT_UI,"Custom ECW UI — PF_Window_EFFECT","official","Custom ECW UI"),
 "ui-system/drawbot-ui-drawing.md":C(EFFECT_UI,"Drawbot Suites — Shared Drawing API","official","Drawbot suites"),
 "ui-system/async-custom-ui-rendering.md":C(EFFECT_UI,"PF_AsyncManagerP — Custom UI Rendering","official","PF_AsyncManagerP"),
 "ui-system/effect-custom-ui-input-routing.md":C(EFFECT_UI,"PF_Cmd_EVENT — UI Event Dispatch","official","PF_Cmd_EVENT"),
 "ui-system/effect-custom-ui-invalidation.md":C(EFFECT_UI,"PF_Cmd_EVENT — UI Event Dispatch","official","PF_InvalidateRect"),
 "ui-system/interactive-ui-latency.md":C(EFFECT_UI,"PF_Cmd_EVENT — UI Event Dispatch","research","UI input-to-display measurement"),
 "ui-system/overview.md":C(INTERNAL,"Editor / View State vs Render State","research","AEIG UI state model"),
 "ui-system/spectrum-and-ae-ui.md":C(INTERNAL,"Editor / View State vs Render State","research","SPECTRUM first-party UI"),
 "ui-system/view-state-and-render-boundary.md":C(INTERNAL,"Editor / View State vs Render State","research","AEIG view/render boundary"),
 "host-integration/cpp-sdk/effect-details/postload-effect-module-descriptors.md":C(INTERNAL,"FLT_FCSpec / PIN_LockDownModules (Private)","observed","FLT_NotifyFilterLoadingDone"),
 "host-integration/cpp-sdk/effect-details/postload-module-lockdown.md":C(INTERNAL,"FLT_FCSpec / PIN_LockDownModules (Private)","observed","PIN_LockDownModules"),
 "host-integration/aegp/general-plugin-setdown-lifetime.md":C(INTERNAL,"Native Plug-in Module Lifecycle (Private)","observed","PLUG / MEE lifecycle"),
 "host-integration/uxp-cep/uxp-after-effects-status.md":C("Extension Host Interfaces (Distinct APIs)","UXP Runtime Presence — AE Host API Unverified","research","UXP runtime detection"),
 "host-integration/uxp-cep/cep-runtime.md":C("Extension Host Interfaces (Distinct APIs)","CEP Panels / ExtendScript Bridge","official","CEP / CSXS"),
 "host-integration/uxp-cep/index.md":C("Extension Host Interfaces (Distinct APIs)","CEP Panels / ExtendScript Bridge","research","CEP vs UXP boundary"),
 "host-integration/cep/cc2015-panel-sdk.md":C("Extension Host Interfaces (Distinct APIs)","CEP Panels / ExtendScript Bridge","research","CEP panel SDK lineage"),
 "gpu-system/overview.md":C(RENDER,"GF / PF GPU Runtime (Observed Native)","observed","PF.dll GF::Device and host GPU"),
 "gpu-system/vulkan-host-backend-feasibility.md":C("SmartFX","PF GPU Rendering — Unverified Non-SDK Backends","research","Vulkan interop feasibility"),
 "gpu-system/cross-api-interop-verified-boundaries.md":C("SmartFX","PF GPU Rendering — Unverified Non-SDK Backends","research","D3D12/Vulkan/Metal interop"),
 "gpu-system/one-millisecond-total-frame.md":C("SmartFX","PF_Cmd_SMART_RENDER_GPU — Performance Qualification","research","AE Composition Profiler goal"),
 "gpu-system/cross-platform-effect-architecture.md":C("SmartFX","PF_Cmd_SMART_RENDER_GPU — Implementation","official","PF GPU render"),
 "gpu-system/effect-plugin-author-field-guide-ja.md":C("SmartFX","PF_Cmd_SMART_RENDER_GPU — Implementation","research","PF Effect plug-in engineering"),
 "gpu-system/optimal-effect-engineering.md":C("SmartFX","PF_Cmd_SMART_RENDER_GPU — Implementation","research","PF Effect optimization"),
 "gpu-system/release-qualification-matrix.md":C("SmartFX","PF_Cmd_SMART_RENDER_GPU — Performance Qualification","research","Effect qualification"),
 "cache-system/compute-cache.md":C("Effect Details","Compute Cache API","official","Compute Cache API"),
 "capability-recipes/cep-vs-uxp-extension-plane.md":C("Extension Host Interfaces (Distinct APIs)","CEP vs UXP — Capability Boundary","research","CEP vs UXP"),
 "capability-recipes/ui-automation-extension-plane.md":C("Extension Host Interfaces (Distinct APIs)","CEP vs UXP — Capability Boundary","research","extension and scripting"),
 "capability-recipes/effect-prefix-rendering.md":C("Effect Details","AEGP Render Options / Layer Checkout","research","AEGP_RenderOptionsSuite"),
 "host-integration/cpp-sdk/aegp-internal-coordinate-bridges.md":C(INTERNAL,"AEGP-to-BEE/TDB Adapter Boundaries","observed","AEGP/BEE bridge"),
 "host-integration/cpp-sdk/state-api-evolution.md":C("AEGPs","AEGP State APIs (Public)","official","AEGP State APIs"),
 "host-integration/cpp-sdk/performance-and-escape-hatches.md":C("Effect Details","Effect SDK Performance Contracts","research","PF Effect"),
 "host-integration/cpp-sdk/verified-render-contracts.md":C("Effect Details","Effect SDK Performance Contracts","research","PF render"),
 "host-integration/cpp-sdk/guide-gap-matrix.md":C("Introduction","SDK Guide / Headers Coverage","research","SDK comparison"),
 "host-integration/cpp-sdk/host-reimplementation-failure-patterns.md":C(RESEARCH,"Independent SDK Reimplementations","research","third-party ABI"),
 "host-integration/cpp-sdk/independent-abi-reimplementations.md":C(RESEARCH,"Independent SDK Reimplementations","research","third-party ABI"),
 "host-integration/cpp-sdk/platform-header-parity.md":C("Introduction","SDK Platform ABI / Headers","official","SDK headers"),
 "host-integration/cpp-sdk/sample-pitfalls.md":C("Introduction","SDK Samples / Errata","research","SDK samples"),
 "host-integration/cpp-sdk/verified-sample-repairs.md":C("Introduction","SDK Samples / Errata","research","SDK samples"),
 "host-integration/cpp-sdk/sdk-distribution-archaeology.md":C(RESEARCH,"SDK Distribution / Version Lineage","research","historical SDK"),
 "host-integration/cpp-sdk/suite-versioning-and-abi.md":C("Introduction","SDK Platform ABI / Headers","official","PICA suite versions"),
}
GIZMO_TOPIC="Custom Comp UI — PF_Window_COMP / PF_Window_LAYER"
def classify(relative_path):
    p=PurePosixPath(relative_path)
    n=p.as_posix()
    if n in SPECIAL:return SPECIAL[n]
    parts=p.parts
    area=parts[0]
    if area=="ui-system" and p.name.startswith("gizmo-"):
        return C(EFFECT_UI,GIZMO_TOPIC,"official","Custom Comp UI")
    if area=="state-model" and len(parts)>1 and parts[1]=="native-property-system":
        return C(INTERNAL,"TDB_StreamBase / TDB_StreamFactory / BEE (Private)","observed","TDB/BEE Stream runtime")
    if area=="host-integration":
        if len(parts)>2 and parts[1]=="cpp-sdk":
            group=parts[2]
            official={
                "introduction":"Introduction","effect-basics":"Effect Basics",
                "effect-details":"Effect Details","smartfx":"SmartFX",
                "effect-ui-events":EFFECT_UI,"audio":"Audio",
                "aegps":"AEGPs","artisans":"Artisans","aeios":"AEIOs",
                "premiere-other-hosts":"Premiere Pro & Other Hosts",
            }
            if group in ("effect-details", "effect-ui-events", "aegps"):
                audited_public_files={
                    "effect-details": {"index.md"},
                    "effect-ui-events": {"index.md"},
                    "aegps": {"index.md", "dynamic-stream-suite.md", "keyframe-suite.md", "register-suite.md", "stream-suite.md"},
                }
                if p.name not in audited_public_files[group]:
                    raise ValueError("Ambiguous new public SDK page needs named host/API ownership: "+n)
            if group in official:
                top=official[group]
                sdk_topic={
                    "introduction":"Introduction — Official SDK",
                    "effect-basics":"Effect Basics — PF_Cmd_* / PF_ParamDef",
                    "effect-details":"Effect Details — Official SDK Suites",
                    "smartfx":"SmartFX — PF_Cmd_SMART_RENDER",
                    "effect-ui-events":"Effect UI & Events — Official SDK",
                    "audio":"Audio — Official SDK",
                    "aegps":"AEGP Suites — Public AEGP API",
                    "artisans":"Artisans — Public Renderer Plug-in API",
                    "aeios":"AEIOs — Public Importer API",
                    "premiere-other-hosts":"Premiere Pro & Other Hosts — SDK",
                }
                return C(top,sdk_topic[group],"official",group)
            return C("Introduction","SDK Overview / Suites","official","Adobe PF/AEGP SDK")
        sub=parts[1]
        mapping={
            "aegp":C("AEGPs","AEGP Host Services / Suite Lifetime","official","AEGP"),
            "aeio":C("AEIOs","AEIO Plug-in Contract","official","AEIO"),
            "artisans":C("Artisans","Artisan Rendering Interface","official","Artisan"),
            "smartfx":C("SmartFX","PF_Cmd_SMART_PRE_RENDER / SMART_RENDER","official","SmartFX"),
            "expressions":C("Expressions (AE Host API)","Expression Engine / API Boundary","research","Expression API"),
            "command-line":C("Command Line (aerender)","Command-Line Host Interface","research","aerender"),
            "scripting":C("Scripting (ExtendScript DOM)","After Effects Scripting Object Model","official","ExtendScript"),
            "pica-sweetpea":C(INTERNAL,"PICA / SweetPea (Private Runtime)","observed","PICA / SweetPea"),
            "premiere-pro":C("Premiere Pro & Other Hosts","Premiere Pro SDK / Cross-host Comparison","research","Premiere Pro"),
        }
        if sub in mapping:return mapping[sub]
        return C(INTERNAL,"AE / MediaCore Host Boundaries","research","host integration")
    if area=="vector-shape-system":
        return C(INTERNAL,"BEE / TDB Vector and Shape Streams (Private)","observed","BEE Vector")
    if area=="evaluation":
        return C(INTERNAL,"BEE Evaluation / Work Queues (Private)","observed","BEE")
    if area=="state-model":
        return C(INTERNAL,"BEE / TDB State & Object Identity (Private)","research","state identity")
    if area=="architecture":
        return C(INTERNAL,"Native Host Modules / Lifecycle","observed","AE host architecture")
    if area=="animation-system":
        return C(INTERNAL,"Keyframe / Interpolation Runtime (Observed)","research","animation runtime")
    if area=="text-system":
        return C(INTERNAL,"BEE Text / Font Runtime (Observed)","observed","BEE text")
    if area=="three-d-system":
        return C(INTERNAL,"3D Layer / Renderer Runtime (Observed)","research","AE 3D runtime")
    if area=="ai-analysis":
        return C(INTERNAL,"Roto Brush / Object Matte Runtime (Observed)","research","AE ML analysis")
    if area=="tracking-analysis":
        return C(INTERNAL,"Tracker / Analysis Runtime (Observed)","research","AE tracking")
    if area=="expression-engine":
        return C(INTERNAL,"Expression Runtime / Caches (Observed)","research","AE expressions")
    if area=="render-graph":
        return C(RENDER,"BEE / Render Graph / Frame Checkout (Private)","observed","BEE render")
    if area=="cache-system":
        return C(RENDER,"AE Cache / Identity / Invalidation (Observed)","research","AE cache")
    if area=="mfr":
        return C("Effect Details","Multi-Frame Rendering (MFR)","official","MFR")
    if area=="gpu-system":
        raise ValueError("New GPU documentation must specify PF SmartFX vs private GF vs cross-API feasibility: "+n)
    if area=="image-pipeline":
        return C(RENDER,"PF_EffectWorld / Pixel & ROI Semantics","research","image processing")
    if area=="color-pipeline":
        return C(RENDER,"Color Conversion / Pixel Color Semantics","research","color pipeline")
    if area=="temporal-system":
        return C(RENDER,"Time Sampling / Motion Blur / Frame Cache","research","temporal")
    if area=="threading-system":
        return C(RENDER,"PF_Cmd_* / MFR Concurrency Contracts","research","PF threading")
    if area=="memory-system":
        return C(RENDER,"PF / AEGP Memory & Residency","research","PF memory")
    if area=="audio-system":
        return C("Audio","PF Audio Rendering / Audio Runtime","research","PF audio")
    if area=="persistence":
        return C(PROJECT,"AEP / AEPX / FFX and Sequence Data","research","project persistence")
    if area=="media-system":
        return C(PROJECT,"Footage / MediaCore / Frame Identity","research","AE media")
    if area=="product-shell":
        return C(PROJECT,"Workspace / Item View / Panel State","research","AE workspace")
    if area=="headless-system":
        return C("Command Line (aerender)","Command-Line Host Interface","research","aerender")
    if area=="interop":
        return C(PROJECT,"AEIO / Interchange Formats (Research)","research","format interop")
    if area=="capability-recipes":
        return C("Introduction","AEIG Cross-API Recipes (Not SDK APIs)","research","recipe")
    if area=="foundations":
        return C("Introduction","AEIG Methodology & Evidence (Not SDK APIs)","research","methodology")
    if area=="archaeology":
        return C(RESEARCH,"Adobe Version / Implementation History","research","historical observation")
    if area=="research-notes":
        return C(RESEARCH,"Host Experiments / Case Reports","research","research receipts")
    if area=="observability":
        return C(RESEARCH,"AE Trace / Debug Databases (Observed)","observed","AE diagnostic")
    if area=="troubleshooting":
        return C(RESEARCH,"Reproduction / Failure Analysis","research","failure")
    if area=="reference":
        topic=("Release Qualification & Provenance" if any(k in p.stem for k in
            ("release","rc-","finalizer","selftest","readiness","operator","l5-","promotion","prediction"))
               else "Research Registry / SDK Inventory")
        return C(REFERENCE,topic,"research","AEIG registry")
    if n=="index.md":
        return C("Introduction","AEIG Home","research","AEIG")
    raise ValueError("No explicit API owner classification for: "+n)

def checked_classify(relative_path):
    c=classify(relative_path)
    assert isinstance(c,Classification), f"Non-dataclass result: {relative_path} {c}"
    assert c.authority in ("official","observed","research"), relative_path
    return c

# Intentionally use canonical public names as authoritative documentation anchors.
OFFICIAL_GUIDE={
 "Custom ECW UI":"https://ae-plugins.docsforadobe.dev/effect-ui-events/effect-ui-events/",
 "Custom Comp UI":"https://ae-plugins.docsforadobe.dev/effect-ui-events/effect-ui-events/",
 "Drawbot suites":"https://ae-plugins.docsforadobe.dev/effect-ui-events/custom-ui-and-drawbot/",
 "PF_Cmd_EVENT":"https://ae-plugins.docsforadobe.dev/effect-ui-events/effect-ui-events/",
 "AEGP":"https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/",
 "SmartFX":"https://ae-plugins.docsforadobe.dev/smartfx/smartfx/",
 "MFR":"https://ae-plugins.docsforadobe.dev/effect-details/multi-frame-rendering-in-ae/",
 "AEIO":"https://ae-plugins.docsforadobe.dev/aeios/aeios/",
 "Artisan":"https://ae-plugins.docsforadobe.dev/artisans/artisans/",
 "PF GPU render":"https://ae-plugins.docsforadobe.dev/intro/gpu-build-instructions/",
}
