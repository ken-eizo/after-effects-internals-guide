"""Regression test for AEIG purpose-based SDK/host classification."""
from sdk_taxonomy import checked_classify
from pathlib import Path
root=Path(__file__).resolve().parents[2]
examples={
 "ui-system/effect-controls-custom-ui/composite-widget-architecture.md":("Custom ECW UI","official"),
 "ui-system/gizmo-cross-platform-contracts.md":("Custom Comp UI","official"),
 "ui-system/drawbot-ui-drawing.md":("Drawbot suites","official"),
 "host-integration/cpp-sdk/aegps/dynamic-stream-suite.md":("aegps","official"),
 "state-model/native-property-system/index.md":("TDB/BEE Stream runtime","observed"),
 "gpu-system/overview.md":("PF.dll GF::Device and host GPU","observed"),
 "gpu-system/cross-platform-effect-architecture.md":("PF GPU render","official"),
 "host-integration/uxp-cep/uxp-after-effects-status.md":("UXP runtime detection","research"),
 "host-integration/cpp-sdk/effect-details/postload-module-lockdown.md":("PIN_LockDownModules","observed"),
}
for p,(owner,authority) in examples.items():
  c=checked_classify(p)
  assert c.owner==owner and c.authority==authority,(p,c)
for path in [
 "ui-system/new-unreviewed-widget.md",
 "gpu-system/unreviewed-widget-or-renderer.md",
 "host-integration/cpp-sdk/effect-details/new-private-foo.md",
 "host-integration/cpp-sdk/aegps/new-native-registration.md",
]:
  try:checked_classify(path)
  except ValueError:pass
  else:raise AssertionError("Ambiguous page silently admitted: "+path)
print("PASS",len(examples),"semantic owner examples and 4 missing-ownership negatives")
