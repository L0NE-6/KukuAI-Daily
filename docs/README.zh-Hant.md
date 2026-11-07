# KukuAI Daily

**庫庫 AI 現行 `kukuai30` 每日簽到單檔腳本，支援多帳號、青龍與 GitHub Actions。**

[简体中文](../README.md) | [English](README.en.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Português (BR)](README.pt-BR.md)

## 概述

預設流程會先讀取會話身份，檢查簽到面板；尚未簽到時只發送一次 signin，等待後再次讀取面板。唯一成功判據是簽到後 `signed_today=true`。

舊 freepoint 任務僅在明確使用 `--legacy-freepoint` 時執行，預設流程不會自動切換到舊鏈路。

## 請求流程

```text
GET  /api/genflowpro/common/userreport?<client-query>
POST /act/v2/kukuai30/homepage?uid=<uk>&tid=291651792210&<client-query>
POST /act/v2/kukuai30/signin?uid=<uk>&tid=291651792210&<client-query>
POST /act/v2/kukuai30/homepage?uid=<uk>&tid=291651792210&<client-query>
```

`uk` 來自 `userreport.data.uk`。固定面板 `tid=291651792210`。已退役的 `getJsToken`、`activityTid`、`aid=15459` 與 `jsToken` 均不再使用。

## 憑據

```text
KUKU_COOKIES=BDUSS=...; PTOKEN=...; STOKEN=...; BAIDUID=...; PANPSC=...
```

多帳號建議使用 JSON 陣列：

```json
[
  {
    "name": "主號",
    "cookie": "BDUSS=...; PTOKEN=...; STOKEN=...; BAIDUID=...; PANPSC=...",
    "business_stoken": ""
  }
]
```

存在 `PTOKEN` 時，腳本會先換發 `genflowpro` 業務 STOKEN；換發失敗會明確終止。`KUKU_STOKEN` / `business_stoken` 僅供舊 freepoint 與 `--token` 使用。

## 成功判據

| 面板狀態 | 結果 |
| :--- | :--- |
| 簽到前已 `signed_today=true` | 中性完成，不重複提交 |
| 簽到後 `signed_today=true` | 本次簽到成功 |
| 簽到後仍為 `false` | 失敗，保留動作響應原因 |
| 動作回 `10152`，但復讀仍為 false | 失敗 |
| 動作回 `8001` | 如實顯示服務端拒絕原因 |
| 缺少 `uk`、`data` 或響應異常 | 失敗 |

HTTP 200、動作 `errno=0`、`errno=10152` 都不能單獨代表成功。

## 部署與驗證

```text
python kuku_daily.py
python -m unittest discover -s tests -v
python -m pytest -q
python -m py_compile kuku_daily.py kuku_get_cookie.py tests\_loader.py tests\test_kuku_contract.py
ruff check .
```

## 隱私與轉載

請勿公開完整 Cookie、STOKEN、`.kuku_stoken.json`、帳號導出檔或含憑據的截圖。官方倉庫與 Release 永久免費；禁止收費包裝、冒充作者，或使用作者身份與付款 QR 製造官方授權假象。詳見 [NOTICE.md](../NOTICE.md)。

## 版本

- 倉庫版本：`v1.4.0`
- 更新記錄：[CHANGELOG.md](../CHANGELOG.md)

本專案用於個人自動化，請遵守相關服務條款並自行承擔使用風險。
