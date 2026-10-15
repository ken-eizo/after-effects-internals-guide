---
status: research-backed-qualification-protocol; no universal performance guarantee
last_verified: 2026-10-16
evidence:
  - E0-G: Adobe Drawbot, UI Event, PF_EventExtra, AsyncManager and MFR contracts
  - E0-G: Apple Instruments Time Profiler/Thread State/Display; Microsoft ETW WPR/WPA/GPUView
  - E2-L: F-UI-001..025 Comp/Layer gizmo captures; indirect host evidence only, not ECW validation
  - E2-X: GizmoSearchAE portable model selector/bench tests (not end-to-end AE guarantee)
  - H: all unmeasured scene, raster and scheduling policies
---

# Custom ECW UI — PF_Cmd_EVENT Performance and Resilience

## 命題: 「あらゆる負荷で最高性能」を検証可能な要求へ変換する

**無条件の最大応答時間は保証できない。** AEが所有するUIイベントスレッド、Drawbot配送、OSスケジューラ、GPU合成、ディスプレイのタイミングは第三者effectの制御外。任意の外部負荷・sleep・driver reset・AE hang等に対し`T_input_to_photon <= X`という有限上限を数学的に証明するためのSDK契約はない。

性能仕様を次の条件付き目標として記載する。条件が外れた時は`degraded / unavailable / unknown`に移行して報告し、silent successや未測定の0msを禁止する。

```text
for every supported environment E and declared workload class W:
    correctness(E,W) == PASS
    crash_or_UAF_or_deadlock(E,W) == 0 observed
    bounded_plugin_work(E,W) && bounded_plugin_memory(E,W)
    p99_latency_candidate(E,W) <= p99_latency_baseline(E,W) + tolerance
    evaluate miss_rate(display_deadline | demand_for_distinct_frame)
    fall_back to proven host-native Drawbot if a fast path fails
```

観測期間有限の「failure 0」は無故障の永久保証ではない。`tolerance`や合格値は製品要求として先に固定し、計測後に都合よく変更しない。どれほど軽くても表示が反映されなければ応答改善とは認定しない。

## End-to-end分解と支配項

```text
HID / mouse movement
  -> OS event queue
  -> AE message pump & active callback [cannot force]
  -> widget model update [plugin-controlled]
  -> PF_InvalidateRect / event flag [host API]
  -> AE scheduling of PF_Event_DRAW [cannot force]
  -> drawlist + Drawbot command generation [plugin-controlled]
  -> AE composition / OS compositor / GPU [cannot force]
  -> panel screen update / display scanout / photons [cannot force]
```

`T_visible = T_os_input + T_ae_queue + T_model + T_invalidate + T_draw_wait + T_drawbot + T_compositor + T_display`は概念上の段階分解。実行が重畳/非同期な区間は単純なp99の総和では表せない。時刻と因果IDの対応を記録して、**同じ入力のcritical path**を復元する。

測定単位を混同しない:
- **CPU running time:** プラグインが実際にCPUで動いた時間。
- **Elapsed/callback latency:** SDK呼出でロック待ちした時間を含む。
- **Host dispatch gap:** `DRAG`戻りから次`DRAW`入場。pluginでは直接縮められない場合がある。
- **Present/display:** drawが実画面の異なる内容になったか。単一presentに複数inputがcoalesceされ得る。
- **Optical input-to-photon:** 高速度カメラ等で測定して初めて可視応答と呼ぶ。
- **No demand:** 静止中はフレーム生成不要。静止をmissed frameとして数えない。

## Windowsの既存実測を解釈する制約

既存AEIG `F-UI-015`はREDRAW9条件の`PF_InvalidateRect`について中央値約370µs、p99約4msを記録。`F-UI-021`にはウィンドウ移動を含むUI長時間停止が存在。**どちらも「全AEバージョンの標準性能」でも「純Gizmo DRAG時の物理表示保証」でもない。**

`F-UI-022`のモデル単体同一描画抑制試験（20万入力で約10417要求）は**仮想入力による削減率**であり、同じ改善率がAEホストのscreen presentへ反映されるとは限らない。GPUフレームレンダーの数値をECW Drawbotの値へ移植しない。

## Workload class: 1つの「重い条件」に集約しない

| Class | 発火条件・負荷源 | 失敗例 | 観測するもの |
| --- | --- | --- | --- |
| W0 Idle | 空のcomp、静止・マウス停止 | 無駄なDRAW、timer busy-loop | redraw count, idle CPU |
| W1 Manipulation | 単一drag、mouse高速往復、snap/keys | last drag欠落、hit jitter | input→DRAW、pose parity |
| W2 Dense UI | 10/100/1000/10000 widget、隠れたsubtree | O(N²)、text再計算、clip破綻 | CPU drawlist, Drawbot calls, allocations |
| W3 Resize & DPI | ECW width、twirl/scroll、Retina/mixed monitor | stale bounds、ghosting | visual diff, invalidation, hit |
| W4 Host CPU | comp expression/preview/AE CPU busy | UI thread starvation | Running/Ready/Waiting stacks |
| W5 GPU contention | AE render/MFR、他GPUジョブ、高VRAM | queue wait、VRAM eviction | GPU timeline, device failure recovery |
| W6 Memory pressure | RAM/VRAM不足、paging、fragmentation | bad allocation、hard faults、thrash | private bytes, residency, stalls |
| W7 Async race | scrubとparameter edit、結果遅延、close | stale thumbnail、UAF、永久pending | purpose/revision/receipt |
| W8 Lifecycle | 100回open/close、Undo/Redo、switch project | leak、dangling handles、wrong instance | allocations, state cleanup |
| W9 OS disturbance | suspend/resume、monitor hotplug、sleep、GPU reset | unrecovered gesture、view scale mismatch | recovery / safe disable |
| W10 Concurrent host | 複数effect instances、MFR worker、different ECWs | shared mutable state race | cross-instance parity, TSAN/sanitizer where applicable |
| W11 Accessibility/input | IME、keyboard、screen-reader expectations | no navigation/OS event | delivery trace, explicit unsupported |

`W11`は性能だけでなく提供可能な入力機能の上限を判定する。AE ECW SDKが保証しない機能は試験不能を「合格」にせず、製品要求との適合可否を返す。

## Hard constraints: 最適化より先に満たす不変条件

1. 公開SDK selector、context、PiPL/GlobalSetup flags、event lifetimeの合法性。
2. 同じ値・描画（許容差を事前明示）・Undo/keyframe/保存・gesture final state。
3. `DRAWBOT_SurfaceRef`/Supplier/Path/Font/Brushの不正寿命なし、post-close callbackへのアクセスなし。
4. update regionは旧・新stroke、Bezier接続、shadow、label、AA fringeを必ず含む。単なるhover-only変更をrender identityへ昇格させない。
5. 同期render checkout、disk I/O、thread creation、コンテキスト跨ぎのmutex待ちを高頻度UI pathから除く。
6. 機能劣化を隠さない。feature不成立は明示し、最新ユーザー値・Undo・UIの最終整合性を保持。
7. Fast pathが失敗したらhost-owned full Drawbot pathに戻す。Drawbot自体が呼ばれない時は「即時再描画」を保証しない。

## Optimization ladder (保守経路→可逆な高速化)

**順序は実測支配項で修正可能。ただし安全のHard gateは変更不可。**

| Stage | 仕事を減らす場所 | 適用と効果の前提 | Failure fallback |
| --- | --- | --- | --- |
| O0 Stable | Host input + full Drawbot | 完全な絵、correct semantics | 唯一の基準 |
| O1 No-op | 等価なvisible stateではinvalidateを省略 | pixel/hit/focus equalityの確認 | O0 |
| O2 Retained CPU | widget layout/tessellation/geometryをimmutable revision cache | text/DPI/theme/scroll/data key一致 | O0/O1 |
| O3 Damage | old/new union + host update_rectに基づく部分drawlist | AE版のclip/retention behavior立証 | full pane O0 |
| O4 Batch | Path/Pen/Brush/Fontのコマンド数とallocation削減 | fill winding, AA, z-order不変 | unbatched O0 |
| O5 Visibility | viewport culling, virtual list, spatial hit index | scroll/focus/offscreen selectionに同値 | O0 |
| O6 Raster | complex static elementのoffscreen image cache | pixel format、DPI、upload、memoryを含め改善 | vector O0 |
| O7 Async | renderer依存previewをhost async requestに分離 | generation, purpose, cancel、receipt有効性 | placeholder + O0 |
| O8 Adaptive | 認定済み候補をworkload/fingerprint別に切替 | 完全なHostEvidenceとfailure rollback | O0 |

GPUをECW DRAWの後釜として独断実装しない。CPUでwidget stateを速く処理できることとGPU render selectorが速いことは別。Background workerは**portable immutable geometryやpreview data**を更新する候補だが、AEのhost-owned Drawbot参照を別スレッドへ渡したり、workerからDRAWを強制したりしない。

## Adaptive quality の許容・禁止

**許容候補:** 入力がない時の静的サブツリー計算省略、非必須diagnostic HUDの更新頻度低下、非本質的preview placeholder、LODが明示的に許されたthumbnail。visible resolution/zoom/AAの品質基準を先に固定。

**禁止:** user semantic dragイベントの間引き、最後のparameter stateの喪失、Bezier制御点位置の不正近似、Undoを潰す、勝手な色/ガンマ変更、Snapを緩める、クラッシュ/未描画をFPS改善と呼ぶ。

Hostにinputが来ない間にOS cursor観測からパラメータを先行更新することはしない。許されるとしても**描画専用のpredictive pose**であり、host座標/clipと全画質が試験済みの場合のみ。予測とauthoritative commitを分離する。

## Admission / fail-closed policy

```text
CandidateStatus = Proposed | ValidatedLocal | ValidatedInHost | Rejected | Unknown

function choose(feature, environment, workload):
    candidates = exact_match_fingerprint(feature, environment, workload)
    candidates = candidates where status == ValidatedInHost
    candidates = candidates where correct_visual_and_semantics
    candidates = candidates where lifecycle_and_memory_safe
    candidates = candidates where load_p99_and_miss_not_regressed
    return pareto_best(candidates) or StableHostDrawbot
```

ポリシー選択は**startup / scene transition / idle safe point**で行い、入力ホットパスで動的ベンチマークを実行しない。同じfingerprintでもGPU driver/AE updateにより候補証拠は失効し得る。ユーザー機での未知の性能を自動的に既知扱いしない。

無限の入力キュー・無限の非同期preview job・無限のcache residencyは不可。非同期表示専用requestはlatest-wins/coalescing、必須document editは順序を保持。バックプレッシャーでも一番新しい最終document valueを失わない。非同期cacheについて`generation`、`instance_id`、`purpose_id`、`lifetime_epoch`を照合して結果を使う。

## 計測プロトコル / 対照試験

1. ベースラインA（O0）を固定してplugin hash、SDK、OS、AE build、project/media/bitdepth、UI倍率、Refresh/VRR、CPU/GPU使用状況、バッテリー/thermal stateを記録。
2. 事前決定した操作script（DRAG trajectory、キー、scroll、resize、time scrub等）を再現。**実際の物理入力とAE event traceを関連づける**。
3. WPR/ETW+WPA（Windows）または Instruments Time Profiler + Thread State + Display（Mac）で同一因果区間のRunning/Ready/WaitとGPU/displayを分離。必要に応じて外部高速カメラ/光センサを使用。
4. A→B→Aの比較を最低3セット程度行い、warmup、記録ツール自体のoverhead、背景処理を記録する。A/Bだけでドライバーthermal driftを誤認しない。
5. それぞれ`p50,p95,p99,max,frames_demanded,frames_presented_distinct,deadline_misses,host_callback_gap,Drawbot_command_count,peak_RAM,peak_GPU/allocation,failures`を採取。
6. W0–W11を分割集計。大半がidleの全体平均によってdense-widget p99を薄めない。UI presentが計測されない場合は`unknown`であり0ではない。
7. 正確な結果・体験の同等性（undo/save/hit/AA）を確認した後にのみ性能比較を認定。`PF_Cmd_RENDER`回数とECW`PF_Event_DRAW`回数を別々に記録。
8. 再現ログには観測不能な項とconfounderを必ず残す。異なるdisplay clockを無較正に合算しない。

## Release targets — 判定のテンプレート

| Requirement | 判定 / reject rule |
| --- | --- |
| No catastrophic failure | 同じ合格条件でcrash, UAF, deadlock, bad host contextが1件でも再現すればreject |
| Semantic integrity | final drag/Undo/keyframe/save/reload/render hash差異はreject |
| O(1) or bounded UI hotpath allocations | 記録した上限を越える予測不能なallocationまたは持続リークはreject |
| p99 improvement | 指定されたWと同一fingerprintのA/B/Aで比較。統計的に不明ならcandidateは採用しない |
| Responsive fallback | unsupported suite/receipt pending/worker failureで保守経路へ戻れる |
| Mixed scale and OS | Mac実測なしのMac合格は不可。HiDPI変更直後のstale UIはreject |
| UI host hang | AE自体が停滞した場合、plugin側が停止を治したと報告しない。観測・切り分けする |
| Unbounded environment | 絶対時間保証は非目標。条件付きのperformance envelopeを開示 |

サンプルthreshold（**製品要件として事前に設定する値でありAdobe保証値ではない**）: ウォームアップ後、O0のp99より悪化しないこと。240Hz運用では1周期が約4.167msだが、「4.167msのCPU budget」ではなく実際のdisplay deadlineとpresentation miss率を扱う。プラグイン単体10µs以内を実証しても全体10µsを宣伝しない。

## 故障注入 (failures to test)

- Drawbot acquireがunsupported/nullを返す、SurfaceやText capabilityが不足。
- `PF_InvalidateRect`がエラー/不正contextになる。強制的な独自DRAWの代わりにhost-owned合法fallbackを要求。
- 非同期Previewのreceipt到着前にeffect delete、Undo、project swap、pane close。stale resultをpublishしない。
- Drag途中にfocus-loss、OS sleep、display移動、AE selection変化、cancel。
- Allocation failure／急激なVRAM pressure／多重インスタンス。容量を無限に使わず、過去のcacheを破棄して機能維持。
- 引き継がれてきた不完全/旧バージョンArbitrary Data。decode失敗時は安全な既定値か明示エラー、未初期化メモリへのアクセス禁止。
- Windows pluginがMac APIを、Mac pluginがWindows GPU backendを選ばない。Universal bundleのarm64/x86_64がそれぞれ正常loadされる。

## 実装別の残り課題

**E2-L/E2-X既存:** GizmoSearchAE Windows上のcallback-QPC/ETW、失敗例、portable selector、fixed modelベンチ。host全体の長尾は制御可能と証明されていない。

**未認定H:** W2/W4/W5/W6/W10/W11について新しい統一stress harness、Mac Intel/Apple Silicon実機、end-to-end input-to-optical、複数widgetを載せたECWの24h leak soak、IME/Accessibility可否、各高速backendのAEホスト定量改善。

これらはこのページ作成時点の**実装/実験未完**であり、文書追加を`VerifiedInHost`へ昇格させるものではない。

**再実行用の独立した実験資料:** `experiments/ui-effect-controls/qualification-matrix-20261016.tsv`（26個の判定ケースとWindows/Mac Intel/Mac ARMの状態）、`experiments/ui-gizmo-input/runs/2026-10-16-portable-core-qualification.md`（2026-10-16 Windows x64 Release CTest 6/6）。後者はあくまでE2-Xのホスト非依存試験。UI実機・Macの性能認定には流用しない。

## 一次資料 / 関連

- Adobe Drawbot: https://ae-plugins.docsforadobe.dev/effect-ui-events/custom-ui-and-drawbot/
- Adobe Effect Events: https://ae-plugins.docsforadobe.dev/effect-ui-events/effect-ui-events/
- Adobe UI Tips: https://ae-plugins.docsforadobe.dev/effect-ui-events/tips-and-tricks/
- Microsoft ETW/WPA: https://learn.microsoft.com/en-us/windows/apps/develop/performance/winui-perf
- Microsoft DirectX/GPUView: https://learn.microsoft.com/en-us/windows/win32/direct2d/profiling-directx-applications
- Apple Instruments performance: https://developer.apple.com/documentation/xcode/analyzing-the-performance-of-your-metal-app/
- Apple Instruments hangs: https://developer.apple.com/tutorials/instruments
- [Measurement acceptance](../gizmo-measurement-acceptance.md)
- [Cross-platform profiling](../gizmo-cross-platform-profiling.md)
- [Adaptive implementation](../gizmo-adaptive-implementation-architecture.md)
- [Widget framework](composite-widget-architecture.md)
- [Cross-platform release contract](cross-platform-compatibility.md)
