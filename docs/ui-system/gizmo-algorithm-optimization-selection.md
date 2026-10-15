---
status: algorithm-catalog-with-explicit-adoption-gates
last_verified: 2026-10-14
evidence:
  - E0-G: Adobe SDK UI, Effect flags, GPU and MFR contracts
  - E0-G: Apple Metal performance / Microsoft WPT
  - E2-X: GizmoSearchAE CPU microbench and regression tests
  - H: unmeasured alternative algorithms
---

# Custom Comp UI — Drawbot Optimization and Event Cost

## I. 性能を支配する「仕事の型」

実装者がまず知るべきはGPU名ではなく、現在の仕事の分類である。

```text
Task
├─ UI EVENT: click/drag/hover/keyboard
│  ├─ short fixed-size model update -> CPU scalar/inlining
│  ├─ bounded geometry build -> CPU precompute/batch Drawbot
│  ├─ no visible change -> do NOT request redundant host repaint
│  └─ changed -> legal PF_InvalidateRect, host DRAW wait
├─ NATIVE OVERLAY: PF_Event_DRAW
│  ├─ Drawbot Path, Stroke, Fill, text via host-owned Surface
│  ├─ geometry / AA / colors fully equivalent
│  ├─ owner-lifetime per DRAW; no direct Metal/D3D injection
│  └─ host compositor and refresh have independent budgets
├─ FRAME RENDER: PF_Cmd_RENDER / SMART_RENDER
│  ├─ identity -> pure rowbytes-correct copy and legal caching hints
│  ├─ few pixels -> CPU fallback candidate
│  ├─ SIMD suitable -> AVX2 / SSE / ARM NEON after capability and parity
│  ├─ large image -> host-compatible D3D12/CUDA/Metal candidate
│  ├─ large separable kernel -> separable / tiled direct
│  └─ generic large convolution -> overlap-save/FFT only after thresholds
└─ OS/Presentation
   ├─ Windows -> ETW/WPA, GPU/DWM/PresentMon
   └─ macOS -> Instruments Thread State / GPU / Display
```

**最高性能とは、正しい結果の範囲でp99の長い停止を減らし、メモリとCPU/GPU仕事量を抑えること。** 競技プログラミングの計算量改善でも、支配項がAEへの0.3〜4msのAPI呼出なら、その呼出数を削るほうが効果が大きい。Amdahlの法則により、全体の1%を占める演算を10倍にしても全体の改善はおおむね1%に満たない。

## II. CPUモデルの計算量を下げる

| 候補 | 大きさと利点 | 不採用の条件 |
| --- | --- | --- |
| 固定長`std::array`とlinear scan | ノード数`N≤24`程度なら実装が単純、連続アクセス | 広大な独立オブジェクトが増えO(N)が支配する場合 |
| 差分state・dirty generation | 見た目に変化がないDRAGを早期終了。ホスト更新削減 | HUDや点滅など別の見た目が変化しているとき |
| snap後に可視座標の等価判定 | 同じpixel / quantized poseにまとめる | 更新すべきselection/hover/hitが変わる場合 |
| SIMD/NEON/AVX2 | 大量の座標変換や配列演算で候補 | 小さい固定配列、分岐だらけ、変換・同期コストが大きいとき |
| spatial index / BVH / grid hashing | ハンドル数が数千を超えるときの近傍探索 | 数十個のノードではindex構築とキャッシュミスが上回る場合 |
| 近似数学・fast-math | 誤差が明示許容されたプレビューに限定 | Hit Test、Snap境界、描画座標、Undo値を変える場合 |

ノード数が少ない場合、枝刈りのための枝分かれ・ヒープ確保・ハッシュ表の導入はむしろ遅くなる。大きな`O(N log N)`手法が小さな`O(N)`を必ず超えることはない。

## III. Drawbot命令とホスト更新費用を下げる

1. UI状態の更新と描画依頼を分離する。ホストイベントの正本入力は絶対に落とさない。
2. 旧形状と新形状に変化がないならHost Invalidator呼出を省略（診断HUDの描画要求は維持）。
3. Drawbotのパスは同色・同種単位でまとめ、Path/NewBrush/NewPen/Releaseの実数を計測する。
4. finite dirty rectの採用条件は、旧・新位置、Bezierの接続辺、線幅、AA fringe、選択/スナップハンドル、tooltip/textすべてを包含すること。完全包含が証明できなければfull paneを選ぶ。
5. 画像やグラフィックを描画するためにOS外部のタイマーで`PF_Event_DRAW`を模倣しない。AEが所有するUI frame scheduleを尊重する。
6. Drawbotの`Surface`、`Supplier`、`Path`、`Brush`の参照を、ドキュメントの有効期間を超えて再利用しない。

**最も重要な定量指標**は「1クリックあたりのDrawbot呼出数」ではなく、**状態が変化したDRAGから物理的に対応する新しい表示が出るまで**のp99、及びその区間にホスト/OSが何を実行し待っていたか。

## IV. Image RenderとGPUの損益分岐

`T_cpu = checkout + CPU_compute + host_return`

`T_gpu = checkout + optional_upload + encode + queue_wait + GPU_compute + optional_download + synchronize + host_return`

各項は重畳することがあるため独立p99を単純合算して総p99にしない。同じタイムライン上のcritical pathを測る。

- Windows DirectX12はAEが提供する`ID3D12Device`/`ID3D12CommandQueue`/`GPU Worlds`に従う。
- Windows NVIDIAではCUDA APIも候補。ホストのCUDA context/streamと渡されたWorld資源の規約を守る。
- macOS MetalはApple Silicon UMA、Intel Mac dGPUでmemory storage/同期が異なる。論理的にメモリ共有できても自動的にコピーや同期がゼロにはならない。
- GPUカーネル起動に伴うfixed costを、小規模Gizmo CPUの数十ns〜数µsに対して支払う根拠はない。Native overlay描画の経路はGPU Render selectorの選択で短縮されるとは限らない。
- 大規模画像処理ならtiling、kernel fusion、separable convolution、FFT/overlap-save、低寿命scratchとトラフィック削減を検証する。色域/float HDR/alpha/ROIの意味を変えない。
- macOS Metal Shader Converterを利用するHLSL共通ソースは、Shader ABI/binding/argument-buffer・ドライバ条件を認定してから採用。自動的にネイティブMSLより速いとは仮定しない。

## V. メモリ予算の形式化

`peak_plugin_RAM ≤ model + event_state + (render_scratch × max_inflight_frames) + diagnostics`

`peak_plugin_GPU ≤ pipelines + textures + (gpu_scratch × max_inflight) + needed_residency`

- WindowsではDedicated VRAMとCPU RAMの限界・予算/evictionを区別。DXGI Budgetはプラグインの割当保証ではない。
- Apple Siliconでは統合物理メモリ。CPUとGPUの単純な足算で二重カウントしない。メモリpressure・デバイスのworking set・コピーの有無も見る。
- Intel Mac dGPUはUnified Memoryという仮定をせず、必要なMetal resource storage modeの転送/同期を計測する。
- あらゆる共有scratch、frame cache、command-bufferのデバイス所有・MFR concurrency、最終使用後の破棄を証明する。
- 競合するGPU作業があるとき、高優先度/大VRAMの使用を無断で強制しない。低メモリ候補へ安全にフォールバックできる設計を評価。

## VI. 安定性の硬いゲートと限界

正確さを破った高速化は不採用。次は**一つでも失敗したら棄却**：

- AE公開SDKのcontext/selector/edition/ABI契約不一致
- 参照のuse-after-free、double free、GPU done-before-fence
- 一つでも視覚/Pixel差分、Undo/Selection失敗、Hostイベント喪失
- 未処理の例外がmacOS `EffectMain`のC ABIを越える
- ホストのrender/MFRでデータ競合、デバイスセットダウン/Cancel時リーク
- 競合負荷のある条件でp99・missed deadline・peak memoryが退化
- Windows測定データを別Mac/Apple GPUに自動適用

## VII. 参照すべき一次資料と研究

- Adobe SDK: https://ae-plugins.docsforadobe.dev/effect-ui-events/custom-ui-and-drawbot/
- Adobe MFR: https://ae-plugins.docsforadobe.dev/effect-details/multi-frame-rendering-in-ae/
- Adobe GPU: https://ae-plugins.docsforadobe.dev/intro/gpu-build-instructions/
- Intel optimization guide: https://www.intel.com/content/www/us/en/developer/articles/technical/intel64-and-ia32-architectures-optimization.html
- Apple Instruments: https://developer.apple.com/documentation/xcode/analyzing-the-performance-of-your-metal-app/
- Microsoft WPA Critical Path: https://learn.microsoft.com/en-us/windows-hardware/test/wpt/optimizing-performance-and-responsiveness-exercise-3
- Google: https://research.google/pubs/the-tail-at-scale/
- AEIG [Cross-platform architecture](gizmo-cross-platform-contracts.md)
- AEIG [Measurement](gizmo-measurement-acceptance.md)
