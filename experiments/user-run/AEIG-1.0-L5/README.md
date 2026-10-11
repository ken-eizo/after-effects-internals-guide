# AEIG 1.0 Core L5 User-Run

このパッケージは、AEIG 1.0 の残る core gate を1回の disposable After Effects 26.3 セッションで観測するための canonical experiment です。ChatGPT 側は After Effects の起動・終了・クリック・レンダーを行いません。AE の実操作だけユーザーが行います。

## 取得する証拠

- `EXP-PLUGIN-001`: 48 suite family × selector 1..32 の PICA negotiation matrix
- `EXP-CACHE-002`: Canvas Receipt の effect-prefix completeness matrix
- `EXP-RG-001`: mutation 前後の BEE / TDB / MixHashGuid / RG / cache trace
- `EXP-SCRIPT-001`: ExtendScript runtime Reflection と scripting docs の比較
- 同一fixtureの pass A / B output、mutation log、環境情報

## Canonical probe

`plugin\AEGP\AEIGReceiptArtie.aex`

SHA-256: `DA8693DBD6B7CCC1BBF3043608D4FD7C93557D9CAF3F08A6B78D0BD5B6A1BB0F`

Adobe SDK 25.6 の Artie sample を基にした研究用 Artisan です。通常作業へ常設しないでください。

## 推奨実行手順

現在phaseだけ確認したい場合は、1つ上の `AEIG-L5-STATUS.cmd` を実行できます。STATUSはAEの起動・終了やprobe installを行わず、現在地だけを表示します。

1. 通常のAE作業を保存し、After Effects / AfterFX.com / aerender を自分で終了します。
2. 1つ上の `AEIG-L5-PREPARE.cmd` を実行します。safety preflight → 過去run archive → clean preflight → temporary probe install を順番に行います。
3. After Effects 26.3を自分で起動し、空の disposable project を使用します。
4. **File > Scripts > Run Script File...** から `01_RUN_IN_AE.jsx` を1回だけ実行します。
5. script完了後、After Effectsを自分で終了します。
6. 1つ上の `AEIG-L5-FINISH.cmd` を実行します。probe removal → verification/finalization → guarded promotion → repository/release audit まで自動実行します。

complete capture が予測を反証した場合、FINISH はpromotionを止めます。その観測は削除・自動再実行せず、model revision対象として保存します。

## Operator session identity

`AEIG-L5-PREPARE.cmd` はarchive後に一意な operator session ID を発行し、発行時刻、current Static RC fingerprint、canonical AEX SHA-256 とともに `datasets/aeig-l5-operator-session.env` へ保存します。JSX は実行開始時にこのmetadataを必須read-backし、environmentとfixture logへ同じsession情報を埋め込みます。

verificationではsession ID / RC fingerprint / AEX hashの一致、`current-pass.txt=DONE`、raw capture全体がsession発行後に作成されたことを確認します。別run由来のrawが1つでも混在した場合はmechanical capture incompleteとしてpromotionしません。`INSTALL_26_3.cmd` 自体もclean preflightを再実行し、copy後のAEXをcanonical binaryとbyte比較するため、wrapperを迂回した直接実行もfail-closedです。

## Fixture contract

Pass A / B は同じ 64×64 comp 内の中央32×32 3D solidと同じ3-effect topologyを使います。rendererは `AEIG Receipt Probe`、effectsは Gaussian Blur / Fill / Tint の3つです。Pass A は Blur=10、Pass B は Blur=75 とし、A完了後にlayer/effect handleを再取得してからmutationします。Blur値は設定後にpropertyからread-backしてlogへ記録します。32×32 sourceにすることでalpha edgeを残し、Blur 10→75の最終output差が観測可能なfixtureにしています。

Mechanical capture completeness は「予測が当たったか」と分離します。最低限、A/Bのrender完了、Blur read-back 10→75、script exit、3D fixture、AEIG renderer、3 effects、AE 26.3 build/OS environment、両output、48×32 suite attempt grid、Receipt attempt coverage、A/B trace block、主要Reflection object群が必要です。A/B output SHA差はmutationが実レンダーへ反映されたことを確認するsemantic gateです。

## Evidence interpretation

- Receipt API error、unexpected status、target trace category 0件は、capture自体が完全なら観測結果です。自動的に「再実行すべき失敗」へ変換しません。
- predictionが反証された場合は canonical prediction logへ反映し、該当domainをmodel revision gateで停止します。
- incomplete captureの場合は canonical prediction/domain/manifests のcommitを行わず、preview diagnosticだけを残します。complete captureのcanonical state更新はmulti-file transactionで行い、途中例外時はprediction/domain/manifestsをまとめてrollbackします。
- raw captureは編集・削除せず、再実行前にはtimestamp付き `prior-runs` へarchiveします。

## Trace safety

Artisanは各 `Artie_Render()` callback 全体をtrace windowとして囲み、dvacore master/category trace volumeとstderr captureを一時変更し、終了時に保存値へ戻します。別ファイル `artisan-stage.tsv` には Render→Camera→Scene→Receipt→Texture→Paint の到達段階だけを記録し、canonical trace schemaとは分離します。対象語彙は `BEE_Eval`, `BEE_Cache`, `BEE_CacheLog`, `BEE_WorkQueue`, `MixHashGuid`, `RenderNode.RG_CacheNodeBase`, `RenderNode.RG_XformNode`, `TDB_StreamBase`, `DiskCache` です。

## Acceptance and release

`AEIG-L5-FINISH.cmd` はtemporary probeを除去した後、Static RC再検証、diagnostic、capture verification、finalization、guarded promotion、repository integrity、release readinessを順番に実行します。AEIG 1.0 は27/27 domain target、locked prospective prediction解決、Static RC一致、final audits PASS、`VERSION=1.0` が揃うまで完成扱いにしません。
