# 🧩 KukuAI Daily

**Kuku AI（Baidu Wenku GenFlowPro）の毎日 LOGIN / CHAT 報酬を受け取る、マルチアカウント対応の Qinglong / GitHub Actions 自動化ツールです。**

[简体中文](../README.md) | [English](README.en.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Português (BR)](README.pt-BR.md)

> 完全な中国語ドキュメントは [../README.md](../README.md) にあります。

## 概要

KukuAI Daily は、Kuku AI の無料ポイント企画で毎日のログイン報酬と会話タスク報酬を取得します。成功時にはアカウントごとの実際の結果を出力します。当日分を取得済みの場合、API は `reward_point=0` を返すため、スクリプトは再実行を新しい報酬として扱わず、冪等な「本日取得済み」の結果として表示します。

業務 API では `genflowpro` スコープのセッショントークンが必要です。Web Cookie だけでは汎用のアカウント照会が通っても、アクティビティ API は未ログインと判定します。現在の `v1.2.0` は公式エンジンの MD5 署名を再現し、`BDUSS` と `PTOKEN` からトークンを交換します。`genflowengine.dll` を読み込まず、Windows、Linux、Docker、Qinglong で実行できます。

## 主な機能

- 毎日の `LOGIN` と `CHAT` タスクを取得します。
- API の冪等応答を正しく処理します。
- 単一アカウントは `KUKU_COOKIES`、複数アカウントは `KUKU_TOKENS` を使います。
- 設定済み STOKEN、ローカルキャッシュ、クロスプラットフォーム MD5 署名交換の順で認証情報を解決します。
- ログでは BDUSS をマスクして表示します。
- WeCom と PushPlus への任意通知に対応します。
- Python 標準ライブラリだけで動作します。

## 認証情報の準備

```bash
python kuku_get_cookie.py
python kuku_get_cookie.py --paste
python kuku_get_cookie.py --exchange
python kuku_get_cookie.py --paste --exchange
python kuku_daily.py --token
```

既定の `--exchange` はローカルデスクトップの Cookie データベースを読み取ります。`--paste --exchange` では `BDUSS` と `PTOKEN` を含む完全な Cookie を貼り付け、任意のプラットフォームで純署名交換を実行できます。`python kuku_daily.py --token` は設定済みアカウントのトークンを交換します。成功すると `KUKU_STOKEN=...` が表示されます。

## 最小構成の Qinglong

1. `kuku_daily.py` を Qinglong のスクリプトディレクトリへアップロードします。
2. 環境変数 `KUKU_COOKIES` と、交換済みの `KUKU_STOKEN` を設定します。
3. スクリプト一覧から定期タスクを作成し、コマンドを `task kuku_daily.py` にします。

```cron
15 8 * * *
```

```bash
task kuku_daily.py
```

複数アカウントでは `KUKU_TOKENS` を使用します。

```text
main|BDUSS_VALUE|PTOKEN_VALUE|STOKEN_VALUE
second|BDUSS_VALUE|PTOKEN_VALUE|STOKEN_VALUE
```

アカウント間は改行または `&` で区切ります。各項目の形式は `メモ|BDUSS|PTOKEN[|STOKEN]` です。

## 最小構成の GitHub Actions

**Settings → Secrets and variables → Actions** に次の Secrets を追加します。

| Secret | 必須 | 用途 |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | 単一アカウント | 単一アカウントの Cookie |
| `KUKU_STOKEN` | 任意 | Cookie と組み合わせるセッショントークン |
| `KUKU_TOKENS` | 複数アカウント | 複数アカウント設定。存在する場合は優先 |
| `QYWX_TOKEN` | 任意 | WeCom ボット key |
| `PLUSPLUS_TOKEN` | 任意 | PushPlus token |

同梱ワークフローは既定では手動実行のみです。最初に **Actions → KukuAI Daily → Run workflow** で検証します。定期実行を有効にする場合は、`.github/workflows/daily.yml` の `schedule:` 2 行をコメント解除します。

```yaml
schedule:
  - cron: '15 0 * * *'
```

`15 0 * * *` は UTC 表記で、北京時間の毎日 08:15 に相当します。Ubuntu runner でも純署名交換を実行できます。`KUKU_STOKEN` は省略可能で、`KUKU_COOKIES` から実行時に交換してキャッシュします。

## 主要な環境変数

| 変数 | 必須 | 説明 |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | 単一アカウント | Cookie ヘッダー、Cookie エディター JSON、または `BDUSS` / `PTOKEN` を含むオブジェクト |
| `KUKU_STOKEN` | 任意 | 交換済みの `genflowpro` セッショントークン |
| `KUKU_TOKENS` | 複数アカウント | `メモ\|BDUSS\|PTOKEN[\|STOKEN]` 形式の複数アカウント |
| `KUKU_PROXY` | 任意 | HTTP(S) または SOCKS5 プロキシ URL |
| `KUKU_NO_NOTIFY` | 任意 | `1` で通知を無効化 |
| `QYWX_TOKEN` | 任意 | WeCom ボット key。`WECHAT_WEBHOOK` も使用可 |
| `PLUSPLUS_TOKEN` | 任意 | PushPlus token |

## コマンドライン

| オプション | 動作 |
| :--- | :--- |
| なし | 設定済みの全アカウントで毎日タスクを実行 |
| `--only N` | N 番目のアカウントだけを実行 |
| `--token` | チェックインせず、セッショントークンの交換だけを実行 |

## 検証範囲

旧 README には、Cookie 解析、リクエストヘッダー、認証情報の優先順位、成功、冪等応答、セッション失効、HTTP 失敗、複数アカウント解析、ログマスクを含む 13 件のオフライン自己テストが記録されています。`v1.2.0` は DLL 呼び出しを純 MD5 署名交換へ置き換えました。新しい交換経路の実アカウントによるエンドツーエンドのオンラインログは含まれていないため、オンライン検収済みとは主張しません。

## プライバシー

Cookie、STOKEN、アカウント一覧は環境変数またはローカルキャッシュから読み取られます。ログに表示される BDUSS はマスク済みです。`.kuku_stoken.json`、環境変数の値、完全な Cookie をリポジトリ、Issue、Actions ログ、スクリーンショットへ公開しないでください。

## 利用範囲と再配布について

公式リポジトリ、スクリプト、デプロイ手順、Release は無料で公開されます。作者の明示的な書面許可なく、本プロジェクトを有料リソース、有料デプロイ、更新代行として販売または包装すること、著作者情報を削除して自作と主張すること、作者になりすますこと、作者の身元、名称、アイコン、支払い用 QR コードを使って公式承認があるように見せることを禁止します。無関係なアカウント、グループ、チャンネル、有料プラットフォームへ転載し、フォロワー増加、流入誘導、転売を図る行為も禁止します。違反時は削除要請の対象となり、作者は更新の停止、リポジトリのアーカイブまたは削除を行う場合があります。詳細は [NOTICE.md](../NOTICE.md) を確認してください。

## リンク

- [Releases](https://github.com/L0NE-6/KukuAI-Daily/releases)
- [Issues](https://github.com/L0NE-6/KukuAI-Daily/issues)
- [中国語 README](../README.md)
- [変更履歴](../CHANGELOG.md)

## 免責事項

本プロジェクトは個人の学習と自動化を目的としています。Kuku AI、Baidu Wenku および関連サービスの利用規約を確認し、自己責任で使用してください。
