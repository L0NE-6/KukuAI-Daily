# 🧩 KukuAI Daily

**庫庫 AI「庫庫 30 天簽到」單檔腳本，支援多帳號、青龍與 GitHub Actions。**

[简体中文](../README.md) | [English](README.en.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Português (BR)](README.pt-BR.md)

> 完整簡體中文文件請見 [../README.md](../README.md)。

## 概覽

KukuAI Daily 預設依序呼叫活動設定、活動首頁、JS 風控 Token 與簽到介面。舊 freepoint 任務只有在明確加上 `--legacy-freepoint` 時才會執行，不會自動回退。

只有回應同時滿足 `errno=0` 與布林值 `data.signed_today=true` 才算簽到成功。`errno=10152` 是今日已簽的中性狀態；`8001` / `8002` 是上游風控失敗。

## 預設請求流程

```text
GET  /act/api/conf?conf_key=kukuSignConf
GET  /act/v2/kukuai30/homepage?tid=<activityTid>
GET  /operation/activitys/api/getJsToken
POST /act/v2/kukuai30/signin?tid=<activityTid>&jsToken=<token>&aid=15459
```

所有請求固定使用：

```text
Referer: https://kuku.baidu.com/operation/activitys/kukuPcSignAct/main
```

## 兩種 STOKEN

| 名稱 | 來源 | 用途 |
| :--- | :--- | :--- |
| 網頁 STOKEN | 完整 Cookie 內的 `STOKEN` | 僅供 30 天簽到 |
| 業務 STOKEN | `KUKU_STOKEN`、多帳號 `business_stoken`、快取或換發結果 | 僅供 `--legacy-freepoint` |

`KUKU_STOKEN` 不會覆蓋網頁 `STOKEN`。Cookie 缺少網頁 `STOKEN` 時，預設流程會明確失敗並提示重新匯出完整 Cookie，不會改用業務 STOKEN。

## 單帳號

```text
KUKU_COOKIES=BDUSS=...; STOKEN=<網頁STOKEN>; PTOKEN=...; BAIDUID=...; PANPSC=...
```

舊 freepoint 可另外設定：

```text
KUKU_STOKEN=<業務STOKEN>
```

## 多帳號

建議使用 JSON 陣列。每個帳號的完整 Cookie 放在 `cookie`，業務 STOKEN 單獨放在 `business_stoken`：

```json
[
  {
    "name": "主號",
    "cookie": "BDUSS=...; STOKEN=<網頁STOKEN>; PTOKEN=...; BAIDUID=...; PANPSC=...",
    "business_stoken": ""
  },
  {
    "name": "副號",
    "cookie": "BDUSS=...; STOKEN=<網頁STOKEN>; PTOKEN=...; BAIDUID=...; PANPSC=...",
    "business_stoken": ""
  }
]
```

也支援逐行格式：

```text
主號|BDUSS=...; STOKEN=<網頁STOKEN>; PTOKEN=...; BAIDUID=...; PANPSC=...|業務STOKEN（可空）
副號|BDUSS=...; STOKEN=<網頁STOKEN>; PTOKEN=...; BAIDUID=...; PANPSC=...|業務STOKEN（可空）
```

舊格式 `備註|BDUSS|PTOKEN[|業務STOKEN]` 仍可解析，但不含網頁 STOKEN 與其它 Cookie，只適合 `--legacy-freepoint`。

## 青龍與 Actions

1. 上傳 `kuku_daily.py`；需要更新用戶端 Cookie 時一併上傳 `kuku_get_cookie.py`。
2. 單帳號設定 `KUKU_COOKIES`，多帳號設定 `KUKU_TOKENS`。
3. 建立 `task kuku_daily.py` 定時任務。

```cron
15 8 * * *
```

| Secret | 必填 | 說明 |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | 單帳號 | 完整網頁 Cookie，含網頁 STOKEN |
| `KUKU_TOKENS` | 多帳號 | JSON 陣列或逐行格式，優先於單帳號變數 |
| `KUKU_STOKEN` | 選填 | 僅單帳號舊 freepoint 使用的業務 STOKEN |
| `QYWX_TOKEN` | 選填 | 企業微信機器人 key |
| `PLUSPLUS_TOKEN` | 選填 | PushPlus token |

## 命令列

| 參數 | 作用 |
| :--- | :--- |
| 無 | 執行所有帳號的 30 天簽到 |
| `--only N` | 只執行第 N 個帳號 |
| `--legacy-freepoint` | 明確執行舊 freepoint，使用業務 STOKEN |
| `--token` | 只換發並輸出舊 freepoint 業務 STOKEN |
| `--version` | 輸出腳本版本 |

## 成功判據

| 上游結果 | 本地處理 |
| :--- | :--- |
| `errno=0`、`data.signed_today=true` | 簽到成功 |
| 首頁 `signed_today=true` | 中性完成，不再 POST |
| `errno=10152` | 中性完成，今日已簽 |
| `errno=8001` / `8002` | 風控失敗 |
| 缺少或非布林 `signed_today` | 失敗 |

## 驗證

```powershell
python -m unittest discover -s tests -v
python -m pytest -q
python -m py_compile kuku_daily.py kuku_get_cookie.py tests\_loader.py tests\test_kuku_contract.py
ruff check .
```

測試全部使用假回應，涵蓋四步主鏈、嚴格成功判據、雙 STOKEN 隔離、多帳號完整 Cookie、脫敏與通知。協議證據見 [PROTOCOL.md](PROTOCOL.md)。

## 隱私

日誌只顯示遮罩後的 BDUSS。請勿公開 `.kuku_stoken.json`、完整 Cookie、網頁／業務 STOKEN、多帳號匯出檔。

## 使用邊界

官方倉庫、腳本、部署說明與 Release 均免費公開。未經作者書面許可，請勿包裝為付費資源、收費部署或更新服務，請勿刪除署名、冒充作者或使用作者身分與收款碼製造背書。完整規則見 [NOTICE.md](../NOTICE.md)。

## 版本

- 倉庫版本：`v1.3.0`
- Release 狀態：由主執行緒統一發布
- 更新記錄：[CHANGELOG.md](../CHANGELOG.md)

## 免責聲明

本專案供個人學習與自動化使用。請遵守庫庫 AI、百度文庫與相關服務條款，並自行承擔使用風險。
