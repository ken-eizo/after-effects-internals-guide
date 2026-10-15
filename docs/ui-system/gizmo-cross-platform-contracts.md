---
status: cross-platform contract analysis; Mac host integration pending
last_verified: 2026-10-14
evidence:
  - E0-G: Adobe Effect SDK Custom UI, Apple Silicon Support, GPU build and MFR
  - E0-G: Adobe AE 26.x system requirements
  - E0-H: AE 25.6 Mac/Windows normalized header parity corpus
  - E2-X: Windows build of shared portable core
---

# Custom Comp UI — Windows/macOS Context and Drawbot Contracts

## 0. 対応の定義

「共通のソースがコンパイル可能」「AEプラグインがOSからロード可能」「AEのSDKが正しいセレクタを送る」「ハンドルが正しく描画される」「同じ画像になる」「高負荷でも十分滑らか」は**別々の合格基準**である。macOSをWindowsの実機数値で認定しない。

| 合格ゲート | Windows x64 | macOS Intel x86_64 | macOS Apple Silicon arm64 |
| --- | --- | --- | --- |
| 共通Gizmo状態機械 | Windowsでビルド/テスト成功 | **Mac実機テスト待ち** | **Mac実機テスト待ち** |
| SDK 25.6ヘッダー | ローカル解析済み | 正規化68/68一致（ソースのみ） | 正規化68/68一致（ソースのみ） |
| ネイティブプラグイン本体 | .aex Release + PiPLのABIローカル検証 | .plugin Universal/Xcodeを別途実装・検証 | .plugin Universal/Xcodeを別途実装・検証 |
| PF_Event_DRAW + Drawbot | 既存Gizmoの実機ログあり | 実機未確認 | 実機未確認 |
| 入力座標/retina/DPI | Windows実測範囲のみ | Cocoa/AE viewマッピング未証明 | Cocoa/AE viewマッピング未証明 |
| GPU/MFR | GPUエフェクトとCustom UIは別契約 | Metal GPU Smart RenderとDrawbotは別契約 | Metal GPU Smart RenderとDrawbotは別契約 |
| 物理240Hz表示 | 240Hz要求はホストへ保証されない | 実機未確認 | 実機未確認 |

**最初の採用経路は3環境で等しい:** AEに登録されたネイティブEffect Custom UIで、入力処理はホストイベント順、図形は`PF_Event_DRAW`内のDrawbotで描く。差異は座標/OS監視、パッケージ、CPU/GPU処理能力と計測ツールへ閉じ込める。

## 1. バイナリ・ビルド・SDK

| 項目 | Windows | macOS |
| --- | --- | --- |
| Plugin package | PE DLL `.aex`、RC型PiPL | Mach-O `.plugin` bundle、Rez/SDK型PiPL |
| CPU ISA | x86_64、Windows on ARMは明示サポートを個別確認 | Intel x86_64 / Apple Silicon arm64 |
| エントリ | `EffectMain`（PiPL CodeWin64等） | `CodeMacIntel64`および`CodeMacARM64`に`EffectMain`を指定 |
| 開発 | MSVC + Adobe SDK、Resource Compiler | Xcode + Mac SDK、Universal二種類のarchitectureでコンパイル |
| 例外 | EffectMain外部へC++例外を出さない | **Apple SiliconではC境界からの例外伝播がterminateにつながる**。例外を必ず内部で遮断 |
| Debug/署名 | WindowsのPE、署名/SmartScreen等別件 | macOS 15+のプラグインデバッグ時はAdobe公式に追加署名案内あり |
| SDK共通部分 | `AE_Effect.h`, Drawbot Suite, render selectorsなど | 同名・同じSDKソース契約。ただしLoader/ABIの同等性は別証明 |

Adobe SDK 25.6のAEIG既存調査では、正規化したMac/Windows公開ヘッダー68件は全て一致。**バイナリ互換・挙動一致を意味しない。** 参照：`docs/host-integration/cpp-sdk/platform-header-parity.md`。

公式: https://ae-plugins.docsforadobe.dev/intro/apple-silicon-support/
公式: https://ae-plugins.docsforadobe.dev/intro/pi-pl-resources/
公式: https://ae-plugins.docsforadobe.dev/intro/debugging-plug-ins/

Adobe現行システム要件はAEバージョンごとに変更される。AE 26.xについては同日現在のAdobe要件を基準に、Windows 11、macOS 14+の対応範囲、Windows ARM、Intel Macの制約を**ビルド・OS版ごと**に判定。過去AE 25.xのWindows 10対応をAE 26.xへ無検証で引き継がない。

https://helpx.adobe.com/jp/after-effects/desktop/get-started/technical-requirements/system-requirements.html

## 2. OS入力、スクリーン座標と画面表示

| 境界 | Windows | macOS |
| --- | --- | --- |
| 編集の正本 | AEのDO_CLICK/DRAG/KEYDOWN等 | 同じEffect SDKイベント |
| OS側の追加のポインタ観測（実験） | Win32 GetCursorPos/GetAsyncKeyState。座標マッピングが検証済みの区間に限定 | Cocoa/Quartzのmouse位置はAEのpane座標と一致しない。NSScreen配置、Retina scale、上下軸、ウィンドウ移動等の実証が必要 |
| スレッド時刻 | QueryPerformanceCounter / QPC frequency | `clock_gettime_nsec_np(CLOCK_MONOTONIC_RAW)`等のMac単調時計候補（macOS実機で較正） |
| OSスケジューリング | ETW・Windows Performance Analyzer（Running/Ready/Wait） | InstrumentsのThread State Trace / System Load / Time Profiler |
| GPU合成・表示 | GPUView、WPR GPU/DWM、PresentMon | Instruments Display/Core Animation/Metal。WindowServerの実装はAEプラグイン所有ではない |
| Refresh | モニタの実出力モード。240Hzなら4.167ms/周期 | 固定refreshとProMotion/VRR等の可変refreshを別記録 |
| 複数モニタ | DPI awareness/per-monitor scaling/混在Hz | NSScreen scale/座標originと画面移動/混在Hz |

macOSの追加ポインタサンプリングをWindowsと同じ式で有効にすることは**禁止**。Retinaや画面配置の変換不明時は、ホストから受け取ったイベント座標のみを使う。表示専用の予測座標は編集状態にコミットしない。

Drawbotは**WindowsのGDI/D3DやMacのCoreGraphics/Metalを直接呼び出すAPIではない**。Host-owned Drawbotは共通で、各OSのコンポジット境界を勝手に省略できない。入力=次のDRAW=次のVSync=画面光子という等式は成り立たない。

公式: https://ae-plugins.docsforadobe.dev/effect-ui-events/custom-ui-and-drawbot/

## 3. 実装の技術別選択マトリクス

| 処理 | Windowsでの検討 | macOSでの検討 | 実装選択の原則 |
| --- | --- | --- | --- |
| Gizmoの2D線・円・ハンドル | Drawbot Path, Stroke/Fill | 同一Drawbot Suite | native UIなら原則host SDK境界を使う |
| 24ノード程度の動作計算 | CPU固定配列（必要に応じSSE/AVX） | CPU固定配列（ARM NEON / Intel SIMDは条件付き） | ベンチでGPU dispatchより安ければCPU |
| 画像エフェクト | CPU SIMD / AE host GPU D3D12 / CUDA | CPU SIMD / AE host GPU Metal | 出力同等性とホストGPU World契約が前提 |
| 大規模image畳み込み等 | フレーム転送/中間画像が支配的ならGPU | unified memoryでもqueue,cache,syncが存在 | 単にGPU搭載でGPUを選ばない |
| 画像キャッシュ | PiPL+GlobalSetup semantic outflags | 同じsemantic outflags・別リソースパッケージ | 画像・ROI・bitdepthの真実を宣言する |
| MFR | 同時のrender selectorとsequence所有 | 同じSDK契約、AppleのObjective-C等の寿命も管理 | UI ContextとMFR render stateを共有しない |
| メモリ | host RAM/VRAM, DXGI budgetを別管理 | Apple Silicon UMA vs Intel Mac dGPUを区別 | 同一物理UMA領域をCPU/GPUで二重計上しない |
| 欠損API/劣化 | verified CPU / full-pane native fallback | verified CPU / host-coordinate native fallback | featureの拒否・クラッシュ・色差分で保守経路 |

AEIG既存のGPU技術書を必ず参照:
- [GPU cross-platform native effect](../gpu-system/cross-platform-effect-architecture.md)
- [GPU optimal effect engineering](../gpu-system/optimal-effect-engineering.md)
- [MFR state ownership](../mfr/state-ownership.md)
- [Gizmo選択体系](gizmo-adaptive-implementation-architecture.md)

## 4. OS専用の高速経路の成立条件

GPU renderを許可するには、該当版のAdobe SDKがそのホスト/GPU frameworkを提供し、実際にGPU selectorが呼ばれ、resource lifetime/queue/syncを守り、画素同等性とp99を測る必要がある。

Windows GPU: AE SDKでD3D12 Device/Queue/Worldを借りる場合はホストのqueue/resource制約を守る。独自Vulkanの高速なdispatchの存在は**AEのDRAW配送を速くする証明ではない**。

Mac GPU: Metal Device/CommandQueueの寿命、Apple Silicon UMAのStorageMode、Intel MacのManaged/Private、同期とGPU residency、GPU loss/cancelを分けて測る。Apple SiliconのUMAでも**無コストのデータ共有とは限らない**。

AppleのPerformance HUDはアプリが適切にMetalを直接使う場合の観測ツール。AE Custom UI Drawbotの全更新間隔をHUDだけで測れるとは主張しない。

公式: https://ae-plugins.docsforadobe.dev/intro/gpu-build-instructions/
Apple: https://developer.apple.com/documentation/xcode/analyzing-the-performance-of-your-metal-app/
Apple: https://developer.apple.com/documentation/metal/gpu-counters-and-counter-sample-buffers

## 5. 動作確認と既知の未達点

- Windows x64: AE 26.3の既存WPR/QPCログとRelease AEXテストがあるが、ウィンドウ移動の混入した測定をGizmo単独の停止原因と断定しない。
- Windows on ARM: AdobeがOS実行をサポートしていることと、本AEXのARM64バイナリがロードできることは別。未検証。
- macOS Intel/Apple Silicon: **今回使えるMac実機がない**。MacのAEX相当ネイティブbundle/署名/AEホスト描画・p99・240Hz・GPU/MFRは未検証。
- 共通Gizmoコアは`D:\Developer\GizmoSearchAE\portable`に独立CMake targetを作り、Windows x64で5/5テスト。Macでは同じソースをnative/Xcodeでコンパイルして独立に証明する。
- macOS GPUドライバー・OS・画面Hzの違いをWindows証拠で埋めない。認定対象は個別のhost fingerprintである。

リンク: [計測プロトコル](gizmo-cross-platform-profiling.md)、[Mac移植受け入れ](gizmo-macos-porting-certification.md)。
