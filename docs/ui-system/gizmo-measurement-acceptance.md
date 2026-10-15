---
status: measurement-protocol-active
last_verified: 2026-10-14
evidence:
  - E0-G: Adobe Custom UI/Drawbot, GPU, MFR, PF EventExtra
  - E2-L: GizmoSearchAE CPU/Drawbot profiler and ETW/WPR traces
  - E2-X: standalone model/copy regression benchmarks (AE integration unverified)
---

# Custom Comp UI — AE-host Measurement and Acceptance

## 1. 評価軸を一つの「FPS」に潰さない

| 観測境界 | 開始→終了 | 使用する観測器 | その値が**証明しない**こと |
| --- | --- | --- | --- |
| Input arrival | OS/HID → AE event入場 | ETW/HIDとQPC較正 | Drawbot表示完了 |
| Model CPU | イベント中の自作演算 | QPC単発分布・固定入力ベンチ | 実機ホストp99 |
| Host redraw API | Suite acquire → `PF_InvalidateRect` → release | サブステージQPC + ThreadCycleTime | DRAW配送や物理画面 |
| Scheduling | DRAG戻り→次DRAW入場 | AEログ + ETW CSwitch/ReadyThread | GPU Present |
| Drawbot CPU | DRAW内の命令発行/Release | コールバック内サンプリング | GPUによる表示 |
| Render / cache | 実render selectorの回数、時間と結果 | Render計測、AE RG/BEE trace | UI overlay描画頻度 |
| GPU/DWM | 描画投入→キュー→合成→present | WPR GPU/DWM・WPA・PresentMon | 最終画面光学応答 |
| Visual | マウス動作→画面上の見える変化 | 高速度カメラ/光学センサー | 内部キャッシュヒット |

**240Hz = 1/240秒 ≈ 4166.67µs**。DRAWコールバックが240回/秒でも「毎回ユニークな画像がpresentされた」ことにはならない。60Hz単位のAE Event `when`値を60fps入力配送の証拠にもしない。

`10µs`は**選んだCPU内の純粋な局所処理**で達成可能な目標として分離する。GPU、AE配送、OS、スキャンアウトを含めた10µsは本体系の保証条件にしない。画面期限については240Hzの4.167ms予算とp99、miss rateで報告する。

## 2. 収集する単位・環境フィンガープリント

すべての試験で、AE version/build、plugin AEX SHA256、PiPLとGLOBAL_SETUPのOutFlags、Windows version、CPU/core数、GPU/driver、メモリ空き、画面refresh/DPI/接続方式（物理/仮想）、コンポ/bitdepth/レイヤー数、モニタ移動の有無、CPU/GPU負荷、WPR収集期間とイベント欠落数、ドラッグ方式を採取する。

コールバックごとの時刻は単調時計のticksと同一セッションの周波数で持つ。別コア、別プロセス、ETWの時計を無較正で引き算しない。**イベントを操作しなかった時間**やウィンドウドラッグを混ぜた結果は、Gizmoによるinput-to-photonの証拠ではない。

過去の独立ログ例：

- REDRAW9の`PF_InvalidateRect`測定で中央値約370µs、p99約4ms（対象実行条件に依存）。
- ユーザー操作を含むWPRでAEメインUIスレッドは0–9秒53%、9–12秒69%、12–15秒31%相当をCPUで実行。約2.3秒/0.94秒のUI遅延は**ウィンドウ移動と混在**している。
- モデル単体20万入力のsnap抑制は10,417回の再描画要求（従来200,000）だった。**AEでの改善量ではない。**
- 4K RGBA8 CPUコピーp50約2.83ms/p99約3.98msは別プロセスのベンチであって、Gizmoの実Render頻度を表さない。

原本は`F-UI-015`、`F-UI-020`、`F-UI-021`、`F-UI-022`、`F-UI-023`および`D:\Developer\GizmoSearchAE`の研究ログ参照。

## 3. ハード制約（1つでも失敗すれば不採用）

1. **API適合**: イベント文脈、host owner、ABI、PiPL/GlobalSetup、SDKのDrawbot/MFR/GPU所有条件を守る。
2. **画質と操作の同一性**: 旧・新の合成画像をbitdepth別に差分比較。ハンドルのAA、stroke、色、選択・フォーカス、Zoom/DPI、Undo、最後のdrag、ESC/DEACTIVATEに退行がない。
3. **資源と安定性**: Scene exit、Device setdown、Host cancel、SDK拒否、メモリ不足時にリーク、クラッシュ、参照切れ、永久pendingがない。
4. **能力検出**: 利用しないGPUパスを勝手に有効化しない。公開SDKが報告したhost/device capabilityに基づき、未サポート時はCPU/Drawbotへフォールバックする。
5. **実機証拠**: 実際のAEホストで期待効果を再現するまで、新候補をreleaseの自動選択に加えない。

## 4. 数値評価: 尾部遅延と資源のPareto選択

各候補について、環境ごとの`{p50,p95,p99,max,miss_240hz, CPU_us_per_drag, host_call_count, DRAW_cmd_count, peak_private_bytes, GPU_mem_bytes, failure_count}`を保存。

**評価優先順:** 安全・画質合格 > p99の改善 > 240Hz期限未達の減少 > peak memory > 全体CPU/GPU時間。平均の差が測定ノイズ程度でも採用しない。安定性悪化を性能改善で相殺しない。

現場用の目安（仮説段階のガイドであり、Adobeの仕様保証ではない）:
- microbenchは多数回のウォームアップと各入力パケットの分布を別々に取得。まとめた測定ブロックのp99を1呼出しのp99と呼ばない。
- 実ホスト測定を最低3回、A→B→Aの交互測定とし、異なる負荷条件での退化をチェックする。
- p99が悪化、不可視状態の破綻、SDKエラー、visual差分、キャッシュのstale reuseが1度でもあれば採用延期。
- 比較の記録は`status = proposed / validated-local / validated-in-host / rejected / unknown`を使用。ホストで再測定していないLeanPix等はvalidated-in-hostへ昇格させない。

## 5. 実験マトリクス

| 要因 | 必ず試す条件 | 意味 |
| --- | --- | --- |
| マウス | POINTS/Transform/Bezier、低速・高速・反転、Snap/Shift/Ctrl | 連続状態と離散状態 |
| Host | AE 26.3実機、可能な別AE版、他プラグインがある/ない条件 | 版依存・外部負荷 |
| 画面 | 240Hz物理、他refresh、HiDPI、view zoom、pane移動 | UI座標/提示 |
| Render | 静止/動画像、8/16/32bpc、masked/transform、1080p/4K | Output等価性 |
| Render threading | MFR有効/無効、複数インスタンス、並列フレーム | 共有状態・寿命 |
| Load | AEアイドル/重いコンポ再生/CPU競合/GPU競合 | long tail |
| Failure | 出力拒否、context close、別モニタ移動、GPU reset、起動/終了 | フォールバック |

## 6. 推奨する比較実験の順序

- ベースライン版Aをバックアップし、既にホストで確認済みの振る舞いを保存する。
- 最小合成を使用し、計測前ウォームアップを揃える。
- DWMとGPU/WPR収集は必要な場合だけ短時間行い、計測自体の負荷を別条件で定量化する。
- 新版Bに差し替えるにはAE終了が必要。**稼働中プラグインをホットスワップしない。**
- 実験Bが適合したら再び版Aに戻して時刻・熱・バックグラウンド負荷を確認。
- 計測開始時に入力を再現。操作をしていないトレースを「Gizmoドラッグのp99」として使わない。
- 公式SDKと一致する性能/意味契約のみをAEIGの**採用済み技術**に昇格。

関連: [実装選択](gizmo-adaptive-implementation-architecture.md)、[メモリ/ホスト](gizmo-execution-memory-policy.md)、[UI時間](interactive-ui-latency.md)。
