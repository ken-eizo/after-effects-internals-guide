---
status: research-backed-design; selector implementation separately tested
last_verified: 2026-10-14
evidence:
  - E0-G: Adobe Custom UI and Drawbot; PF EventExtra; PF OutData; MFR
  - E0-H: AE SDK 25.6 headers in local developer environment
  - E2-L: GizmoSearchAE WPR / QPC / code and benchmark artifacts
  - H: runtime backend ranking until controlled AE A/B/A
---

# Custom Comp UI — Drawbot Implementation Selection

## 目的と前提

この章は、After Effects（AE）のネイティブGizmoを、**最小CPU時間・最小メモリ・低い遅延の裾・正しい画質・高い安定性**で実装するための技術選択規則を定義する。特定のAPI（Vulkan、Direct3D、Drawbot）が常に最速だという主張は採らない。実装を決定する単位は「プラグイン全体」ではなく、各処理が属する**実行境界と所有者**である。

**基本式：正当な候補集合 C から、安全性・ABI・表示同等性・ホスト互換性という硬い制約を全て満たす候補だけを残し、その集合内で実測の長い停止と資源費用を比較する。** 未計測の候補は、いかに理論上速くても自動採用しない。

`選択 = 許可されたAPI契約 ∩ 正しい結果 ∩ 実測済みの負荷条件 ∩ 資源予算 ∩ 障害回復能力`

評価対象は以下の独立したパイプラインである。

| 実行面 / Plane | 入力・結果 | 主な所有者 | 出力の締切 |
| --- | --- | --- | --- |
| Interaction | DO_CLICK/DRAG/KEYDOWN、座標、選択、スナップ | AEイベント配送 + effect UI状態 | 入力に同期、DRAWとは別 |
| Presentation | `PF_Event_DRAW`、Drawbot Path/Surface | AE Composition/Layer UI | ホストの次のDRAW機会 |
| Render / Evaluation | `PF_Cmd_RENDER`、SmartFX、MFR、キャッシュ | AEレンダラ + effect実装 | 合成要求時 |
| GPU compute | `PF_Cmd_GPU_*`などGPU対応レンダリングセレクタ | AEが選んだGPUフレームワーク + effect | GPUレンダラ実行時 |
| OS / Display | コンポジタ、GPUキュー、DWM、スキャンアウト | Windows / GPU / 画面 | 実表示、240Hz時約4.167ms周期 |

**禁則:** GPUレンダラに対応したという事実から、AEネイティブのComposition Viewer UIが240Hz毎フレーム描画されると推論しない。DrawbotはDRAW内に限る。第三者ウィンドウを上に重ねても、ホストのネイティブGizmoへ自動的に変換されない。

## 実装候補と採用境界

| 処理 | 基本選択（現在） | より攻めた選択を許す条件 | 禁止条件・フォールバック |
| --- | --- | --- | --- |
| 編集状態 | シリアルなホストイベント順と固定長Model | 一時的な表示用コピーで遅延サンプルを利用 | DRAWからプロジェクト/永続状態を書き換えない |
| 座標変換 | AEのUI callbacksとコンテキスト座標 | DPI・Zoom・pane座標のマッピングを実機確認した限定プレビュー | OSスクリーン座標=AE view座標と無検証で決めない |
| 更新要求 | 変更があったときだけ`PF_InvalidateRect` | 全範囲の可視性を証明した有限damage、ホスト実機での比較 | KEYDOWNなど検証されていない文脈で不正呼出しをしない |
| 更新タイミング | REDRAW9系・ホスト管理の次DRAW | `PF_EO_UPDATE_NOW`等を同条件A/B/Aで選択 | 独自タイマーからDRAWを直接実行しない |
| 描画 | batched Path / Brush / Pen with lifetime-bound cleanup | Drawbotコマンド数とp99が改善した候補 | 実際のAA・色・線の見た目が変わる候補は不採用 |
| メモリ | 固定長モデル＋コールバック内の一時リソース | 有効なキャッシュ同一性と参照寿命を確立した場合のみ再利用 | 古いDrawbot Supplier/Surface/Pathを無根拠に持ち越さない |
| 画素処理 | 正しいrowbytesを守ったCPU恒等コピー | `PF_OutFlag_PIX_INDEPENDENT`など**意味的に真の契約**をA/B/Aで検証 | コピー不要・zero-copyと宣言するだけの架空APIを仮定しない |
| GPU処理 | 実画像計算がなければGPUパスを追加しない | コストがGPU転送と同期を上回り、ホストのGPU selectorが呼ばれ、フレームワーク/デバイスを検証した場合 | 独立Vulkan経路でAEの未提供UI描画権限を仮定しない |
| MFR | render状態が安全であるまで保守的に無効 | 同時呼出・sequence/cacheの所有を証明し、SDK規則を満たしたとき | mutable stateをUI/複数レンダースレッドで共有しない |

## 最適化の順序

1. **意味と所有を決める。** 機能がViewだけか、画像のrender identityへ影響するか、永続状態へ影響するかを分類。
2. **ホストの契約を固定。** 正しいイベント、参照寿命、PiPL/GlobalSetup一致、フォーマット、スレッド安全性を検証。
3. **待ちと仕事を分解。** CPU running、Ready、Waiting、SDK呼出、Drawbotコマンド、GPUキューとDWMを別に計測。
4. **支配的な費用から削る。** 同じ絵のinvalidate削除 → host call数削減 → 描画バッチ → 未使用計算削除 → 高価な画素コピー/キャッシュの最適化。数nsの算術改善よりmsのホスト同期待機を優先する。
5. **適切な比較方法を使う。** 変更前A→変更版B→A再測定、ウォームアップ、同一プロジェクト、負荷レベル/画面/AEバージョン/デバイスを記録。
6. **p99と品質を合格判定にする。** 平均のみの改善、破綻を隠す更新削除、描画フレーム偽装は不採用。
7. **不成立時は保守実装へ戻る。** 拒否されたinvalidateのpending解除、フォーカス喪失時のドラッグ終端、Render失敗、GPU不可の安全フォールバックを試験。

関連: [最適化アルゴリズム選択木](gizmo-algorithm-optimization-selection.md)、[Windows/macOS条件分離](gizmo-cross-platform-contracts.md)、[macOS実機認定](gizmo-macos-porting-certification.md)、[実行・描画の選択規則](gizmo-execution-memory-policy.md)、[実測・検証基準](gizmo-measurement-acceptance.md)、[UI入力→表示時間](interactive-ui-latency.md)。

## 形式化した決定（候補認定モデル）

実験対象について`Capability`（ホストが利用を許可したAPI）、`Semantics`（演算結果の意味）、`Evidence`（実機確認）、`Cost`（実測した資源負担）を独立して管理する。

```text
Task = {Plane, Work, HostContext, View, ImageFormat, Concurrency}
Machine = {OS, CPU, GPU, Driver, RAM, Refresh, DPI}
Candidate = {Backend, RequiredAPI, Semantics, MemoryBound, FailureFallback}
Proof = {Unmeasured | LocalOnly | VerifiedInHost | Rejected}
Result = {SelectedBackend, Reason, SupportingEvidence, Fallback}
```

選択器は**事前の測定結果を判定**するだけで、入力イベント中の高負荷測定・malloc・GPUベンチを開始しない。認定条件を変更する時は既存版を保持したA/B/A手順で再認定する。

```text
for candidate in valid_api_and_semantics(task, machine):
    if candidate.proof != VerifiedInHost:
        continue
    if candidate.has_wrong_pixels_or_crashes_or_lifetime_violations:
        continue
    if candidate.exceeds_memory_budget_or_regresses_p99:
        continue
    retain(candidate)

if no candidates:
    return stable_host_native_fallback

return nondominated_choice(
    first=lower_p99_and_display_deadline_miss,
    then=lower_peak_memory,
    then=lower_cpu_gpu_total_time
)
```

入力ドラッグの場合、ホスト内で選ぶのは`DrawbotFullScene / DrawbotPointsFast`のような**同じAPI上の命令生成**である。画像レンダラの`CPU / HostManagedGPU`は別の選択。GPUのメーカーが同じでも、レンダー出力とUI描画を混ぜて一つのbackendとは呼ばない。

### GPU損益分岐は総費用で判定

実画像計算のGPU化には、少なくとも次を計上する。

`T_gpu = T_host_checkout + T_upload_if_needed + T_dispatch + T_queue_wait + T_kernel + T_download_if_needed + T_sync + T_host_return`

`T_cpu = T_checkout + T_cpu_compute + T_host_return`

比較条件は`T_gpu.p99 < T_cpu.p99`かつメモリ予算内で、AEのGPU対応セレクタが要求したGPU/device/frameworkを遵守すること。Gizmoの小規模ハンドル幾何で`T_cpu_compute`が既に極小なら、GPU起動/同期はむしろ遅い可能性が高い。

画像キャッシュの場合は`T_render_call_count × T_render_cost`の総和を減らすことに意味があり、一回のmemcpyの命令最適化だけを見ない。UIViewの差分再描画と最終レンダーキャッシュの整合は独立に検証する。

### 既存コードへの接続（検証済みの範囲）

`D:\Developer\GizmoSearchAE\ae_plugin\GizmoImplementationSelection.hpp`に、Host/API/描画内容/検証証拠から候補を決める**副作用なしの選択関数**を設けた。

- デフォルト: 未計測のGPU/MFR/ピクセル独立最適化を選択しない。
- `Points + mode9 + drag + fast + HUD off`: 既存と同じ最短描画経路。
- dirty regionの十分性が確認されない場合: full-paneへ保守的に戻す。
- late preview: 有効なアンカー・実証した座標変換・描画範囲内でだけ候補化。
- GPU/MFR/ピクセル独立性は`VerifiedInHost`の証明フラグなしに自動有効化しない。

**重要:** 現在のAEXがこの選択器を通じて接続するのは既存の`POINTS/REDRAW9`描画経路のみ。他の分岐はテスト可能な採用規則であって、AE本体で既に適応GPU切替が完成したという意味ではない。ピクセル独立の`LeanPix`は別の事前検証用ビルドである。

この境界を守ることで、最適化の性能よりも不安定化する危険がある局面では、**品質と安全性を優先した経路**が必ず残る。

### ハードウェア別の実測候補を比較する第二段階（Host Fingerprint）

コードに`GizmoMeasuredBackendSelector.hpp`を追加し、次を比較キーにする。

`{AE build, OS build, CPU signature, GPU device, GPU driver, display millihertz, pixel depth, workload ID}`

`workload ID`にはコンポ、UIモード、色、zoom/DPI、負荷階級、テスト条件の区別を含めた**外部で管理する不透明ID**を指定する。指紋が一つでも異なれば、実測のランキングを破棄して安全なベースラインを選ぶ。実行中にCPU/GPU/driverを自力でポーリング・探索しない。収集はアイドル時、ベンチマークとユーザーの許可がある場所で行う。

各実測候補は`{delivery_p99_ns, CPU_us, peak_RAM, peak_VRAM, deadline_misses, samples, failure_count}`を持つ。選択は数値が実測された`VerifiedInHost`候補のみ。未計測、ローカルのみ、Rejected、メモリ予算超過、API非対応、参照寿命違反、画像差分、クラッシュは除外する。

**安全な保守条件:** ベースラインよりp99、missed deadlines、平均CPU、peak RAM/VRAMのいずれも悪化させない。デフォルトの最小p99改善閾値は5%（ほかにメモリや期限未達の改善があれば選択対象）。同じ指紋・同じ負荷での結果がない場合は候補index 0に戻す。これはあくまで検証用の選択ロジックであり、現在のAEXに実機計測プロファイルが自動配布されるわけではない。

`GizmoImplementationSelectionTests.cpp`では、未知・異なるドライバー・異なるモニターHz・異なるworkload ID・検証不足・VRAM不足・劣化したmiss rate・クラッシュ・参照寿命違反の各条件でindex 0に戻ることをテストした。

**将来の拡張:** OS/driver更新やAE版更新でEvidenceの有効範囲を失効させる。例外的なベンダー最適化やSIMD命令セットを使う場合も、まずその環境の能力を証明し、同じ物理出力と低いtail latencyを測定する。単純なGPU RAMの数値だけでGPU実行を選ぶことは禁止する。

## 技術候補台帳（2026-10-14時点）

候補には、**SDK契約の正しさ**、**ソース/単体テストの成功**、**AE実機での操作・画質の検証**、**AEホストでの性能改善**を別々に記録する。どれか一つの「成功」で他の軸を証明したことにはしない。

| 技術候補 | API/ローカル | AE実機の観測 | 速度改善の認定 | 次の試験 |
| --- | --- | --- | --- | --- |
| Drawbot batched path | SDK対応、ローカルAEXビルド可 | 既存の実機ログでDRAW呼出あり | Drawbot内訳は測定済み。最終240Hzは**未証明** | DRAWコマンド数とPresent分布を対照 |
| REDRAW9の更新要求 | `PF_InvalidateRect` + `PF_EO_UPDATE_NOW` | 実操作で遅延減少の主観・p50改善ログあり | 条件が完全一致したA/B/Aは未完了 | hostバージョンとp99を管理 |
| スナップ中の同一描画抑制 | Model状態機械テスト PASS | 新版AEXでの実操作未測定 | 200,000モデル入力中10,417再描画要求は**単体** | AEで呼出数/p99比較 |
| Lean Drawbot一時キャッシュ16枠 | ビルド、サイズチェック PASS | 新版AEXの描画未測定 | スタック構造量削減。GPU/host時間は未確認 | Brush/Penミス数、画質比較 |
| LeanPix `PIX_INDEPENDENT` | PiPLとGLOBAL_SETUP整合 PASS | 新AEXを実機へ未配置 | **未認定**。意味契約は恒等処理に整合 | 8/16/32bpc等価性、cache命中 |
| GPU版effect画像レンダー | SDKには専用セレクタが存在 | 本GizmoのGPU実装未完成 | **採用不可**（UI Drawbotへの置換権限ではない） | 実画像処理がある別候補で計測 |
| MFRスレッド化 | 公式契約あり | 本Gizmoに対して同時renderの安全証明なし | **採用不可** | sequence/mutable ownership監査 |
| 独立Vulkan UI overlay | 自作別ウィンドウなら描画は可能 | ネイティブAEのComposition Viewerとは同一ではない | **正式ネイティブGizmoとしては不採用** | SDKに正当な統合面が新設されるまで保留 |
| Hardware profile自動選択 | 純粋なC++候補比較/フォールバックテストPASS | 実測候補データ未投入 | 本番有効化**未認定** | 実機A/B/Aの同じ指紋で認定 |
| Windows ETW/WPR観測 | 本人操作ログ/イベント欠落0 | AE UIスレッドCPU高負荷は観測済み | ウィンドウ移動が混在し因果未確定 | ウィンドウ固定、Ready/Wait + present相関 |

### 現在の支配的な問題

未検証のプラグイン独自の画素コピーやGPU命令を高速化する前に、**AEホストUIスレッドのホスト内処理・Drawbot要求・DRAW配送の長い停止**を分離すべきである。実機条件の一例では、`PF_InvalidateRect`呼出自体に約0.37msの中央値と約4msのp99が記録され、独立のWPRではAEのUIスレッドが3秒区間で約2.06秒CPU実行していた。しかし両測定は異なる操作/セッションであり、因果的に足し合わせない。

**完成度の線引き:** この章とC++選択器は「最適な実装を証拠から選べる体系」の基礎である。AEの未公開内部コードの最適化、240Hzの物理表示を常時保証するプラグイン、全経路10µsは実現済みと主張しない。評価項目が失敗したら候補を退け、実機で再現性が得られた技術だけを昇格する。
