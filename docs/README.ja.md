# 🧩 KukuAI Daily

**Kuku AI「30 日チェックイン」を実行する単一ファイルスクリプト。複数アカウント、Qinglong、GitHub Actions に対応します。**

[简体中文](../README.md) | [English](README.en.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Português (BR)](README.pt-BR.md)

> 完全な中国語ドキュメントは [../README.md](../README.md) にあります。

## 概要

KukuAI Daily は、設定取得、活動ホーム、JS トークン取得、サインインの順に API を呼び出します。旧 freepoint タスクは `--legacy-freepoint` を明示した場合だけ実行され、自動フォールバックは行いません。

`errno=0` かつブール値の `data.signed_today=true` が返った場合だけ成功です。`errno=10152` は本日チェックイン済みの中性状態、`8001` / `8002` は上流のリスク制御失敗です。

## リクエストフロー

```text
GET  /act/api/conf?conf_key=kukuSignConf
GET  /act/v2/kukuai30/homepage?tid=<activityTid>
GET  /operation/activitys/api/getJsToken
POST /act/v2/kukuai30/signin?tid=<activityTid>&jsToken=<token>&aid=15459
```

Referer は常に次を使用します。

```text
https://kuku.baidu.com/operation/activitys/kukuPcSignAct/main
```

## 2 種類の STOKEN

| 種類 | 取得元 | 用途 |
| :--- | :--- | :--- |
| Web STOKEN | 完全な Cookie 内の `STOKEN` | 30 日チェックイン専用 |
| Business STOKEN | `KUKU_STOKEN`、複数アカウントの `business_stoken`、キャッシュ、交換結果 | `--legacy-freepoint` 専用 |

`KUKU_STOKEN` が Cookie 内の Web STOKEN を上書きすることはありません。Web STOKEN が欠けている場合、既定フローは完全な Cookie の再エクスポートを求めて失敗し、Business STOKEN へ切り替えません。

## 単一アカウント

```text
KUKU_COOKIES=BDUSS=...; STOKEN=<web-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...
```

旧 freepoint 用の Business STOKEN は別に設定します。

```text
KUKU_STOKEN=<business-stoken>
```

## 複数アカウント

JSON 配列を推奨します。完全な Cookie は `cookie`、旧 freepoint 用トークンは `business_stoken` に分けます。

```json
[
  {
    "name": "main",
    "cookie": "BDUSS=...; STOKEN=<web-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...",
    "business_stoken": ""
  },
  {
    "name": "second",
    "cookie": "BDUSS=...; STOKEN=<web-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...",
    "business_stoken": ""
  }
]
```

行形式も使用できます。

```text
main|BDUSS=...; STOKEN=<web-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...|optional-business-stoken
second|BDUSS=...; STOKEN=<web-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...|optional-business-stoken
```

旧形式 `name|BDUSS|PTOKEN[|business-stoken]` は互換解析のみです。Web STOKEN を含まないため、既定の 30 日フローでは失敗し、`--legacy-freepoint` 専用になります。

## Qinglong / GitHub Actions

1. `kuku_daily.py` をアップロードします。Cookie 更新が必要な場合は `kuku_get_cookie.py` も配置します。
2. 単一アカウントは `KUKU_COOKIES`、複数アカウントは `KUKU_TOKENS` を設定します。
3. `task kuku_daily.py` を定期実行します。

```cron
15 8 * * *
```

| Secret | 必須 | 用途 |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | 単一アカウント | Web STOKEN を含む完全な Cookie |
| `KUKU_TOKENS` | 複数アカウント | JSON 配列または行形式 |
| `KUKU_STOKEN` | 任意 | 単一アカウントの旧 freepoint 専用 Business STOKEN |
| `QYWX_TOKEN` | 任意 | WeCom ボット key |
| `PLUSPLUS_TOKEN` | 任意 | PushPlus token |

## コマンドライン

| オプション | 動作 |
| :--- | :--- |
| なし | 全アカウントの 30 日チェックイン |
| `--only N` | N 番目のアカウントだけ実行 |
| `--legacy-freepoint` | Business STOKEN を使う旧 freepoint を明示実行 |
| `--token` | 旧 freepoint の Business STOKEN を交換して表示 |
| `--version` | スクリプトのバージョンを表示 |

## 成功判定

| 上流結果 | ローカル処理 |
| :--- | :--- |
| `errno=0`、`data.signed_today=true` | 成功 |
| ホームの `signed_today=true` | 中性完了、POST しない |
| `errno=10152` | 中性完了、本日チェックイン済み |
| `errno=8001` / `8002` | リスク制御失敗 |
| `signed_today` 欠落または非ブール値 | 失敗 |

## 検証

```powershell
python -m unittest discover -s tests -v
python -m pytest -q
python -m py_compile kuku_daily.py kuku_get_cookie.py tests\_loader.py tests\test_kuku_contract.py
ruff check .
```

すべて偽レスポンスを使用します。4 段階フロー、厳格成功判定、10152、8001/8002、明示的レガシー、Web/Business STOKEN 分離、複数アカウントの完全 Cookie、マスク、通知を検証します。詳細は [PROTOCOL.md](PROTOCOL.md) を参照してください。

## プライバシー

ログでは BDUSS をマスクします。`.kuku_stoken.json`、完全な Cookie、STOKEN、アカウント出力を公開しないでください。

## 利用範囲

公式リポジトリ、スクリプト、手順、Release は無料です。作者の書面許可なく有料販売、有料デプロイ、更新代行、作者なりすまし、收款 QR による公式承認の偽装を行わないでください。詳細は [NOTICE.md](../NOTICE.md) を確認してください。

## バージョン

- リポジトリ版：`v1.3.0`
- Release：メインスレッドで統一公開
- 更新履歴：[CHANGELOG.md](../CHANGELOG.md)

## 免責事項

本プロジェクトは個人の学習と自動化を目的としています。Kuku AI、Baidu Wenku および関連サービスの利用規約を確認し、自己責任で使用してください。
