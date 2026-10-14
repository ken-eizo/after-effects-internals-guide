---
status: supported-sdk-guide-companion
last_verified: 2026-10-14
evidence: E0-H + E2-L
versions: Adobe SDK25.6; Windows AE2025/2026 private comparison
---

# AEGP_RegisterSuite5 — Supported Plug-in Registration

`AEGP_RegisterSuite5` is the public interface for subscribing to commands and registering **documented host plugin capabilities** such as Artisans and AEIO modules. It is **not** a general `TDB_StreamBase` or `BEE_Layer` class provider API.

Official reference: [AEGP Suites — Registering with After Effects](https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/#registering-with-after-effects). Installed source `AE_GeneralPlug.h` around lines 2742–2832.

## Name and version

| Symbol | Value in SDK25.6 |
| --- | --- |
| C struct | `AEGP_RegisterSuite5` |
| Suite name | `kAEGPRegisterSuite` = `"AEGP Register Suite"` |
| Version constant | `kAEGPRegisterSuiteVersion5` = **6** (frozen in AE 10.0) |

Like other AEGP suites, the numeric version macro is not necessarily the same integer as the C suite suffix.

## Supported registration methods

| Entry | Responsibility |
| --- | --- |
| `AEGP_RegisterCommandHook` | Receive registered host menu commands |
| `AEGP_RegisterUpdateMenuHook` | Update available menu commands |
| `AEGP_RegisterDeathHook` | Receive host/plugin shutdown notification |
| `AEGP_RegisterVersionHook` | Plugin version callback |
| `AEGP_RegisterAboutStringHook` | Text for About UI |
| `AEGP_RegisterAboutHook` | About callback |
| `AEGP_RegisterArtisan` | Supported Artisan 3D renderer |
| `AEGP_RegisterIO` | Supported AEIO import/export module |
| `AEGP_RegisterIdleHook` | Idle callback |
| `AEGP_RegisterTracker` | Supported Tracker service |
| `AEGP_RegisterInteractiveArtisan` | Interactive Artisan renderer |
| `AEGP_RegisterPresetLocalizationString` | Preset/property name localization mapping |

This is the complete **12-method** SDK25.6 `RegisterSuite5` surface that was inspected. None takes a native `TDB_MatchName` plus a C++ Stream Creator callback or provides a custom indexed/named group canonical UILayout.

## Registration is not creating a property class

```text
Supported external AEGP:
  entry function / plugin ID
  └─ AEGP_RegisterSuite5
       ├─ command/update/death/idle hook
       ├─ Artisan / Tracker / IO capability
       └─ localization

Internal Adobe native boot:
  aelib.dll -> OM_Birth / FLT_Birth / BEE_Birth
  └─ TDB_StreamFactory::RegisterFactoryFunc
       └─ arbitrary native C++ class Creator for Adobe first-party types
```

The second path is a private Adobe implementation observed in AE2025/2026 binaries (F-VECTOR-093–096). Do not assume a third-party AEX's ordinary entrypoint will execute under equivalent host initialization or be allowed to publish custom factory classes.

## Command Hook notes

A registration hook and a menu item are distinct steps. Successfully registering a command number does not itself mean the item is visible in a selected menu; add/update operations are separate supported surfaces. Callback threading, lifetime, and command ownership follow their individual SDK contracts.

A shutdown Death Hook is a valid way to clean up resources **owned by an AEGP**, but is not proof that all native Adobe project Stream instances referencing unsupported foreign private methods have already been destroyed.

## Native property research status

Scoped inspection of the installed **70** SDK25.6 public header files found no supported general native Stream class registration, foreign parent UILayout provider or independent BEE Layer factory declaration. This negative result is limited to that inspected public SDK, not a theorem about future Adobe offerings or unavailable partner APIs.

See [Native Factory Registration](../../../state-model/native-property-system/factory-registration-lifetime.md), [API Atlas](../../../state-model/native-property-system/api-atlas.md) and [Adobe Guide AEGP Suites](https://ae-plugins.docsforadobe.dev/aegps/aegp-suites/). Sources: official SDK25.6 (E0-H), F-VECTOR-072/088 and native F-VECTOR-093–096 (E2-L).
