---
status: implementation-roadmap-with-release-gates; macOS host smoke pending
last_verified: 2026-10-14
evidence:
  - E0-G: Adobe Apple Silicon Support, PiPL, Custom UI and MFR
  - E0-H: AE SDK 25.6 normalized Windows/macOS header parity
  - E2-X: Windows portable-core build, platform fingerprint tests
---

# Custom Comp UI — macOS Effect Plug-in Porting

## 到達条件

macOSについて「対応済み」と呼ぶのは、**Intel x86_64 / Apple Silicon arm64 の対象AE版**で、実際の`.plugin`バンドルがロードされ、同じGizmoが表示・操作され、後述の品質・p99・復帰試験に合格した時だけとする。共有C++コア単体テストやmacOS ABIのヘッダー互換だけでは不足。

## 段階0: 共通CPUコアを実際のMacで動かす

```bash
cd /path/to/GizmoSearchAE
bash portable/validate_macos.sh
```

このスクリプトはmacOSでCMake+Xcode/Apple Clangを利用し、共通コアを**native architecture**として構築する。AEアプリやプラグインのインストール先は変更しない。

`portable/CMakeLists.txt`はAE SDK、Windows.h、Cocoaを参照しない。Model状態機械、Property/fuzz、ピクセルrowbytes、Redraw抑制、OS別候補選択の5テストを登録。Windows x64実機でこの5/5テスト合格を確認済み。Mac実機による合格データはまだない。

Apple Intel+ARM両スライスのビルドも確認:

```bash
cmake -S portable -B build-portable-universal -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES='arm64;x86_64'
cmake --build build-portable-universal --parallel 2
lipo -info build-portable-universal/GizmoImplementationSelectionTests
```

このUniversal形式は**純粋C++テストのMach-O**。AE effectバンドル、PiPL、実際のmacOSアプリによるLOADとは異なる。

## 段階1: SDKのバイナリ入口とPiPL

1. Adobe公式の**Mac SDK sample**（同じAE版に対応）を選び、Xcodeの`.plugin` bundle、Resources、AEFX suite helper、PiPL(`.r`)の構築方法をベースにする。Windows `.rc`をそのまま`.plugin`へ入れてはいけない。
2. MacのPiPLにはIntel/ARMを別々に宣言:
   `CodeMacIntel64 {"EffectMain"}`、`CodeMacARM64 {"EffectMain"}`。
3. `lipo -archs`で`x86_64 arm64`両方を確認。SDKのPiPLと実EffectMainの`my_version`, `out_flags`, `out_flags2`, Match Name, PiPL kindを一致させる。
4. Pluginのロード時に`PF_Cmd_GLOBAL_SETUP`→`PARAMS_SETUP`→`RENDER`等の実呼出しが起こり、host UIへ登録されることをログ/Host UIで確認。
5. Apple SiliconのC ABIの外へC++例外を送らない。`EffectMain`のtry/catch境界とNULL/unsupported suite処理を維持。
6. macOS 15+はAdobe公式のプラグインデバッグ署名要件に従う。無署名のままユーザーの主AEで無理にロードしたり、SIP回避を行わない。

Adobe: https://ae-plugins.docsforadobe.dev/intro/apple-silicon-support/
Adobe: https://ae-plugins.docsforadobe.dev/intro/exporting-symbols-in-effects/

## 段階2: OS依存箇所を隔離する

現在のGizmoSearchAEはWindows向けの`GizmoInputProbe.cpp`を含み、次のコードは**Mac対応済みではない**。

| Win処理 | Mac移植時に守る意味契約 |
| --- | --- |
| `GetCursorPos`/`GetAsyncKeyState` | AEのイベント座標が正本。Macでのscreen/pane/Retina mappingを証明するまで最新OS pointer予測を**無効** |
| `QueryPerformanceCounter` | SDKホスト単位時計をMac単調時計（`clock_gettime_nsec_np`等）へ切り替え、周波数・タイムドメインを報告 |
| `QueryThreadCycleTime` | Macのthread CPU sampleとscheduler traceで別指標化。OSごとの生cycleを比較しない |
| `GetTempPathA`, `fopen_s`, `sprintf_s` | POSIX/mac標準C++でUTF-8/prefix/safe pathを用いる。書込はUI hotpath外 |
| `GetMessageTime`, `GetTickCount64` | Windowsのメッセージ時間に対応するMac値があると仮定しない。未観測ならunknown |
| `__declspec(dllexport)` | Mach-Oのentry symbol visibilityをXcodeとPiPLで確認 |
| Windows RC PiPL | Mac Rez resource/CodeMacARM64, Intel64 |
| DPI/monitor selection | `NSScreen`のpoints/pixels、`backingScaleFactor`、host Pane zoom変換を検証 |

この表の移植完了まで、Windows-only`GizmoInputProbe.cpp`をMac用の正式なAE effectと呼ばない。共有ModelやDrawbot scene codeのポーティングが主対象であり、**UI/OS座標の異なる意味を直接持ち込まない**。

`GizmoPlatformClock.hpp`は既にWindows QPCとmacOSの単調ナノ秒時計を別々に提供する小さな抽象化。Windows側でソースビルド済み、Mac側でのコンパイルと精度は未確認。

## 段階3: 入力/描画の一致

初期実装は`HostEvent`を唯一のソースとし、CLICK/DRAG/RELEASE/DEACTIVATE/KEYDOWNを検証。Host DRAWでDrawbot supplier / surface / path / fontの参照寿命を守る。Windowsの「LATEST ON」予測座標はMacの最初の導入では**使わない**。

- 画面倍率100/200%、外部ディスプレイへの移動、物理とRetina画面、ウィンドウResize、上下左右に配置した複数モニタでノード座標が実マウスと一致。
- 旧・新ハンドル、Bezier stroke/AA、名前/テーマ色、カーソル形状、Hit Test、スナップ/Shift、最後のDRAG、DEACTIVATE、ESC復帰の全確認。
- `PF_InvalidateRect`で描画を要求。イベントからの戻りに`PF_EO_UPDATE_NOW`を立てても、ホストが240HzごとにDRAWしてくれると仮定しない。
- 画面縮小/拡大で旧/新 damage範囲が完全に塗り直され、幽霊図形が残らない。
- 実ホストでの描画と独立モデルのピクセル一致を検証する。

## 段階4: Render, cache, MFRとGPUの別承認

画像の`PF_Cmd_RENDER`はDrawbotとは異なる経路。Macでも8/16/32bpc、float HDR、rowbytes/ROI、同一メモリ、zero-alpha RGB、mask、layer crop、output extentを試験する。

`PF_OutFlag_PIX_INDEPENDENT`は意味が真の時だけ宣言し、PiPLとGlobalSetupを一致させ、各パラメータ編集/Undo/時刻変更のcacheヒットと正しい更新を確認する。WindowsのLeanPixの結果をMacのキャッシュ挙動へコピーしない。

MFRを宣言する前に`PF_EffectSequenceDataSuite1` read-only render access、UI stateとrender stateの独立性、グローバル可変データ、reentrant suite callbacks、Cancel時の配列寿命を確認。

Mac Metal effect画像GPUが必要な場合は`PF_Cmd_GPU_DEVICE_SETUP`, `PF_Cmd_SMART_PRE_RENDER`, `PF_Cmd_SMART_RENDER_GPU`, `PF_Cmd_GPU_DEVICE_SETDOWN`を公式SDKで実装。Metal render可能の宣言はDrawbot OverlayのGPU直描き権限にはならない。

## 段階5: 分布の尾と、性能低下時の選択

- 10秒程度の実ドラッグを、Mac Intel / Apple Silicon（それぞれAE版、画面refresh、Zoom固定）で3回以上測る。
- Instruments Time Profiler、Thread State Trace、Displayを別々に取り、Thread Running/Ready/Waiting、AE Drawbot CPU p99、OS compositorを対応づける。
- 同一の画質・入力処理、クラッシュ0、メモリ/CPU上限、p99と表示締切未達率がベースラインより悪化しなければ`VerifiedInHost`へ昇格。
- すべての候補には`Fallback`が必要。Macが強制終了/ロック、Render失敗、Metal device loss、API unsupported、画質差分の時は保守経路に戻す。
- 物理的な入力→光子は別途高速度カメラ/光センサで測る。それ以前の`240Hz必達`、`0.01ms total`は未証明。

## 完了の証拠となる成果物（Mac実機待ち）

- `xcrun xctrace`の`.trace`とコマンドログ
- IntelとARMのUniversal`.plugin`ファイルと`lipo`出力
- 署名/ロード可否とAE Build
- 同一pixel fixture / bitdepth/scaleで比較した画像のハッシュ
- SDKイベントcallbackのQPC/Mach時計校正・DRAWと表示の対応
- A/B/Aのp99、peak working set・GPU residency、callback数、処理内容
- CPU・GPU・WindowServer問題のWPA/Instruments相当の解析
- Signed, reproducible build, crashes/leaks none

関連: [Cross-platform contract](gizmo-cross-platform-contracts.md)、[Performance capture](gizmo-cross-platform-profiling.md)、[MFR ownership](../mfr/state-ownership.md)。
