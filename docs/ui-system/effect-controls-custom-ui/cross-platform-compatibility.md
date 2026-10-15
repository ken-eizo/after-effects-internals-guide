---
status: research-backed-contract; Windows runtime evidence partial; macOS host qualification pending
last_verified: 2026-10-16
evidence:
  - E0-G: Adobe Effect UI & Events, Custom UI & Drawbot, Apple Silicon Support, Windows on Arm Support
  - E0-G: Adobe Parameter Supervision, Arbitrary Data Parameters, Tips & Tricks
  - E0-H: AEIG SDK 25.6 normalized Windows/macOS header parity (68/68)
  - E2-X: Windows GizmoSearchAE portable tests (shared pure model only; not an ECW or macOS host acceptance test)
  - H: OS-specific fast-path equivalence and performance until controlled host tests
---

# Custom ECW UI — Windows/macOS Host Compatibility

## 対象と主張の強さ

対象はEffect Controls Window (ECW)内の **Effect Custom UI** である。Composition/Layer overlay、AEGP独立パネル、CEP/UXP、レンダー画像へのGPU描画を混ぜない。MacではIntel x86_64とApple Silicon arm64を別環境として認定し、Windows x64も独立認定する。Windows ARM64はAdobeの該当ホスト/版で利用可能な場合の追加ターゲットであり、Windows x64バイナリがそのままnative ARM64となるわけではない。

**E0-G contract:** `PF_OutFlag_CUSTOM_UI`、`PF_REGISTER_UI`、`PF_Cmd_EVENT`、`PF_PUI_CONTROL`を使ったECW領域へのイベント・Drawbot描画がサポートされる。`PF_PUI_TOPIC`（折り畳んでも見える領域）と`PF_PUI_CONTROL`（折り畳むと隠れる領域）は別。描画は`PF_Event_DRAW`内のみ。

**非主張:** Macで同じバイナリがロード済み、同じ入力が届く、同じフォントピクセルになる、同じp99になる、240Hz必達、OSのGPUコマンドでDrawbotを自由に置き換えられる、のいずれも未証明。

## Compatibility ladder — 「対応」の6段階

| Gate | 証明する内容 | Windows x64 | macOS Intel/ARM | 拒否条件 |
| --- | --- | --- | --- | --- |
| P0 Source | SDKヘッダー/portable modelがコンパイル | SDK parityとWindows portable testsの既存証拠 | 68/68ヘッダー比較のみ。native compile待ち | OS専用APIが共通層へ漏れる |
| P1 Loader | PiPLとentry symbol、ホストにロード | Windows既存Gizmoのログあり | Universal `.plugin`・AE host load待ち | 署名、PiPL、ABI、loader失敗 |
| P2 ECW Event | CREATE/ACTIVATE/CLICK/DRAG/DRAW/CLOSEのライフサイクル | 一部実機計測あり | 実機未認定 | 不正event、閉鎖後コールバック処理 |
| P3 Visual | DPI、Retina、text、AA、theme、image format、座標、damage | 検証された環境範囲のみ | 実機未認定 | ピクセル差/残像/ヒット位置の不一致 |
| P4 Semantic | 変更、Undo、keyframe、save/reload、複数instance、MFR | 実装ごとに独立試験 | 実機未認定 | 破損、取り違え、再入不正 |
| P5 Performance | 負荷別A/B/A、p99、long-tail、memory、input-to-display | 部分証拠。ホスト全体の保証なし | 実測待ち | 改善退化・ハング・資源逸脱 |

P0/P1を合格しただけでP3–P5を「両対応」と宣伝しない。認定単位は`(AE version/build, SDK ABI, OS/build, arch, GPU/driver, display mode, UI scale, test scenario)`。

## Portable UI kernel と host adapter の分割

```text
ECW parameter/event contract (Adobe)
   ├── Win host adapter: .aex / PiPL / QPC / diagnostics
   ├── Mac host adapter: .plugin Universal / PiPL / monotonic clock
   └── Portable semantic kernel (no OS UI handles, no AE pointers)
         ├── document-value snapshot and immutable revision
         ├── per-view widget tree, layout, hit-test, focus/capture
         ├── draw-command plan and damage union
         └── state transitions / serialization / deterministic tests

PF_Event_DRAW -> Drawbot adapter -> host-owned supplier/surface
PF_Cmd_RENDER / SmartFX -> separate image renderer (possibly host GPU)
```

Portable kernel内に`HWND`、`NSView*`、`CGContextRef`、`ID3D12Device*`、`MTLDevice`、Drawbot`SurfaceRef`を永続保持しない。Windows/macOS adapterでもECWのネイティブ親ウィンドウ所有権を奪わない。OSで先行観測したカーソルは、座標変換が実機で認定されない限りauthoritative parameterに使用禁止。基本はAEイベント座標を正本にする。

## Effect parameter と state の契約

- `PF_Cmd_PARAM_SETUP`で一意かつ将来互換のparameter IDを設定。Custom ECWのcontrol寸法を初期指定する。CC 2014以降の動的高さは`PF_UpdateParamUI`の規定経路を使う。
- `PF_Cmd_UPDATE_PARAMS_UI`はappearance/enable stateの変更のみ。値を変更しない。公開SDKの`PF_GetCurrentState`はこのselectorで通常のrender-state照会にならない。
- `PF_Cmd_USER_CHANGED_PARAM`、許容されたuser eventでのみ値を変更し、`PF_ChangeFlag_CHANGED_VALUE`の適用条件と実ホストUndoを検証。Adobeの`PF_ParamDef`とSupervision文章にはCLICK時の記述差があるため、CLICKのchange_flags利用は**未確定のままhost fixtureで検証**し、無条件には利用しない。
- 複雑な形状・カーブ等の永続値は`PF_Param_ARBITRARY_DATA`が候補。NEW/COPY/DISPOSE/FLATTEN/UNFLATTEN/INTERP/COMPARE等、当該データ型のselector契約を埋め、disk-safeでversionedな表現を採用。再入、Undo、プロジェクトの再読込、古いバージョンを試験する。
- hover、tooltip、pointer capture、scroll位置、編集中テキスト、DPI/layout cacheはview-local。render identityや保存値へ自動昇格させない。
- `PF_PUI_STD_CONTROL_ONLY`の適用不可パラメータ型（ARBITRARY/CUSTOM/PATH等）を避ける。std control変更でarbを監督する場合はSupervisionの経路を使用。

## Drawbot/HiDPI/色・フォント

| 問題 | 採用する境界 | 計測・試験 |
| --- | --- | --- |
| UI表面 | `PF_GetDrawingReference`から現在のSupplier/Surface、DRAW内だけで描く | close/reopen、複数インスタンス、draw失敗 |
| Path/Font/Brush/Pen/Image | New系には対応した`ReleaseObject`。借用Supplier/Surfaceを解放しない | lifetime, leak, double-free, high load |
| 文字 | `SupportsText`を検査。UTF-16、表示環境のフォント、文字幅差に依存する | 和文/合字/絵文字/RTL/非対応fallbackのクリップ |
| Image | `Supports/PrefersPixelLayoutBGRA/ARGB`とstraight/premulを区別 | RGBA縁、rowbytes、拡縮、Retina |
| HiDPI | logical pane座標とraster pixel寸法を分離。SDKのoffscreen image+Surface Transform方式は候補 | 100/125/150/200%、多画面移動、point↔pixel |
| Theme | 必要に応じoverlay theme suiteを使用。ECWへの適用外観は実機で判断 | 暗/明/OS差、contrast、selection |
| Surface state | clip/transform/AAを変更した場合push/popを対にする | 異常終了時の状態汚染、次widget |
| Invalidate | 旧・新geometry＋影/AA/labelのunion、部分更新はホスト挙動確認後 | resize, folding, scrolling, all widgets repaint |

AE公式はMacのcustom UI DRAW時の前景/背景色が単純な白/黒ではないことを明記。OS既定色を無条件に前提としない。フォントの完全な1px一致はcross-platformのAPI保証ではなく、基準bitmap・許容差・fallbackと一緒に評価する。

## macOS Universalの実装ゲート

1. 対象AE版のAdobe Mac SDK sample/Xcode projectから`.plugin` bundle + resourcesを作成する。Windows `.aex`をリネームしない。
2. PiPLに`CodeMacIntel64 {"EffectMain"}`、`CodeMacARM64 {"EffectMain"}`を宣言。`lipo -archs`でarchを確認してから、**各archのAE実機ロード**を行う。
3. 全C ABI境界でC++例外を捕捉する。apple-siliconのextern C例外伝播でterminateし得るとのAdobe明記事項を守る。
4. macOS 15+のプラグインロード時には署名を検査する。Adobeは開発時のad-hoc `codesign --force --deep --sign -`を案内しており、実際の署名対象（bundle内のbinary等）は構成に従って確認する。**Release署名後にbundle内容を変更しない。**
5. **AE 26.5以降のmacOS非Betaをデバッガで追跡する場合**、Adobe公開手順では製品版のまま直接attachするのではなく、開発用コピーへの`get-task-allow`付与・再署名が必要。これはMacのloader合格や通常ユーザーへの配布に必要な操作ではない。Beta 2027以降には開発者モード手順が別にある。主環境のAEを無断で再署名/SIP変更しない。
6. native modelテストだけでなく、ECWを展開/折畳、windowをresize/移動、Retina/非Retinaのmixed display、AE再起動、project open、複数effectで実行。
7. macOS IntelとApple SiliconでGPU/OS対応ホストの現行サポートを別々に確認。Universalに両sliceがある事実は、そのAEバージョンが両CPUでサポートされている証明ではない。

## 差分試験の最低限の入力系列

```text
NEW_CONTEXT -> ACTIVATE -> DRAW
DO_CLICK(handle) -> DRAG(x1) -> DRAG(x2,last) -> DRAW
DO_CLICK(empty) -> ADJUST_CURSOR -> KEYDOWN(if received)
VIEW resize -> theme/DPI change -> DRAW
parameter external change -> UPDATE_PARAMS_UI -> DRAW
UNDO -> REDO -> SAVE -> CLOSE -> REOPEN -> DRAW
DEACTIVATE -> CLOSE_CONTEXT -> release context resources
```

イベントの実際の配送順はhost観測値として記録し、上は**試験シナリオ**でありSDKが全イベント順を約束するものではない。drag終端が到着しないケースも注入。コンポビューの`PF_Event_MOUSE_EXITED`をECWで必ず受け取ると仮定しない。

## 認定成果物とUnknown frontier

OSごとにbundle hash, PiPL/entry evidence, event trace, screenshot fixtures, pixel diff, list of unsupported capabilities, lifetime/leak trace, A/B/A p99, test OS/AE build, repro steps, failing casesを残す。テストIDとplatform別の状態は `experiments/ui-effect-controls/qualification-matrix-20261016.tsv` に分離する。

- **Existing E2-X:** Windows共通C++コアのテストはある。Mac host/ECWを試していない。
- **H:** Mac DPI/hittest parity、exact text/AA parity、native universal loader・署名・起動・Intel+ARM性能。
- **H:** OS private panel manipulationを用いた高速化は公開SDK保証外。候補扱いせず、保守経路はホストDrawbotとする。

## 一次資料と内部リンク

- Adobe Effect UI & Events: https://ae-plugins.docsforadobe.dev/effect-ui-events/effect-ui-events/
- Adobe Custom UI & Drawbot: https://ae-plugins.docsforadobe.dev/effect-ui-events/custom-ui-and-drawbot/
- Adobe PF_ParamDef: https://ae-plugins.docsforadobe.dev/effect-basics/PF_ParamDef/
- Adobe Parameter Supervision: https://ae-plugins.docsforadobe.dev/effect-details/parameter-supervision/
- Adobe Arbitrary Data: https://ae-plugins.docsforadobe.dev/effect-details/arbitrary-data-parameters/
- Adobe Apple Silicon: https://ae-plugins.docsforadobe.dev/intro/apple-silicon-support/
- Adobe Mac signing/debug: https://ae-plugins.docsforadobe.dev/intro/debugging-plug-ins/
- Adobe Mac attach AE 26.5+: https://ae-plugins.docsforadobe.dev/intro/debugging-ae-macos/
- Adobe PiPL resources: https://ae-plugins.docsforadobe.dev/intro/pipl-resources/
- Adobe Windows Arm: https://ae-plugins.docsforadobe.dev/intro/windows-on-arm-support/
- Adobe UI Tips: https://ae-plugins.docsforadobe.dev/effect-ui-events/tips-and-tricks/
- [既存Cross-Platform Matrix](../gizmo-cross-platform-contracts.md)
- [Mac host certification](../gizmo-macos-porting-certification.md)
- [Widget architecture](composite-widget-architecture.md)
- [Adversarial performance qualification](performance-and-resilience.md)
- F-UI-025: research/findings/F-UI-025-cross-platform-gizmo-performance-qualification.md (Comp/Layer gizmo evidence; ECW未認定)
