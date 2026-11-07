# KukuAI Daily

**Single-file runner for the current Kuku AI `kukuai30` daily check-in, with multi-account, Qinglong, and GitHub Actions support.**

[简体中文](../README.md) | [English](README.en.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Português (BR)](README.pt-BR.md)

## Overview

The default flow reads the session identity, checks the current panel, sends one sign-in action only when needed, then reads the panel again. The final `signed_today=true` readback is the only success criterion.

The legacy freepoint task family remains available only with an explicit `--legacy-freepoint` flag. The default flow never falls back to it.

## Request flow

```text
GET  /api/genflowpro/common/userreport?<client-query>
POST /act/v2/kukuai30/homepage?uid=<uk>&tid=291651792210&<client-query>
POST /act/v2/kukuai30/signin?uid=<uk>&tid=291651792210&<client-query>
POST /act/v2/kukuai30/homepage?uid=<uk>&tid=291651792210&<client-query>
```

`uk` comes from `userreport.data.uk`. The fixed panel id is `291651792210`. The retired `getJsToken`, `activityTid`, `aid=15459`, and `jsToken` parameters are not used.

## Credentials

Use the full Cookie from the same login session:

```text
KUKU_COOKIES=BDUSS=...; PTOKEN=...; STOKEN=...; BAIDUID=...; PANPSC=...
```

For multiple accounts:

```json
[
  {
    "name": "main",
    "cookie": "BDUSS=...; PTOKEN=...; STOKEN=...; BAIDUID=...; PANPSC=...",
    "business_stoken": ""
  }
]
```

When `PTOKEN` is present, the script exchanges it for a `genflowpro` business STOKEN. Exchange failure is reported explicitly. `KUKU_STOKEN` and `business_stoken` remain specific to the legacy freepoint and `--token` paths.

## Success rules

| Homepage state | Result |
| :--- | :--- |
| Already `signed_today=true` before sign-in | Neutral already-signed result; no action POST |
| `signed_today=true` after sign-in | Successful check-in |
| `signed_today=false` after sign-in | Failure; show the action response reason |
| Action returns `errno=10152` but readback stays false | Failure |
| Action returns `errno=8001` | Show the server rejection reason |
| Missing `uk`, `data`, or malformed response | Failure |

HTTP 200 and action `errno=0` are not enough. The post-action homepage readback is authoritative.

## Deployment

1. Upload `kuku_daily.py`; also upload `kuku_get_cookie.py` if you need to refresh client Cookies.
2. Configure `KUKU_COOKIES` or `KUKU_TOKENS`.
3. Schedule `python kuku_daily.py` in Qinglong or GitHub Actions.

```cron
15 8 * * *
```

## Verification

```powershell
python -m unittest discover -s tests -v
python -m pytest -q
python -m py_compile kuku_daily.py kuku_get_cookie.py tests\_loader.py tests\test_kuku_contract.py
ruff check .
```

Tests use fake responses only. See [PROTOCOL.md](PROTOCOL.md) for the field-level contract.

## Privacy and redistribution

Never publish full Cookies, STOKEN values, `.kuku_stoken.json`, account exports, or screenshots containing credentials. The official repository and Releases remain free. Do not sell, repackage, impersonate the author, or use the author's identity and payment QR codes to imply endorsement. See [NOTICE.md](../NOTICE.md).

## Version

- Repository version: `v1.4.0`
- Changelog: [CHANGELOG.md](../CHANGELOG.md)

This project is intended for personal automation. Follow the applicable service terms and use it at your own risk.
