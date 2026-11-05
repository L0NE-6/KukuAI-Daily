# 🧩 KukuAI Daily

**A single-file runner for the Kuku AI 30-day check-in, with multi-account, Qinglong, and GitHub Actions support.**

[简体中文](../README.md) | [English](README.en.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Português (BR)](README.pt-BR.md)

> Full Chinese documentation: [../README.md](../README.md)

## Overview

KukuAI Daily runs the Kuku AI 30-day activity by calling the configuration, activity homepage, JS token, and sign-in endpoints in order. The legacy free-points tasks are available only with an explicit `--legacy-freepoint` flag.

The default flow never falls back to the legacy API. A sign-in succeeds only when the response contains `errno=0` and a boolean `data.signed_today=true`. `errno=10152` is a neutral already-signed result; `8001` and `8002` are upstream risk-control failures.

## Request flow

```text
GET  /act/api/conf?conf_key=kukuSignConf
GET  /act/v2/kukuai30/homepage?tid=<activityTid>
GET  /operation/activitys/api/getJsToken
POST /act/v2/kukuai30/signin?tid=<activityTid>&jsToken=<token>&aid=15459
```

The Referer is fixed to:

```text
https://kuku.baidu.com/operation/activitys/kukuPcSignAct/main
```

## Two separate tokens

| Token | Source | Used by |
| :--- | :--- | :--- |
| Web STOKEN | `STOKEN` inside the full browser Cookie | The 30-day check-in only |
| Business STOKEN | `KUKU_STOKEN`, per-account `business_stoken`, cache, or exchange | The explicit legacy free-points flow only |

`KUKU_STOKEN` never overrides the web `STOKEN`. If the Cookie has no web `STOKEN`, the default flow fails with a request to export the full Cookie again. It does not silently use the business token.

## Single account

```text
KUKU_COOKIES=BDUSS=...; STOKEN=<web-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...
```

`KUKU_STOKEN` is optional and is read only by `--legacy-freepoint`:

```text
KUKU_STOKEN=<business-stoken>
```

## Multiple accounts

The recommended format is a JSON array. Each item stores the complete Cookie separately from the optional business token:

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

A line-oriented format is also accepted:

```text
main|BDUSS=...; STOKEN=<web-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...|optional-business-stoken
second|BDUSS=...; STOKEN=<web-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...|optional-business-stoken
```

The old positional format `name|BDUSS|PTOKEN[|business-stoken]` is still parsed for compatibility, but it does not contain a web STOKEN or the other browser fields. It is therefore suitable only for explicit `--legacy-freepoint`; the default 30-day flow reports the missing web STOKEN.

## Qinglong and GitHub Actions

1. Upload `kuku_daily.py`; upload `kuku_get_cookie.py` when you need to refresh client Cookies.
2. Set `KUKU_COOKIES` for one account or `KUKU_TOKENS` for multiple accounts.
3. Run `task kuku_daily.py` on a schedule.

```cron
15 8 * * *
```

For GitHub Actions, add:

| Secret | Required | Purpose |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | one account | Complete web Cookie including web `STOKEN` |
| `KUKU_TOKENS` | multiple accounts | JSON array or line format |
| `KUKU_STOKEN` | optional | Legacy business STOKEN for one-account mode only |
| `QYWX_TOKEN` | optional | WeCom bot key |
| `PLUSPLUS_TOKEN` | optional | PushPlus token |

## Command line

| Option | Effect |
| :--- | :--- |
| none | Run the 30-day check-in for every configured account |
| `--only N` | Run account N only |
| `--legacy-freepoint` | Run the legacy free-points tasks with a business token |
| `--token` | Exchange and print a legacy business token without checking in |
| `--version` | Print the script version |

## Success semantics

| Upstream result | Local result |
| :--- | :--- |
| `errno=0`, `data.signed_today=true` | Claimed successfully |
| Homepage `signed_today=true` | Neutral, already signed |
| `errno=10152` | Neutral, already signed |
| `errno=8001` / `8002` | Risk-control failure |
| Missing or non-boolean `signed_today` | Failure |

The process returns success when at least one account reaches a claimed or neutral state. If every account fails, it returns a non-zero exit code.

## Verification

```powershell
python -m unittest discover -s tests -v
python -m pytest -q
python -m py_compile kuku_daily.py kuku_get_cookie.py tests\_loader.py tests\test_kuku_contract.py
ruff check .
```

Tests use fake responses only. They cover the four-step flow, strict success checks, 10152, 8001/8002, explicit legacy mode, web/business STOKEN isolation, full multi-account Cookie fields, masking, and notifications. See [PROTOCOL.md](PROTOCOL.md).

## Privacy

Logs mask BDUSS values. Never publish `.kuku_stoken.json`, full Cookies, web/business STOKEN values, or account export files in a repository, Issue, Actions log, or screenshot.

## Usage and redistribution

The official repository, scripts, deployment instructions, and releases remain free. Without explicit written permission, do not package this project as a paid resource or paid deployment service, remove attribution, impersonate the author, or use the author's identity or payment QR codes to imply official endorsement. Violations may lead to takedown requests and the author may pause or archive the project. See [NOTICE.md](../NOTICE.md).

## Version

- Repository version: `v1.3.0`
- Release status: pending the main release process
- Changelog: [CHANGELOG.md](../CHANGELOG.md)

## Disclaimer

This project is intended for personal learning and automation. Follow the terms of Kuku AI, Baidu Wenku, and related services, and use it at your own risk.
