# 🧩 KukuAI Daily

**Daily LOGIN and CHAT reward collection for Kuku AI (Baidu Wenku GenFlowPro), with multi-account, Qinglong, and GitHub Actions support.**

[简体中文](../README.md) | [English](README.en.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Português (BR)](README.pt-BR.md)

> Complete Chinese documentation: [../README.md](../README.md)

## Overview

KukuAI Daily signs in to the Kuku AI free-points activity and completes the daily conversation task through the service APIs. A successful run returns the reward result for each account. If the daily reward was already collected, the activity API returns `reward_point=0`; the script reports that as an idempotent "already collected" state instead of claiming new points.

The business API expects a `genflowpro` session token. A web Cookie alone may still allow generic account queries, but the activity endpoints require the issued session token. The current `v1.2.0` implementation reproduces the official engine's MD5 signature and exchanges the token from `BDUSS` plus `PTOKEN` without loading `genflowengine.dll`. This works on Windows, Linux, Docker, and Qinglong.

## Core capabilities

- Collects the daily `LOGIN` and `CHAT` tasks.
- Handles repeated daily runs through the activity's idempotent response.
- Supports one account with `KUKU_COOKIES` and multiple accounts with `KUKU_TOKENS`.
- Resolves credentials in this order: configured STOKEN, local cache, cross-platform MD5-signature exchange.
- Masks BDUSS values in logs.
- Sends optional WeCom or PushPlus notifications.
- Uses only the Python standard library.

## Credential preparation

```bash
python kuku_get_cookie.py
python kuku_get_cookie.py --paste
python kuku_get_cookie.py --exchange
python kuku_get_cookie.py --paste --exchange
python kuku_daily.py --token
```

The default `--exchange` path reads the local desktop Cookie database first. With `--paste --exchange`, paste a complete Cookie containing `BDUSS` and `PTOKEN`; the tool then performs the pure-signature exchange on any platform. `python kuku_daily.py --token` exchanges tokens for already configured accounts. The tool prints a `KUKU_STOKEN=...` value.

## Minimum Qinglong setup

1. Upload `kuku_daily.py` to a Qinglong script directory.
2. Add `KUKU_COOKIES` and the generated `KUKU_STOKEN` as environment variables.
3. Create a scheduled task from the script list so the command is `task kuku_daily.py`.

```cron
15 8 * * *
```

```bash
task kuku_daily.py
```

For multiple accounts, set `KUKU_TOKENS` instead of the single-account variables:

```text
main|BDUSS_VALUE|PTOKEN_VALUE|STOKEN_VALUE
second|BDUSS_VALUE|PTOKEN_VALUE|STOKEN_VALUE
```

Use newlines or `&` between accounts. Each item uses `remark|BDUSS|PTOKEN[|STOKEN]`.

## Minimum GitHub Actions setup

Add these repository Secrets under **Settings → Secrets and variables → Actions**:

| Secret | Required | Purpose |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | for one account | Cookie for one account |
| `KUKU_STOKEN` | optional | Session token paired with the Cookie |
| `KUKU_TOKENS` | for multi-account | Multi-account entries; takes precedence |
| `QYWX_TOKEN` | optional | WeCom bot key |
| `PLUSPLUS_TOKEN` | optional | PushPlus token |

The bundled workflow is manual-only by default. Run **Actions → KukuAI Daily → Run workflow** for the first validation. To enable the schedule, uncomment the two `schedule:` lines in `.github/workflows/daily.yml`:

```yaml
schedule:
  - cron: '15 0 * * *'
```

The cron expression uses UTC. `15 0 * * *` means 08:15 Beijing time. The Ubuntu runner can perform the pure-signature exchange. `KUKU_STOKEN` may be omitted; `KUKU_COOKIES` is exchanged at run time and cached.

## Key environment variables

| Variable | Required | Description |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | for one account | Cookie header, Cookie-editor JSON, or an object containing `BDUSS` and `PTOKEN` |
| `KUKU_STOKEN` | optional | Issued `genflowpro` session token |
| `KUKU_TOKENS` | for multi-account | Multi-account list in `remark\|BDUSS\|PTOKEN[\|STOKEN]` format |
| `KUKU_PROXY` | optional | HTTP(S) or SOCKS5 proxy URL |
| `KUKU_NO_NOTIFY` | optional | Set to `1` to disable notifications |
| `QYWX_TOKEN` | optional | WeCom bot key; `WECHAT_WEBHOOK` is also accepted |
| `PLUSPLUS_TOKEN` | optional | PushPlus token |

## Command-line options

| Option | Effect |
| :--- | :--- |
| none | Run the daily tasks for every configured account |
| `--only N` | Run account number N only |
| `--token` | Exchange and print session tokens without checking in |

## Verification scope

The previous README records 13 offline self-tests covering Cookie parsing, request headers, credential precedence, success, idempotent responses, expired sessions, HTTP failures, multi-account parsing, and log masking. Version `v1.2.0` replaces the DLL call with the pure MD5-signature exchange. This repository does not include a real-account, end-to-end online log for that new exchange path, so it does not claim online acceptance.

## Privacy

Your Cookie, STOKEN, and account list are read from environment variables or the local token cache. Logs only display masked BDUSS fragments. Never publish `.kuku_stoken.json`, environment values, or full Cookie data in a repository, Issue, Actions log, or screenshot.

## Links

- [Releases](https://github.com/L0NE-6/KukuAI-Daily/releases)
- [Issues](https://github.com/L0NE-6/KukuAI-Daily/issues)
- [Chinese README](../README.md)
- [Changelog](../CHANGELOG.md)

## Disclaimer

This project is intended for personal learning and automation. Follow the terms of Kuku AI, Baidu Wenku, and related services, and use it at your own risk.
