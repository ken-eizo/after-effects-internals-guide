---
status: active
last_verified: 2026-09-16
evidence: Adobe Spectrum public docs + Adobe AE developer docs + AEIG runtime archaeology
---
# Adobe Spectrum Design System vs After Effects Editor UI

## Core finding
After Effects UI should be modeled as two related but non-identical layers: Adobe's cross-product design language and AE-specific product-shell/editor controls. Spectrum is a strong source for shared design primitives, but it is not a complete specification of the Timeline, Effect Controls, viewer chrome, property rows, docking shell, or other AE-specialized surfaces.

Adobe describes Spectrum as its design system and publishes design resources plus implementation libraries. Adobe developer material also points to a Spectrum Figma plugin. This makes Spectrum the best public starting point for a Figma-side AE design kit, while AE-specific components still need independent reconstruction and validation.

## Design-to-implementation bridge
A useful architecture is:

`Spectrum design resources -> AEIG semantic tokens -> AE component specifications -> Figma components -> implementation adapters`

The implementation adapter must remain host-specific. A Figma component or Spectrum component name is not evidence that After Effects exposes that component to third-party extensions.

## Public implementation families
Spectrum has public implementation families including Spectrum CSS, React Spectrum, and Spectrum Web Components. These can inform dimensions, states, semantics, accessibility, and interaction patterns. Their availability on the web does not imply that they can be loaded unchanged inside every AE extension runtime.

CEP panels are HTML/JS surfaces and can reproduce Spectrum-derived styling, subject to the bundled CEF/runtime constraints of the target AE version. UXP can provide tighter Spectrum integration in hosts where a public UXP contract exists, but AEIG must continue to distinguish runtime presence from supported third-party AE capability.

## Figma conclusion
Use the official Spectrum Figma resources as the upstream shared-component vocabulary. Build an AEIG-owned AE layer on top rather than treating a generic Spectrum kit as an After Effects kit. The AE layer should contain measured, versioned components and tokens and should record whether each value is inherited from Spectrum, observed in AE, or approximated.
## AE-specific component taxonomy
AEIG should reconstruct at least these families: application/workspace shell; panel header and tabs; toolbars; menus and context menus; tree/list rows; property rows; numeric and text editors; sliders and scrubbers; disclosure controls; timeline layers and switches; keyframes and interpolation affordances; graph-editor controls; Effect Controls rows; viewer chrome and overlays; dialogs; notifications; drag/drop and docking indicators.

For each component record: geometry, density, typography, iconography, colors, state transitions, hit targets, keyboard behavior, focus behavior, drag semantics, theme behavior, scaling/DPI behavior, and version scope.

## Token model
Do not begin with hard-coded CSS variables. Preserve provenance:

- `spectrum.*`: values or semantics traceable to public Spectrum resources;
- `ae.observed.*`: values measured directly from a named AE release/theme/DPI configuration;
- `ae.semantic.*`: stable AEIG concepts mapped onto observed or Spectrum tokens;
- `ae.component.*`: component-local decisions;
- `prototype.*`: unverified approximations used only during design exploration.

This prevents a visual approximation from silently becoming an alleged native AE constant.

## Runtime boundary
ScriptUI, CEP, native plug-in custom UI, and UXP substrate are different execution and rendering planes. A component specification should therefore be renderer-neutral. For example, `AE.NumericField` describes behavior and appearance; separate adapters can target HTML/CSS, ScriptUI where feasible, or native/custom drawing.

This is especially important for high-frequency interactions such as scrubbing, timeline manipulation, drag previews and popovers. Fidelity is not only color and spacing: latency, pointer capture, focus, undo grouping, keyboard routing and host redraw behavior are part of the component contract.

## Research method
1. Capture a controlled matrix of AE versions, themes, UI scaling and DPI.
2. Measure repeated primitives before specialized components.
3. Compare measurements against Spectrum semantics and tokens.
4. Separate inherited/shared behavior from AE-only behavior.
5. Record interaction traces for hover, press, focus, drag, edit and disabled states.
6. Reconstruct components in Figma with variants and variables.
7. Implement renderer adapters and compare screenshots/interaction behavior.
8. Keep discrepancies as explicit findings rather than tuning them away without provenance.
## Current evidence boundary
Public Adobe material establishes Spectrum as Adobe's design system, provides UI/design resources, and identifies a Spectrum Figma plugin. Adobe's After Effects developer portal establishes supported extension routes including scripts, panels, and plug-ins, but these facts do not expose the private implementation of AE's own product UI.

AEIG already establishes a continuing CEP route and detects UXP-related runtime substrate in modern AE installations. Keep the existing rule from `capability-recipes/cep-vs-uxp-extension-plane.md`: physical runtime substrate is weaker evidence than an AE-specific public third-party host contract.

The September 2026 AE 26.5 user documentation is especially useful as a moving UI target: Adobe documents an Effect Controls panel modernization on a modern framework with icon-oriented controls. Treat this as evidence that AE's UI implementation is actively evolving, so component observations must always carry a version.

## Deliverable definition: AEIG UI Kit
The target artifact is not merely a Figma mockup. `AEIG UI Kit` is a versioned specification with five synchronized layers:

1. evidence/provenance;
2. semantic design tokens;
3. component contracts and variants;
4. Figma representation;
5. runtime adapters/prototypes.

A component is considered reconstructed only when its visual states and important interaction semantics are documented and its evidence/version scope is explicit.

## Related AEIG material
- `docs/capability-recipes/cep-vs-uxp-extension-plane.md`
- `docs/host-integration/uxp-cep/cep-runtime.md`
- `docs/host-integration/uxp-cep/uxp-after-effects-status.md`
- `docs/architecture/product-system-atlas.md`
- `datasets/ae-2025-extension-substrates.csv`
- `datasets/ae-2025-extension-loader-strings.csv`

## Public references
- Adobe Spectrum: https://spectrum.adobe.com/
- Spectrum design tokens: https://spectrum.adobe.com/page/design-tokens/
- Spectrum UI kits: https://spectrum.adobe.com/page/ui-kits/
- Adobe After Effects Developer: https://developer.adobe.com/after-effects/
- Adobe Spectrum implementation guidance mentioning the Figma plugin: https://developer.adobe.com/express/add-ons/docs/guides/build/design/implementation-guide
