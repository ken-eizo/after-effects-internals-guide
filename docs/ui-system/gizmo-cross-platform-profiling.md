---
status: platform-specific capture protocol; Mac execution not yet recorded
last_verified: 2026-10-14
evidence:
  - E0-G: Microsoft Windows Performance Analyzer, Apple Instruments
  - E2-L: Windows GizmoSearchAE WPR and per-event QPC data
---

# Custom Comp UI — Host Event and Presentation Profiling

## 目的

同じAE/プラグインに見える「カク付き」を、OS間で対応づけられる観測事実に分解する。**平均FPSではなく、コンテンツ変化が必要なマウス入力のうち、ホストの次DRAWと物理フレームへ届かなかった割合、p95/p99、最大値**を扱う。

```text
HID/OS event --> AE Input callback --> Model change
                              |
                              +--> PF_InvalidateRect accepted
                                      |
                                      +--> AE host scheduler (RUN/READY/WAIT)
                                                |
                                                +--> PF_Event_DRAW [Drawbot]
                                                          |
                                                          +--> Host composition
                                                                    |
                                                                    +--> GPU queue / OS compositor
                                                                              |
                                                                              +--> display scanout / photons
```

必ず**タイムドメイン**を区別する。QPC、ETW、Mach time、Instrumentsのtrace時間、GPU counter、カメラ時間を未較正のまま加算しない。Drawbot callback 240回/秒は表示光子240回/秒ではない。

## Windows経路（実機で動作確認あり）

1. AEのコンポを開き、ウィンドウを動かさず、固定したモニタ・Zoom・モードをメモ。
2. ユーザー自身が`D:\Developer\GizmoSearchAE\RECORD_GIZMO_WPR_MANUAL.cmd`でUAC許可、Enter後に操作。録画は12秒。本人操作なしのETLは標本に使わない。
3. 確認:`wpr -status`で記録が残っていないか、ETLはサイズ・SHA256・Lost Eventsが記録されているか。
4. WPAの`CPU Usage (Precise)`: AE MainWindowを所有するTIDについてRunning / Ready / Waitingを区別。ReadyThreadStackとNewThreadStackで、遅れたスレッドをreadyにした側も調べる。
5. WPAのCPU Usage (Sampled): 同じUI TIDに絞ったstackで、AE本体/Drawbot/プラグイン/ドライバのどれがCPU時間を使っているかを見る。プロセス合計をUIスレッドと混同しない。
6. GPU/DWM: 独立のPresentを画面に変化したDRAWと対応付ける。Presentイベントだけでは光子・ユニーク表示更新を証明しない。
7. スナップなし/あり、HUDなし/あり、latestなし/あり、重いレイヤー構成、CPU/GPU競合の条件を切り替えてA/B/A。

既存のWindow移動が混ざったログには約2.3秒と0.94秒のUI応答遅延が存在するが、**通常Gizmoドラッグだけの遅延とは未認定**。ETWのLost Events 0という条件も因果を補わない。

Microsoft:
https://learn.microsoft.com/en-us/windows-hardware/test/wpt/optimizing-performance-and-responsiveness-exercise-3
https://learn.microsoft.com/en-us/windows-hardware/test/wpt/cpu-analysis

## macOS経路（手順を用意、実機データ待ち）

### 必要な準備

- 実際のmacOS上でXcode/Instrumentsと`xcrun xctrace`が利用できることを確認。
- 対象Adobe After EffectsのPIDを`ps -Ao pid,comm`で確認。
- Mac Apple Silicon arm64 / Intel x86_64、OS build、AE build、GPU、メモリ、Retina scale、ProMotion設定、画面接続方式と実refreshを記録。
- Xcode Instrumentsでattachの許可がない場合、macOSの承認手順に従う。SIPを無断で無効化しない。AEの署名を勝手に書き換えない。

`D:\Developer\GizmoSearchAE\portable\capture_gizmo_macos.sh`
をMacへ持ち込むと、使用者がENTERを押してから4秒後に12秒の`xctrace`収集を開始する。
デフォルトはTime Profiler。System Trace / Game Performance / Metal System Traceの利用可否と名前は**そのXcode上の`xctrace list templates`で確認してから**指定する。

Macで取得するトレースは`.trace`であり、WindowsのETLへ変換しなければならないという要求はない。解析時に次の対応を記録する。

| Windows WPA | macOS Instruments | 比較可能な概念 |
| --- | --- | --- |
| CPU Usage (Sampled) | Time Profiler | CPU中に実行されたcall stack |
| CPU Usage (Precise) | Thread State Trace | scheduler: Running/Ready/Waiting |
| DPC/ISR/Other drivers | System Load / System Call Trace | 背景システム仕事（完全な同型ではない） |
| GPU/DWM | GPU / Display / Metal System Trace | GPUとOSディスプレイの活動 |
| RAM pages / hard faults | Virtual Memory Trace / Allocations | VM/メモリ操作 |
| QPC callback stamps | `clock_gettime_nsec_np(CLOCK_MONOTONIC_RAW)`とsignposts | plugin固有イベント |
| PresentMon frame/event | Display track / external optical | 表示周期・画面変化の検証 |

Apple:
https://developer.apple.com/documentation/xcode/analyzing-the-performance-of-your-metal-app/
https://developer.apple.com/metal/tools/
https://developer.apple.com/documentation/xcode/monitoring-your-metal-apps-graphics-performance

### Mac Instrumentsの重要な制限

- GPU TraceやMetal HUDは、AE Drawbotから表示への全段階を自動的に同定できるわけではない。アプリのMetal workloadがある場合の内訳を示す。
- Apple SiliconのGPU countersはApple GPUのpass/dispatchに対する数字。AE Composition Viewer上の既存Drawbotのpaintと1対1に結び付けるには追加のイベント対応が必要。
- InstrumentsのSystem Traceは負荷をかけるので、計測なし/計測ありの基準差も測る。長時間の全System Traceを繰り返す前にディスク空きとthermal stateを確認。
- ProMotionの可変refresh時には、静的に`1/120`で固定の描画期限があるとは仮定しない。実際のVSync/表示modeに応じて期限未達を算出する。
- Cocoaの座標にはwindow origin、scaleFactor、画面起点の違いがある。補助マウス取得が正しいピクセルと一致するまで**HostEventのみ**を使う。
- 実際の光子タイミングを測る場合、同一画面に入力パターンを生成し、高速カメラ/光学センサなどの時刻付き実験装置が必要。

## 計測プロトコルを比較可能にする最小共通スキーマ

CSV/JSON等の計測receiptには、最低限次の項目を保管する。

```text
platform, arch, os_build, ae_build, host_pid, ui_tid_or_equivalent
plugin_sha256, SDK_version, drawing_mode, event_source, test_pattern
display_id, refresh_type, measured_refresh, scaling_factor, bitdepth, zoom
t_input_received, t_state_committed, t_sdk_invalidate_begin/end
t_draw_enter/end, t_gpu_present_if_mapped, t_optical_if_measured
clock_domain, trace_start/end, lost_events, sampling_rate, instrumentation_overhead
cpu_running, ready, waiting, p50, p95, p99, max, missed_display_deadline_count
peak_private_RAM, peak_GPU_or_unified_residency, allocation_count, visual_hash
confidence, source_path, hashes, observed_confounders
```

**注意:** clock/domainの異なる未対応数値は空欄にする。present/optical未測定はゼロとせず`unknown`。macOSのUnified MemoryをWindowsのDedicated VRAM値として誤比較しない。

## 比較してよい条件 / してはいけない条件

- **よい:** Mac IntelとApple Siliconの別々のA/B/A、「同じMacで機能ON/OFF」の再現性。「同じOS/build/driver/monitor/bitdepth/Zoom」のp99比較。
- **だめ:** Windows QPCとMac Mach clockの生ticksを直に比較。Metal kernel 0.1msとWindows AE end-to-end 5msをランキング。画面を動かしたときのハングを通常ドラッグのカク付きと断定。ユーザー操作なしのトレースから入力遅延を断定。
- 可能ならAE標準のネイティブPOINT gizmoを同じコンポで測り、AEの独立したhost UI負荷を比較基準にする。内部実装が同じという推測は避ける。

関連: [Cross-platform contract](gizmo-cross-platform-contracts.md)、[計測採用基準](gizmo-measurement-acceptance.md)、[UI timing](interactive-ui-latency.md)。
