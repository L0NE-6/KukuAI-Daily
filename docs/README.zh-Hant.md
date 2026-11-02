# 🧩 KukuAI Daily

**庫庫 AI（百度文庫 GenFlowPro）每日登入與對話獎勵領取工具，支援多帳號、青龍與 GitHub Actions。**

[简体中文](../README.md) | [English](README.en.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Português (BR)](README.pt-BR.md)

> 完整中文文件請見 [../README.md](../README.md)。

## 概覽

KukuAI Daily 會領取庫庫 AI「免費領積分」活動中的每日登入與完成一次對話獎勵。成功執行時會輸出每個帳號的實際獎勵結果；若當天已領取，活動介面會回傳 `reward_point=0`，腳本會按冪等結果顯示「今日已領」，不把重複執行誤報成新增積分。

業務介面需要作用域為 `genflowpro` 的會話權杖。只帶網頁 Cookie 時，通用帳號查詢可能正常，但活動介面仍會判定未登入。目前 `v1.2.0` 已復刻官方引擎的 MD5 簽名，使用 `BDUSS` + `PTOKEN` 換發，不需要載入 `genflowengine.dll`；Windows、Linux、Docker 與青龍都能執行。

## 核心能力

- 領取每日 `LOGIN` 與 `CHAT` 任務。
- 正確處理活動介面的冪等回執。
- 單帳號使用 `KUKU_COOKIES`，多帳號使用 `KUKU_TOKENS`。
- 依序嘗試已設定的 STOKEN、本機快取、跨平台 MD5 簽名換發。
- 日誌只顯示遮罩後的 BDUSS 片段。
- 可選企業微信與 PushPlus 推送。
- 僅使用 Python 標準函式庫。

## 準備憑據

```bash
python kuku_get_cookie.py
python kuku_get_cookie.py --paste
python kuku_get_cookie.py --exchange
python kuku_get_cookie.py --paste --exchange
python kuku_daily.py --token
```

預設 `--exchange` 會先讀取本機桌面端 Cookie 資料庫。使用 `--paste --exchange` 時，可手動貼上含 `BDUSS` 與 `PTOKEN` 的完整 Cookie，再於任意平台完成純簽名換發。`python kuku_daily.py --token` 會為已設定帳號直接換發。工具會輸出 `KUKU_STOKEN=...`。

## 最短青龍設定

1. 將 `kuku_daily.py` 上傳到青龍腳本目錄。
2. 新增環境變數 `KUKU_COOKIES` 與換發得到的 `KUKU_STOKEN`。
3. 從腳本清單建立定時任務，讓命令成為 `task kuku_daily.py`。

```cron
15 8 * * *
```

```bash
task kuku_daily.py
```

多帳號請改用 `KUKU_TOKENS`：

```text
主號|BDUSS_VALUE|PTOKEN_VALUE|STOKEN_VALUE
副號|BDUSS_VALUE|PTOKEN_VALUE|STOKEN_VALUE
```

帳號之間可用換行或 `&` 分隔，每條格式為 `備註|BDUSS|PTOKEN[|STOKEN]`。

## 最短 GitHub Actions 設定

在 **Settings → Secrets and variables → Actions** 新增：

| Secret | 必填 | 用途 |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | 單帳號 | 單帳號 Cookie |
| `KUKU_STOKEN` | 否 | 與 Cookie 配套的會話權杖 |
| `KUKU_TOKENS` | 多帳號 | 多帳號資料，設定後優先使用 |
| `QYWX_TOKEN` | 否 | 企業微信機器人 key |
| `PLUSPLUS_TOKEN` | 否 | PushPlus token |

內建工作流程預設只能手動觸發。先到 **Actions → KukuAI Daily → Run workflow** 驗證。需要定時執行時，取消 `.github/workflows/daily.yml` 裡兩行 `schedule:` 註解：

```yaml
schedule:
  - cron: '15 0 * * *'
```

`15 0 * * *` 使用 UTC，等於北京時間每天 08:15。Actions 的 Ubuntu runner 可以執行純簽名換發；`KUKU_STOKEN` 可省略，由 `KUKU_COOKIES` 在執行時換發並快取。

## 關鍵環境變數

| 變數 | 必填 | 說明 |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | 單帳號 | Cookie 標頭、Cookie 編輯器 JSON，或含 `BDUSS` / `PTOKEN` 的物件 |
| `KUKU_STOKEN` | 否 | 已換發的 `genflowpro` 會話權杖 |
| `KUKU_TOKENS` | 多帳號 | 多帳號，格式 `備註\|BDUSS\|PTOKEN[\|STOKEN]` |
| `KUKU_PROXY` | 否 | HTTP(S) 或 SOCKS5 代理網址 |
| `KUKU_NO_NOTIFY` | 否 | 設為 `1` 時關閉推送 |
| `QYWX_TOKEN` | 否 | 企業微信機器人 key，也相容 `WECHAT_WEBHOOK` |
| `PLUSPLUS_TOKEN` | 否 | PushPlus token |

## 命令列參數

| 參數 | 作用 |
| :--- | :--- |
| 無 | 執行所有已設定帳號的每日任務 |
| `--only N` | 只執行第 N 個帳號 |
| `--token` | 只換發並輸出會話權杖，不執行簽到 |

## 驗證範圍

舊版 README 記錄了 13 項離線自測，涵蓋 Cookie 解析、請求標頭、權杖優先順序、成功、冪等、會話失效、HTTP 失敗、多帳號解析與日誌脫敏。`v1.2.0` 已把 DLL 呼叫替換為純 MD5 簽名換發；倉庫沒有附上新換發路徑的真實帳號端到端線上日誌，因此不宣稱已完成線上驗收。

## 隱私提醒

Cookie、STOKEN 與帳號清單只從環境變數或本機權杖快取讀取，日誌只顯示遮罩後的 BDUSS 片段。請勿在倉庫、Issue、Actions 日誌或截圖中公開 `.kuku_stoken.json`、環境變數值或完整 Cookie。

## 連結

- [Releases](https://github.com/L0NE-6/KukuAI-Daily/releases)
- [Issues](https://github.com/L0NE-6/KukuAI-Daily/issues)
- [簡體中文完整文件](../README.md)
- [更新記錄](../CHANGELOG.md)

## 免責聲明

本專案供個人學習與自動化使用。請遵守庫庫 AI、百度文庫與相關服務條款，並自行承擔使用風險。
