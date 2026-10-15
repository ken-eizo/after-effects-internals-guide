---
status: proposed-reference-architecture; host-specific integration pending
last_verified: 2026-10-16
evidence:
  - E0-G: Adobe Effect UI & Events, PF_EventExtra/Union, Drawbot suites
  - E0-G: Adobe PF_ParamDef, Parameter Supervision and Arbitrary Data selectors
  - E0-H: AE_EffectUI.h, DrawbotSuite.h (local SDK 25.6 references in AEIG)
  - E2-L: F-UI-001 through F-UI-025 Comp/Layer gizmo evidence; indirect host scheduling only, not ECW verification
  - H: retained widget tree / layout batching / accessibility implementation performance
---

# Custom ECW UI — PF_PUI_CONTROL Widget Composition

## 位置付け

**これは実装済みのGUIライブラリの説明ではない。** After Effects ECWの1個または複数のcustom parameter control内に、Slider、Bezier/Curve、XY、Timeline-like view、List、Tree、Icon Button、Color Ramp、Lens Editor等を統合する際の**提案するポータブルアーキテクチャ**と、実機昇格条件を定義する。

Win32 HWND/Cocoa NSView/HTMLをECW内へ任意に「ネイティブ追加」できるという公開SDK契約はない。公式の入口は`PF_PUI_CONTROL` / `PF_PUI_TOPIC`によるホスト所有の領域、`PF_Cmd_EVENT`、`PF_Event_DRAW`のDrawbotである。個々のwidgetにAEの独立したフォーカス/キーボード/アクセシビリティオブジェクトが自動生成されるわけではない。

**ECW専用adapter契約:** `PF_Context.w_type == PF_Window_EFFECT`のイベントのみを受理し、`PF_EventExtra`の`PF_EffectWindowInfo.index`で対象パラメータを、`area`の`PF_EA_PARAM_TITLE` / `PF_EA_CONTROL`でタイトルと編集領域を区別する。`current_frame` / `param_title_frame` / `horiz_offset`を座標・クリッピングの入力として解釈し、Twirlの開閉と制御領域の有無を常に考慮する。**Comp/Layerビューの座標・drag実測をECW内のイベント配送の保証として使わない。**

## 所有者と層の定義

```text
AE-host ECW and parameter streams (authoritative)
 └─ Effect UI adapter: lifecycle, suite acquisition, event conversions
     └─ WidgetRuntime (portable; per view/context)
         ├─ DocumentSnapshot (immutable versioned values; never owns PF_ParamDef*)
         ├─ InteractionState (pointer capture/focus/hover/keyboard/drag)
         ├─ LayoutTree (stable widget ID, logical bounds, clip/z-order)
         ├─ InputRouter (reverse-order hit test, capture and bubbling policy)
         ├─ DrawList (immutable logical primitives, text/image commands)
         ├─ DamageTracker (old ∪ new bounds + stroke/AA/labels)
         └─ RevisionGate (layout, style, data, DPI, async-preview generations)
             ↓
       DrawbotBridge [DRAW callback scoped resources] → host Surface
     └─ ParameterCommit [only permitted host selectors]
     └─ AsyncPreviewBridge [host AsyncManager purpose / receipt lifetime]
```

`WidgetRuntime`はAE plugin instanceとview/contextを区別する。同じEffectの複数ECW、複数コンポ、異なる倍率にまたがって`activeWidget`や`dragStart`をグローバル共有しない。主たるパラメータ値はAEが所有し、UIはその時点のsnapshotを保持する。

## Widget contract — 最小の再利用可能な公開表面（設計案）

| Interface | 入力 | 出力 | 保持禁止 |
| --- | --- | --- | --- |
| `measure(const Constraints&, Style, Scale)` | logical width/height constraints | preferred/min/max size | AE render checkout, AE Suite handle |
| `arrange(Rect, LayoutRevision)` | parent logical rect | stable child rects | OS DPIを暗黙に掛け直す |
| `hitTest(Point, Clip, Visibility)` | host→logical transformed point | optional widget ID + region | hidden/outside clipへのhit |
| `onInput(Event, StateSnapshot)` | ordered host input | pure state delta + intent | PF_ParamDef*を永続化 |
| `paint(const ViewSnapshot&, DrawList&)` | immutable snapshot | logical draw commands | Drawbot Supplier/Surfaceのretain |
| `damage(previous, next)` | old/new visual bounds | conservative union | stroke, shadow, textを除外 |
| `serializeValue(Version)` | document semantic values only | schema-versioned data | view hover、capture、tooltip |
| `cancel(reason)` | deactivation, context close, project switch | safe idle state | 未完了drag/workerの参照 |

**Widget tree != AE parameter tree.** 各子widgetがAEの真のnative property streamになるわけではない。個別のkeyframe/expressions/undoが必要なら、実際にAEへ登録されたParameter streamを使うか、Arbitrary Dataの補間・保存契約を設計し、それぞれの制約を明示する。

## Layout / DPI / styling

1. 基準座標は**logical ECW pane coordinates**。physical pixelsと区別し、hostイベントからの変換関数を全入力と描画で共有。
2. Layout計算にはwidth/height、label/title、font metrics、control minimum、pane scrolling/collapse、content scale、text directionを入力。入力が同じならlayoutが同じというdeterminismを要求。
3. Flex/stack/grid等の配置はportable純粋処理として構成。親Clipと子Clipを交差させてZ-orderの逆順でhitする。可視外はhitしない。
4. レイアウト変更時は**旧表示領域と新表示領域を同時にinvalidate**。折り畳み、ECW幅変更、localeやfont変化ではfull pane fallbackを許す。
5. Scaleは**1回だけ**変換。stroke/hit radius/antialiasは物理pixel閾値かlogical単位かを個々に宣言し、Win per-monitor DPI と Mac Retina を混同しない。
6. z-indexを頻繁にソートしない。可視範囲に応じた部分Layout/virtualizationは複雑度が十分大きい場合だけ実測採用。
7. AEのnative controlsと同じ見た目を求める場合も、SDKに公開されたhost theme primitivesの範囲のみを保証する。OS文字レンダラのピクセル完全一致は別ゲート。

## イベント機械 — capture・focus・commit

```text
Idle
  ├─ DO_CLICK(hit) -> Pressed(widget_id, start_value, pointer)
  │                    request send_drag where valid
  ├─ ADJUST_CURSOR -> hit-test + requested host cursor
  └─ KEYDOWN(if AE forwards) -> validated widget-local action

Pressed
  ├─ DRAG -> Dragging(capture_id, preview_value, dirty bounds)
  ├─ DRAG(last) -> Commit(final_value) -> Idle
  ├─ DEACTIVATE/CLOSE -> CancelOrCommitByExplicitPolicy -> Idle
  └─ unrelated context/instance event -> ignored or separately routed

Dragging
  ├─ DRAG(new) -> ordered preview (never overwrite with stale async)
  ├─ DRAG(last) -> authorized parameter commit -> Idle
  └─ context destruction -> drop capture, release borrowed resources
```

ユーザーが変更するAEパラメータと、UIだけのフォーカスを混同しない。Ctrl/Shift/Alt/ESCの解釈はhost配送が確認された範囲のみ。`PF_Event_KEYDOWN`は任意のキーアップ/IME/右クリック/ホイール/マルチタッチ配送を保証しない。完全なテキスト入力やアクセシビリティ/IMEが製品必須なら、このcustom ECW入口のみで満たせるかを別の実機試験で認定し、未達なら**標準AEパラメータやhost提供の別UI経路**を選択する。

当該UIの選択・hover・drag preview変更ではAEプロジェクトに書き込まない。正式値は`PF_Cmd_USER_CHANGED_PARAM`やSDKが許容するuser eventで`PF_ChangeFlag_CHANGED_VALUE`等を介して反映。VALUEとUI flagsの更新を同じcallbackで無制限に行わない。CLICK中change flagsのGuide内記載差は別途host testとする。

## Serialization / Undo / multiple instances

| State class | 例 | 所有 / 保存 | 不変条件 |
| --- | --- | --- | --- |
| Document semantic | lens vertex、Bezier keys、gradient stops | AE Parameter / Arb Data | host undo/redo/clone/save一致 |
| View/editor | scroll, selection, zoom, hovered widget | per-context UI model | Render IDに混入しない |
| Transient gesture | capture, start pose, mouse delta | current interaction | context closeで消滅 |
| Async request | purpose id, generation, receipt | host-managed async + local generation | stale resultをpublishしない |
| Cached render plan | geometry drawlist, tessellation | widget-owned immutable versioned CPU data | layout/data/theme revisionで失効 |
| Drawbot handle | pen/brush/path/font/image | DRAW callback scope | 不正再利用・double releaseなし |

Arbitrary Dataは特にNEW/DISPOSE/COPY/FLATTEN/UNFLATTEN/INTERP/COMPARE/SCAN/PRINTの対応が設計対象。可変長構造のdecodeでは長さ・個数・整数オーバーフロー・schema version・NaN/Inf・不明enumを検査。projectファイル由来データをtrusted in-memory pointerとして解釈しない。再入発生時にglobal singleton書込や再帰ロックでdeadlockしない。

## Renderer backend — Drawbotへの命令生成の最適化

`DRAW`はDrawbot専用。Render treeを直接host GPU surfaceに転送する権限と混同しない。以下は**導入順**であり、各優位性はH（実機でA/B/Aが必要）。

1. スタイルやlayout revision不変ならCPUでのgeometry/tessellationを再生成しない（**Drawbot PathRefのコールバック跨ぎキャッシュではない**）。
2. clip/dirty更新領域と交差しないwidgetのdraw-command generationを省略。ただしhostが部分surfaceを保持するかは確認し、不明ならfull redrawに戻す。
3. 同一styleのsolid rectanglesや連続pathを描画バッチ化。`PaintRect`候補と`NewPath`候補はcommand/AA/overdrawまで比較。
4. DRAW内の`NewBrush`/`NewPen`/`NewPath`/`NewDefaultFont`を必要最小回数にし、各`ReleaseObject`をRAIIで対応。借用refはReleaseObjectしない。
5. `SupportsText`でtextの有無を判定。文字レイアウトはサイズ/locale/theme/scaleをキーにCPU側cache可能だが、draw refやfont refの寿命には流用しない。
6. 複雑なグラフをオフスクリーンbitmap化する候補はpixel-layout preference、premultiplied alpha、rowbytes、DPI、upload/pixel copy、実メモリを含めて比較。`NewImageFromBuffer`自体のコストを無視しない。
7. Surface clip/AA/transform変更時はPush/Popを必ず対にし、`Flush`を高頻度で乱用しない。
8. 基準画質（pixel and interaction parity）が壊れる候補は速くても不採用。virtualizationで見えないwidgetは処理省略可能だが、キーボード/selection/scroll操作との意味一貫性を保証する。

## CPU計算量選択木

| 件数 / ワークロード | baseline | 高度化候補 | 実機採用条件 |
| --- | --- | --- | --- |
| 約10〜100 controls | Flat array + linear hit test | なしが通常 | O(N) profilingで十分 |
| 数百の可視要素 | Flattened display list、batch | tile/binning、dirty subtree | 生成+Drawbot p99改善 |
| 数千のスクロール要素 | indexed visible set | virtual list / spatial hash | focus/scroll/hit/clip parity |
| 数千の制御点・曲線 | tessellation caching + clip | BVH/R-tree / level-of-detail | boundary/snap精度一致 |
| 高負荷histogram/image preview | host async manager | downsample preview cache | stale/pending/receipt寿命試験 |

「Nが多い」だけでGPUへ逃がさない。CPUで10µsのmodelをGPUに移してもhost配送とDrawbotの更新が速くなる保証はない。

## Asynchronous content and stale-result rejection

ECW内のthumbnail/histogram/lens previewは、必要なら`PF_AsyncManagerP`のhost-managed requestを利用。purposeは意味的に安定させ、revisionの異なる結果は描画しない。`no receipt` / `receipt but no world` / `receipt and usable world`は別状態。render resultをUI threadで同期取得する一般設計は避ける。

```text
on_state_change:
    ++desired_generation
    invalidate_visual_bounds_when_context_is_valid

on_draw:
    snapshot = newest_immutable_snapshot()
    if cached_result.generation == snapshot.generation:
        paint(cached_result)
    else:
        request_host_async_for_semantic_purpose(snapshot)
        paint_placeholder_or_last_valid_appropriately_labeled()
    // no waiting for worker or render completion
```

これは実装可能な**設計パターン**であって、上記疑似コードをそのまま`PF_AsyncManagerP` APIとしてコンパイルできるものではない。host-specific receiptとcancel protocolは公式SDK/headerの実シグネチャに従う。

## Required verification before calling this a production framework

1. **Pure tests:** layout determinism、DPI transform inverse、hit order、clip、gesture transaction、cancel、dirty union、fuzz Arb decode、widget count 1/100/1000/10000。
2. **AE Windows host:** open/close、multiple ECWs/effect instances、scroll/twirl/resize/theme、多画面DPI、host Undo/redo/save/load、keyframe、UI render dependencies。
3. **AE Mac Intel/ARM:** all above + Retina/mixed screen/IME/text fallback + signing/loading。
4. **Load tests:** dense drawlist, static vs moving subtrees, frequent display scale change, rapid time scrubbing with async generation switches, memory pressure and AE MFR。
5. **Provenance:** every backend stored with compiler flags, plugin hash, AE build, display, CPU/GPU, test fixture and `validated-in-host` status. Windows portable-only passes are not AE renderer proofs。

## Sources and nearby chapters

- Adobe Effect UI & Events: https://ae-plugins.docsforadobe.dev/effect-ui-events/effect-ui-events/
- Adobe PF_EventUnion: https://ae-plugins.docsforadobe.dev/effect-ui-events/PF_EventUnion/
- Adobe Drawbot: https://ae-plugins.docsforadobe.dev/effect-ui-events/custom-ui-and-drawbot/
- Adobe PF_ParamDef: https://ae-plugins.docsforadobe.dev/effect-basics/PF_ParamDef/
- Adobe Parameter Supervision: https://ae-plugins.docsforadobe.dev/effect-details/parameter-supervision/
- Adobe Arbitrary Data: https://ae-plugins.docsforadobe.dev/effect-details/arbitrary-data-parameters/
- [Cross-platform release](cross-platform-compatibility.md)
- [Drawbot resources](../drawbot-ui-drawing.md)
- [Event routing](../effect-custom-ui-input-routing.md)
- [Invalidation](../effect-custom-ui-invalidation.md)
- [Host async previews](../async-custom-ui-rendering.md)
- [Adversarial qualification](performance-and-resilience.md)
