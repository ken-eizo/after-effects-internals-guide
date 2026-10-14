# After Effects ネイティブプロパティ拡張 — 型登録・親子構造・ホスト所有の技術体系

> 更新：2026-10-14。AE 2025 / 2026（Windows）実物バイナリと、AE 2026 実機検証に基づく。macOS の同等バイナリ・実機は未検証。**第三者による独自ネイティブ Stream 登録は未実現**。

## 目的と対象外

目的は、After Effects の**標準タイムライン UI**へ、エフェクトやレイヤーが持つ**未知の独自ネイティブ Property / Named Group / Indexed Group** を、Adobe 自身が持つ Stream と遜色なく直接追加すること。想定する用途は Paint の Stroke、Shape Contents、Text Animator のような編集可能な階層。

これは次のものとは異なる。

- CNL 独自 C++ エンジン内に存在する型やキーフレーム。Adobe 標準タイムラインには表示されない。
- `PF_ADD_TOPIC` や、標準 PF パラメータの折りたたみ UI。任意のネイティブ Stream クラスを新規登録するものではない。
- Pseudo Effect や Expression Controls。Adobe ネイティブ型として新たな任意クラスを登録するものではない。
- Paint Bucket や Brush Strokes。ここで調査する Paint は、**ブラシツール使用時に自動生成される Paint エフェクト**。
- シェイプレイヤー、マスク、エフェクト等の既存 Layer を偽装・借用した「新規 Layer」。

## ネイティブ階層を成立させる独立したゲート

| Gate | 必要条件 | 確定している実装・観測 | 第三者 AEX での結果 |
| --- | --- | --- | --- |
| 0 | ホストがプラグインの native Stream/Layer Provider をロードして認識 | BEE の内部 `Birth` 経路から各組込み Layer family が登録 | **提供された公開 SDK では provider API 未確認** |
| 1 | MatchName と C++ Stream creator を TDB に登録 | `TDB_ScRegisterStreams::Register` → `TDB_StreamFactory::RegisterFactoryFunc`、PaintAtom の実登録を機械語で確認 | **外部 creator 未実証** |
| 2 | **親グループが新規 MatchName を受け入れる** | `FillInCanonicalUILayout` → `GetCanonicalStream` → `SetupCanonicalLayout` → `CanStore` | **既存 Paint への `CNL:PaintAtom` 追加拒否を実機確認** |
| 3 | Native Stream を実体として生成し AE が所有 | 既存 `ADBE Paint Atom` は生成済み・AEGP で取得可能 | 外部新型未実証 |
| 4 | AE タイムライン UI が表示・選択・編集する | 既存 Paint/Animator は AE UI に表示。既存 Paint の全35 Stream を AEGP で取得済み | 外部新型未実証 |
| 5 | AE ネイティブのキーフレーム・エクスプレッション | 公開 SDK に `AEGP_GetStreamType`, `AEGP_GetStreamNumKFs` 等 | 既存 Paint 取得プローブ v2 はビルド済・未実機検証 |
| 6 | AEP ファイル保存・再読み込み | 既存の `BEE_PaintAtom::Read/Write` を追跡可能 | 外部新型未実証 |
| 7 | レンダラー、独自ツール・ギズモ、Undo、stable IDs | Adobe BEE のネイティブ Shape/Paint 基盤に存在する | 外部新型未実証 |
| 8 | 安全なロード/アンロードと複数バージョン・OS の ABI 整合性 | Windows 2025/26 で private C++ ABI や RVA が異なる | 公開される互換 ABI なし。macOS 未実機検証 |

この表の PASS は「内蔵 Adobe 型について存在を確認」の意味であり、「第三者の独自ネイティブ型で動作」ではない。

### Gate 1 — 登録される型

```text
BEE_AVLayer::RegisterStreams
 └─ TDB_ScRegisterStreams::Register(match_name, std::function<creator>, bool)
      └─ TDB_StreamFactory::RegisterFactoryFunc
           ├─ CreateStream（標準インスタンスの構築経路）
           └─ RegisterSeparatedDimensions
```

Paint の `BEE_PaintAtom::Create` や Text の Animator/Selector class creator は、実際に Adobe の登録関数に渡される。これは **Adobe 内部の C++ ABI** であり、`TDB_ScRegisterStreams::Register` がエクスポートされていても第三者向け公開 SDK とみなしてはならない。

### Gate 2 — 親が受け入れるクラス

```text
BEE_StrokesGroupBase::FillInCanonicalUILayout
 └─ GetCanonicalStream(ADBE Paint Atom) → 親の標準レイアウト

TDB_StreamGroup::SetupCanonicalLayout
 ├─ virtual FillInCanonicalUILayout（vtable slot #57）
 └─ SetUILayout

TDB_StreamGroup::CanStore（vtable slot #56）
 └─ 親側の許容 MatchName と照合
```

BEE Paint、Text Animator、Text Selectors、Text Animator Properties の各グループの vtable では、**共通 TDB CanStore** + **型固有 FillInCanonicalUILayout** の組合せを機械語で確認（Windows 2025/26）。

AE2026 実機での具体例：

```text
Parent: ADBE Paint Group (INDEXED)
AEGP_CanAddStream("ADBE Paint Atom")                → TRUE
AEGP_CanAddStream("CNL:PaintAtom")                  → FALSE
AEGP_CanAddStream("ADBE Paint Atom - CNLProbe")     → FALSE
```

したがって、**creator の登録さえすれば既存の Paint / Text に自由な子を追加できる**という予想は成立しない。第三者の独自型用の親グループを定義するか、Adobe が外部クラスを許容する正規手段が必要。

Shape Contents は別規則を持ち、未知の `ADBE Vector Shape - ...` 名に `CanAddStream=TRUE` を返す例がある。しかし、それは factory が生成可能という意味ではない。

### 実際の公開 SDK で確認できること

`E:\ae25.6_61.64bit.AfterEffectsSDK\Examples\AEGP\Streamie\Streamie.cpp` は、既存の `ADBE Paint Group` の Stroke を列挙し、並び替え・複製・名前変更・削除する Adobe 純正の AEGP サンプルである。

このサンプルは**既存の Adobe ネイティブ型に対する操作**であり、任意新型の TDB registrar ではない。

### 現在の CNL / ChapeLayer の位置

- 独立した C++ typed Timeline engine と vector/undo/archive は実装・ビルド済。**AE 標準タイムラインではなく CNL 独立実装**。
- Paint の実体は `Required\Paint.aex`。内部 `Paint Suite` を通じて `AfterFXLib.dll!PaintEffectEntryPoint` と接続され、組込み BEE/TDB Stream 登録を使用する。
- AE2026 実機で Paint 35 Stream をエラー 0 で読み取り、親子型受入を6件測定済。これは第三者 AEX の**既存型へのアクセス**を示す。
- 最新 CNL inspector v2 は既存 Paint リーフの AE 型・時間可変・キーフレーム数を追加取得するよう C++ 実装・Windows Release ビルド済。ただし **v2 実機未実行**。

### 安全な研究・製品化の判定

最初に必要なのは、第三者 AEX が独自 native Stream class creator と canonical parent layout を**サポート対象 API**として登録できる経路の証明である。未公開 ABI をアプリ本体へ注入、DLL 書換、アドレス直打ち、private `Register` のライブ呼出しで「動いた」だけでは製品化の達成とみなさない。

外部 registrar が見つからなければ、Adobe SDK チームに、次の2要件を分離して照会する：

1. Effect 内の**未知の独自 TDB Stream class**を登録して標準 Timeline に表示するためのサポート API はあるか。
2. Indexed/Named Group の **canonical allowable children** と C++ factory を第三者が定義する正規インターフェースはあるか。

独自ネイティブ Layer クラスを目指す場合は別途 `BEE_Layer` の作成型と Comp 所有・アーカイブ・描画の Gate が追加される。Paint の調査だけで Layer の新規登録が可能になったわけではない。

## 一次実証資料

- `research/findings/F-VECTOR-080-adobe-paint-aex-native-tdb-registration.md` — Paint creator の実際の TDB 登録
- `research/findings/F-VECTOR-081-paint-suite-host-owned-effect-bridge.md` — Paint AEX と host Paint Suite
- `research/findings/F-VECTOR-082-sdk-streamie-and-readonly-paint-inspector.md` — 公開 SDK と AEGP inspector
- `research/findings/F-VECTOR-083-paint-inhost-native-stream-hierarchy-admission.md` — **AE2026 実機 Paint 35 Stream + CanAdd 実測**
- `research/findings/F-VECTOR-084-tdb-native-two-gate-paint-text-canonical-policy.md` — Paint / Text canonical grammar
- `research/findings/F-VECTOR-085-paint-native-leaf-keyframe-metadata-probe.md` — v2 Inspector の未実機ビルド

- `research/findings/F-VECTOR-086-automatic-bee-canonical-property-grammar-census.md` — Paint/Text/Shape/Layer の FillInCanonicalUILayout を一括抽出（AE2025 102定義/515参照、AE2026 104定義/527参照。エクスポート名に基づく部分抽出）。

## 2026-10-14 実機 v2 検証・公開 SDK 範囲監査の追加

- F-VECTOR-087: AE2026 の実際の Paint v2 調査で Brush 6本 / native Stream 170 / leaf metadata 142 / `canVaryOverTime=TRUE` 109件 / エラー0件。Paint Path は `AEGP_StreamType_NO_DATA`（独自の内部値型を持つため通常の公開 Stream 値 API に出ない）。これは外部型登録成功を意味しない。
- F-VECTOR-088: インストール済み SDK25.6 の公開ヘッダー70ファイルを検査。`AEGP_RegisterSuite5` 12機能・`AEGP_DynamicStreamSuite4` 26機能を列挙したが、任意の C++ ネイティブ Stream クラス/親 UILayout を登録する公開インターフェースを確認できず。SDK26.5公開更新履歴も外部 Stream 型 Provider は明記していない。
- 完成判定: `datasets/chape_host_native_timeline_product_gate_20261014.json` は **`NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM`**。CNL自作アニメーションエンジンのテストと外部 AEX の Paint 調査は合格だが、Adobe本体所有の独自型は未実現。
- Adobe SDKチームへの正規問い合わせ草案: `docs/vector-shape-system/adobe-native-property-provider-sdk-inquiry.md`。未送信。公開されていない内部 ABI を製品ホストで無断実行して成功扱いにしない。

## F-VECTOR-089 / 090 — AE純正 AEX 横断監査と危険な private registrar の分離（2026-10-14）

- AE2025の481件／AE2026の633件のインストール済み AEX を静的に検査。BEE.dll や TDB.dll を直接利用する Adobe AEX が存在する一方、指定した `TDB_StreamFactory::RegisterFactoryFunc`／`TDB_ScRegisterStreams::Register` の直接インポートは **0件**（動的解決・Suite・delay-import は調査外）。ユーザーの第三者プラグイン名は公開データセットに含めていない。
- `CNLPrivateTDBDisposable.aex` の Release ビルドと静的安全ゲート監査は PASS（SHA256 `c91ffce77be481a394c243c0de64568487d3f24e5864cbba9376eaf1500b5622`）。**非公開 TDB レジストリへの実機書込は未実行。Adobe 本番環境への導入は禁止**。あくまで、明示的な危険性同意を得た使い捨て隔離 AE 環境の候補実験。
- 上記の結果は、独自の AE ネイティブ Stream/Group 型が完成したことを意味しない。製品判定は引き続き `NOT_DELIVERED_HOST_NATIVE_CUSTOM_STREAM`。
- 一次資料は `research/findings/F-VECTOR-089-aex-import-survey-registered-native-stream-owner-gap.md` と `research/findings/F-VECTOR-090-disposable-private-tdb-registrar-not-host-certified.md`。

## EXP-SHAPE-091 — Windows VM 限定の危険な private TDB 登録試験（2026-10-14）

ユーザーはクラッシュの危険性を承知したうえで**使い捨ての隔離 Windows VM**内での実験を明示的に許可。ただしローカル環境は Windows 10 Home（Microsoft Windows Sandbox 非対応）、VirtualBox 5.2.20 に Linux boot2docker VM しか存在せず、AE を独立して起動できる Windows VM はない。このため、**ユーザー許可を尊重しつつ、物理 PC の AE に非公開の登録実験を流し込むことはしていない**。

研究用パッケージをローカル `D:\Developer\ShapeLayerAE\results\CNLPrivateTDB_VM_ONLY_20261014.zip` に作成（SHA256 `B881BC258B0CC19DB694B2FEA056C86C07AC27744AD10D85B47D3F9EA6789D2A`）。VM ゲスト識別、仮想ディスク、ネットワーク遮断、ホスト共有の解除、独立したゲスト側 AE インストール、空・未保存プロジェクト、スナップショット確認、実験 AEX の完全な SHA を必須にする。

物理ホストでの読み取り専用チェックは **REFUSED exit 20**、手動起動スクリプトも **AEX をインストールする前に REFUSED**。実験用 AEX は通常の AE に未導入。**非公開の登録関数は未実行で、ネイティブ独自型の登録・表示は未完成**。

証拠：`research/findings/F-VECTOR-091-vm-only-private-tdb-registration-test-kit-and-host-refusal.md`。次の必須条件は、スナップショット付き Windows VM と、VM 内だけの AE 2026 独立インストールの確保。
