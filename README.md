# Big Ambitions JP Localization Pack

Big Ambitions の複数 Mod を対象にした、日本語翻訳パックの雛形です。

## 構成

```text
Big-Ambitions-JP-Localization-Pack/
├── Makefile                      # 同期・ビルド・配布物作成
├── thumbnail.png                 # Steam Workshop プレビュー画像
├── Locales/
│   └── ja.json              # ゲームへ配布する生成物
├── Translations/
│   └── <mod>.json           # Mod ごとの翻訳元
├── src/
│   └── BigAmbitions.JpLocalizationPack/
│       ├── BigAmbitions.JpLocalizationPack.csproj
│       └── LocalizationPackMod.cs  # discovery 用の最小 Mod
├── build.py                     # 翻訳元の検証と結合
├── build_workshop.py            # Steam 説明文・VDF生成
├── sync_workshop.py             # Workshop の en.json を同期
├── workshop/
│   ├── metadata.json            # 説明・対応Mod一覧の定義
│   └── description.txt         # Steam向けの生成物
└── README.md
```

## 一括生成

Steam が取得済みの Workshop Mod から翻訳キーを同期し、`ja.json`、DLL、配布フォルダを一括生成します。

```sh
make
```

入力と出力は次の通りです。

```text
~/Library/Application Support/Steam/steamapps/workshop/content/1331550/*/Locales/en.json
    ↓
Translations/<mod-dll-name>.json
    ↓
Locales/ja.json
    ↓
dist/BigAmbitionsJapanesePack/
```

Mod に `Locales/ja.json` が同梱されていればその日本語を優先し、なければ初めて見つかったキーを英語の仮訳として追加します。`Translations/` で日本語へ書き換えた値は、その後 `make` を実行しても上書きされません。Workshop に存在しない Mod を購読・ダウンロードする処理は行わず、Steam が取得済みの Mod だけを対象にします。

別の Steam Library を使う場合はパスを上書きできます。

```sh
make WORKSHOP_DIR="/path/to/workshop/content/1331550" \
  MANAGED_DIR="/path/to/Big Ambitions_Data/Managed"
```

ファイルを変更せず、同期漏れ・生成漏れ・C# ビルドを確認するには次を実行します。

```sh
make check
```

Steam の説明文と対応 Mod 一覧は `workshop/metadata.json` で管理します。各 Mod の `translationFile` は `Translations/` と照合されるため、一覧の追加漏れも `make check` で検出できます。`make workshop` で `workshop/description.txt` を生成し、Release workflow が同じ定義からタイトル・説明文を公開します。

## 翻訳を追加する

1. `Translations/<mod-id>.json` を作成する。
2. Localization Key は小文字で記述する。
3. 次のコマンドで `Locales/ja.json` を生成する。Workshop との同期も同時に行われます。

```sh
make locales
```

生成物が最新か確認するだけなら、次を実行します。

```sh
make check
```

ビルド時に以下を検証します。

- 各ファイルのルートが JSON object であること
- Key と翻訳文が string であること
- Key が trim 済みの小文字であること
- パック内で Localization Key が重複していないこと

## DLL をビルドする

現行の Mod discovery は、Mod 直下に DLL がちょうど一つあるフォルダだけを候補にします。さらに DLL には、`RegisterModClass` で登録された `IModBigAmbitions` 実装と、認識可能な entry scope attribute が必要です。

この条件は 2026-09-12 時点の Steam build ID `25231854` に同梱された `BigAmbitions.ModsInternal.dll` で確認しています。[公式 Modding SDK](https://github.com/hovgaardgames/bigambitions) も Mod assembly を含む manifest と DLL のコンパイルを前提にしています。

この雛形には、翻訳のロード以外は何もしない最小 Mod class を含めています。ゲームの `Managed` ディレクトリを指定してビルドしてください。

macOS の標準的な Steam 配置例：

```sh
dotnet build src/BigAmbitions.JpLocalizationPack \
  -c Release \
  -p:BigAmbitionsManagedDir="$HOME/Library/Application Support/Steam/steamapps/common/Big Ambitions/Big Ambitions.app/Contents/Resources/Data/Managed"
```

ゲーム更新後は、現在の `BigAmbitions.ModAPI.dll` を参照して DLL を再ビルドしてください。ゲーム同梱 DLL はこのリポジトリへコピーしません。

## 配布

ビルドした DLL と `Locales/ja.json` を同じ Mod ルートへ配置します。ルートに複数の DLL を置くと discovery に失敗するため、DLL はこの Mod 本体だけにしてください。

```text
BigAmbitionsJapanesePack/
├── BigAmbitions.JpLocalizationPack.dll
├── thumbnail.png
└── Locales/
    └── ja.json
```

翻訳元の `Translations/`、`build.py`、PDB、`.deps.json` は開発用なので配布物には含めません。

Localization Key は全 Mod で共有され、同じキーはロード順が後の Mod に上書きされます。本体キーや他の翻訳 Mod のキーを意図せず上書きしないよう注意してください。元 Mod が未導入の場合、その Mod 向けのキーは参照されないだけです。

## Steam Workshop の自動更新

GitHub Release を公開すると、`.github/workflows/release.yml` がリリースに添付した
`BigAmbitions.JpLocalizationPack.dll`、リリース対象の `Locales/ja.json`、
`thumbnail.png` を
既存の Steam Workshop アイテムへアップロードします。ドラフトを保存しただけでは実行されません。

初回公開だけは Big Ambitions の `Mods > Mod Creator` から手動で行い、以下を
GitHub の `Settings > Secrets and variables > Actions` に登録してください。

| 種類 | 名前 | 値 |
| --- | --- | --- |
| Variable | `STEAM_WORKSHOP_ITEM_ID` | Workshop URL の `id` にある数字 |
| Secret | `STEAM_USERNAME` | Workshop アイテムを所有する Steam アカウント名 |
| Secret | `STEAM_PASSWORD` | Steam アカウントのパスワード |
| Secret | `STEAM_CONFIG_VDF` | SteamCMD で認証済みの `config.vdf` を Base64 化した値 |

macOS で `STEAM_CONFIG_VDF` 用の値をクリップボードへコピーする例です。

```sh
base64 < "$HOME/Library/Application Support/Steam/config/config.vdf" | tr -d '\n' | pbcopy
```

Release を公開する前に DLL をビルドし、Release asset のファイル名を
`BigAmbitions.JpLocalizationPack.dll` にしてください。DLL が添付されていない場合は、
壊れた配布物で Workshop を上書きせずにワークフローが失敗します。

ビルド済み DLL を添付して Release を作る例：

```sh
make
gh release create v0.1.0 \
  dist/BigAmbitionsJapanesePack/BigAmbitions.JpLocalizationPack.dll \
  --generate-notes
```

`config.vdf` とパスワードはログイン情報を含むため、リポジトリへコミットしないでください。
ワークフローはパスワードで毎回ログインし、`config.vdf` を Steam Guard の端末認証に使います。
Steam Guard の再承認を求められた場合は同じ Steam アカウントで SteamCMD に再ログインし、
`STEAM_CONFIG_VDF` を更新してください。ワークフローは `workshop/metadata.json` から
タイトル、説明、対応 Mod 一覧を生成し、配布ファイル、プレビュー画像、
Change Notes のリリースタグと一緒に更新します。
