# KukuAI Daily

**Kuku AI の現行 `kukuai30` デイリーチェックインを実行する単一ファイルスクリプトです。複数アカウント、Qinglong、GitHub Actions に対応します。**

[简体中文](../README.md) | [English](README.en.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Português (BR)](README.pt-BR.md)

## 概要

既定フローはセッション身份を取得し、签到パネルを確認します。未签到の場合だけ signin を 1 回送信し、待機後にパネルを再読取します。唯一の成功条件は、签到後パネルの `signed_today=true` です。

旧 freepoint 処理は明示的な `--legacy-freepoint` 指定時だけ実行され、既定フローが自動で旧 API に切り替わることはありません。

## リクエストフロー

```text
GET  /api/genflowpro/common/userreport?<client-query>
POST /act/v2/kukuai30/homepage?uid=<uk>&tid=291651792210&<client-query>
POST /act/v2/kukuai30/signin?uid=<uk>&tid=291651792210&<client-query>
POST /act/v2/kukuai30/homepage?uid=<uk>&tid=291651792210&<client-query>
```

`uk` は `userreport.data.uk` から取得します。固定パネルは `tid=291651792210` です。退役した `getJsToken`、`activityTid`、`aid=15459`、`jsToken` は使用しません。

## 認証情報

```text
KUKU_COOKIES=BDUSS=...; PTOKEN=...; STOKEN=...; BAIDUID=...; PANPSC=...
```

複数アカウントでは JSON 配列を推奨します。

```json
[
  {
    "name": "main",
    "cookie": "BDUSS=...; PTOKEN=...; STOKEN=...; BAIDUID=...; PANPSC=...",
    "business_stoken": ""
  }
]
```

`PTOKEN` がある場合、`genflowpro` の業務 STOKEN を交換します。交換失敗は明示エラーになります。`KUKU_STOKEN` / `business_stoken` は旧 freepoint と `--token` 専用です。

## 成功判定

| パネル状態 | 結果 |
| :--- | :--- |
| 签到前から `signed_today=true` | 中性完了。signin を送信しない |
| 签到後 `signed_today=true` | 今回の签到成功 |
| 签到後も `false` | 失敗。action のエラー理由を表示 |
| action が `10152` でも再読取が false | 失敗 |
| action が `8001` | サーバーの拒否理由をそのまま表示 |
| `uk`、`data`、レスポンス形式が不正 | 失敗 |

HTTP 200、action の `errno=0`、`errno=10152` だけでは成功になりません。

## 実行と検証

```text
python kuku_daily.py
python -m unittest discover -s tests -v
python -m pytest -q
python -m py_compile kuku_daily.py kuku_get_cookie.py tests\_loader.py tests\test_kuku_contract.py
ruff check .
```

## プライバシーと再配布

完全な Cookie、STOKEN、`.kuku_stoken.json`、アカウント出力、認証情報を含むスクリーンショットを公開しないでください。公式リポジトリと Release は無料です。有料包装、作者のなりすまし、作者名や支払い QR による公式認証の誤認を禁止します。詳細は [NOTICE.md](../NOTICE.md) を参照してください。

## バージョン

- リポジトリ版：`v1.4.0`
- 変更履歴：[CHANGELOG.md](../CHANGELOG.md)

本プロジェクトは個人自動化向けです。関連サービスの規約を確認し、自己責任で使用してください。
