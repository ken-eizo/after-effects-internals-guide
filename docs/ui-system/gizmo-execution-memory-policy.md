---
status: evidence-bounded-design
last_verified: 2026-10-14
evidence:
  - E0-G: Adobe Drawbot; event redraw; GPU/MFR and PF OutFlags
  - E2-L: GizmoSearchAE CPU/Drawbot and WPR data
  - H: unverified optimizations are hypotheses, not defaults
---

# Custom Comp UI — PF_Cmd_EVENT Execution and Memory Boundaries

## 1. 分岐してよい境界と、してはいけない境界

実装の自動選択は**処理の意味が保たれる範囲**で行う。「GPUが高速」という属性だけでGPUを選択しない。GPUには転送、カーネル起動、同期、ホストとのデータ境界、CPUへの戻しが含まれ、Drawbot Custom UIとは別である。

### 入力および状態管理（低レイテンシ面）

- UIのAuthoritative stateはAEイベントの順序で更新する。DO_CLICK、DRAG、最後のDRAG、DEACTIVATEを順序付きトランザクションとして扱う。
- 純粋なModel計算は固定長配列を使い、入力コールバック内ではディスクI/O・ヒープ確保・スレッド生成・待機をしない。競技プログラミング的な局所性、同一性チェック、早期終了をここに適用する。
- スナップ・軸ロックで最終図形に差がない場合、入力追跡は維持したまま不要な再描画要求を削除できる（`F-UI-022`）。
- コールバックの座標値はAEのView/Composition/Layer座標を区別する。OS座標のlate-latchは計測で正しいことを検証するまで候補であり、Adobe UI callbackを回避する正規の変換として一般化しない。
- パラメーターの永続化とUndoが必要な本番Gizmoは、ビュー上のModelだけで完結する実験Gizmoとは異なる。変更のコミット点をAEのAPIとtransactionに合わせる。

### 描画（ホストコントロール面）

- `PF_Event_DRAW`以外でDrawbot描画は行わない。Drawbot参照はイベント内で取得し、正常/異常経路を問わず対応するSuite/オブジェクトを解放する。
- 色、線幅、塗りをキーとしたBrush/Penキャッシュは**そのDRAW内だけ**有効とする。大量の色の時は所有付き一時オブジェクトへフォールバックする。
- 複数ハンドルを単一Pathにまとめることは既に実装済み。今後の採用条件は「更に命令数が減った」ではなく、**実際のhost DRAW p99が改善し、表示画像が同一**であること。
- 全画面invalidateは安全な基準。有限damageは旧・新位置、連結辺、stroke、AA、ラベルとlate previewを含む場合のみ候補化する。領域unionを省くcoalescingは禁止。
- `PF_EO_UPDATE_NOW`は次のDRAWを早く要求するだけであり、GPUのPresentや画面の240Hz周期を保証しない。パスは確認されたホストバージョン単位で比較する。

### Pixel evaluation / キャッシュ面

- カスタムGizmoのUIとエフェクトのピクセルレンダリングは独立した契約。DrawbotをGPU selectorへ移せばネイティブComp UIが高速化するという主張はしない。
- ピクセル恒等コピーなら`PF_OutFlag_PIX_INDEPENDENT`は意味上の候補。ただしホストのキャッシュ削減は実測で判定する。`LeanPix`は試験版（`F-UI-023`）。
- rowbytes、入力/出力別バッファ、同一メモリ、8/16/32bpc、ゼロアルファRGB、ROI、マスク/レイヤー変換が異なる場合の同等性を保持する。単なる`memcpy`置換や「zero-copy」は契約なしに保証しない。
- 画像の実処理が複雑なら、CPU SIMD / GPU実装を別候補として測る。転送・キュー・同期・一時バッファ・AEが要求するpixel formatを含む実測総費用で決める。
- `PF_OutFlag2_SUPPORTS_GPU_RENDER_F32`はImage renderのホストGPU処理宣言であり、Composition viewer Drawbot APIの改造権限ではない。
- `PF_OutFlag2_SUPPORTS_THREADED_RENDERING`は複数フレームの同時レンダーが安全だという**宣言**。UIのContext状態、sequence_dataとキャッシュ所有をチェックせず付けない。

## 2. メモリ予算・資源寿命

| 区分 | 上限の定義 | 典型的な所有 | 削減方針 |
| --- | --- | --- | --- |
| Model | 同一インスタンスの固定サイズ | effect Context | kMaxNodesと属性を予算化、O(N)は最大Nで評価 |
| UI event context | 旧参照を残さない | AE | DRAW境界外へ借用参照を持ち越さない |
| Drawbot transient | DRAWごとのPath/Brush/Pen/Font | Drawbot Supplier契約 | scoped RAII、同一DRAW内バッチ/キャッシュ |
| Render scratch | フレーム/タイル単位で計測 | AEレンダー/プラグイン | 入力と出力の別名・寿命契約、GPU/CPU resident両方を計上 |
| Diagnostics | release版では0または既知の上限 | plugin | サンプリング専用ビルド; ホットパスでログ書込しない |
| Host caches | ユーザー/AE管理の一部 | AE | 不必要なoutflagとwide dependencyを減らし、暗黙のキャッシュ専有をしない |
| GPU residency | GPU frameworkとAE device scope | AE + effect | GPU device setdownで解放、VRAM容量だけで可否を決めない |

現在のGizmoSearchAE Leanでは`Context < 16KiB`、`Surface < 2KiB`をコンパイル時に検査している。これらは**プラグイン構造体**の上限であり、AE本体、ホストDrawbotリソース、GPUメモリ総量の上限ではない。GPUメモリとWindowsの物理RAMは別勘定で記録する。

## 3. スレッド、再入、ホスト負荷への耐性

- Custom UIの入力状態に対する書込は、実際のAEイベント順が保証する範囲に限定し、MFR render workerと競合するグローバル可変状態へ共有しない。
- `ThreadSafe`やMFRを宣言する前に、SequenceData取得方法、フレームごとの一時状態、参照カウント、GPU device setdown、AEプロジェクト終了時の破棄をレビューする。
- 重いホストのUIスレッドはGizmoのモデル計算を10µsにしても止まることがある。WPRでRunning / Ready / Waitingを別測定し、ロック待ちや優先度を原因と推定する前にスレッド切替・スタックで検証する。
- UIコールバック中の独自ワーカー作成、ThreadPriority/ProcessPriorityの一方的な引き上げ、AEメモリへのパッチ、別窓GPUオーバーレイは、安全な高速化手段とは扱わない。
- コールバックでのリクエスト受理はDRAW完了でない。DRAW完了はGPU Present完了でない。GPU Presentは画面発光時刻でない。状態は別のカウンターで扱う。
- 入力最後のリリースが未配送でもDEACTIVATEでpendingを破棄し、当該ホストイベントで再描画できる状態へ復帰する。SDKがinvalidateを拒否した時はpendingを取り消す。

## 4. 選択を制御する「証明フラグ」

処理経路を切り替える条件は、CPU名やGPUブランドでなく、そのホスト条件に対して保持した証拠とする。

`候補 = API対応 && Context有効 && 出力同等 && 参照寿命安全 && 実機測定済 && (p99改善または予算遵守)`

各候補の`VerifiedInHost`は、**AEバージョン、OSビルド、画面Hz、GPUとドライバー、色深度、view倍率、CPU負荷区分、テスト結果ハッシュ**を結び付けた記録である。別環境では自動的に`Untested`へ戻す。ハードウェア型名のみで実測済み証拠を再利用しない。

試行したが画質不一致・クラッシュ・極端なp99退化を示した候補は`Rejected`とし、後のシステム更新時も勝手に採用しない。

関連: [アーキテクチャ](gizmo-adaptive-implementation-architecture.md)、[計測と合否](gizmo-measurement-acceptance.md)、[Drawbot資源](drawbot-ui-drawing.md)、[MFR状態所有](../mfr/state-ownership.md)。
