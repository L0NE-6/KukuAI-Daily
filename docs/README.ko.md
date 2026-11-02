# 🧩 KukuAI Daily

**Kuku AI(Baidu Wenku GenFlowPro)의 매일 LOGIN 및 CHAT 보상을 수집하는 멀티 계정·Qinglong·GitHub Actions 자동화입니다.**

[简体中文](../README.md) | [English](README.en.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Português (BR)](README.pt-BR.md)

> 전체 중국어 문서는 [../README.md](../README.md)에서 확인할 수 있습니다.

## 개요

KukuAI Daily는 Kuku AI 무료 포인트 활동에서 매일 로그인 보상과 대화 작업 보상을 받습니다. 성공하면 계정별 실제 결과를 출력합니다. 당일 보상을 이미 받았다면 API가 `reward_point=0`을 반환하며, 스크립트는 이를 새 보상으로 오인하지 않고 멱등적인 "오늘 이미 수령" 상태로 표시합니다.

비즈니스 API에는 `genflowpro` 범위의 세션 토큰이 필요합니다. 웹 Cookie만으로는 일반 계정 조회가 될 수 있어도 활동 API는 로그인되지 않은 상태로 판단합니다. 현재 `v1.2.0`은 공식 엔진의 MD5 서명을 재현하여 `BDUSS`와 `PTOKEN`으로 토큰을 교환하며 `genflowengine.dll`을 로드하지 않습니다. Windows, Linux, Docker, Qinglong에서 실행할 수 있습니다.

## 핵심 기능

- 매일 `LOGIN` 및 `CHAT` 작업을 수집합니다.
- API의 멱등 응답을 올바르게 처리합니다.
- 단일 계정은 `KUKU_COOKIES`, 멀티 계정은 `KUKU_TOKENS`를 사용합니다.
- 설정된 STOKEN, 로컬 캐시, 크로스 플랫폼 MD5 서명 교환 순서로 자격 증명을 확인합니다.
- 로그에서 BDUSS를 마스킹합니다.
- 선택적으로 WeCom 및 PushPlus 알림을 보냅니다.
- Python 표준 라이브러리만 사용합니다.

## 자격 증명 준비

```bash
python kuku_get_cookie.py
python kuku_get_cookie.py --paste
python kuku_get_cookie.py --exchange
python kuku_get_cookie.py --paste --exchange
python kuku_daily.py --token
```

기본 `--exchange`는 로컬 데스크톱 Cookie 데이터베이스를 읽습니다. `--paste --exchange`에서는 `BDUSS`와 `PTOKEN`이 포함된 전체 Cookie를 붙여넣고 어느 플랫폼에서나 순수 서명 교환을 실행할 수 있습니다. `python kuku_daily.py --token`은 설정된 계정의 토큰을 교환합니다. 성공하면 `KUKU_STOKEN=...` 값이 출력됩니다.

## 최소 Qinglong 설정

1. `kuku_daily.py`를 Qinglong 스크립트 디렉터리에 업로드합니다.
2. 환경 변수 `KUKU_COOKIES`와 교환한 `KUKU_STOKEN`을 추가합니다.
3. 스크립트 목록에서 예약 작업을 만들고 명령을 `task kuku_daily.py`로 설정합니다.

```cron
15 8 * * *
```

```bash
task kuku_daily.py
```

멀티 계정에는 `KUKU_TOKENS`를 사용합니다.

```text
main|BDUSS_VALUE|PTOKEN_VALUE|STOKEN_VALUE
second|BDUSS_VALUE|PTOKEN_VALUE|STOKEN_VALUE
```

계정은 줄바꿈 또는 `&`로 구분합니다. 각 항목은 `메모|BDUSS|PTOKEN[|STOKEN]` 형식입니다.

## 최소 GitHub Actions 설정

**Settings → Secrets and variables → Actions**에서 다음 Secrets를 추가합니다.

| Secret | 필수 | 용도 |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | 단일 계정 | 단일 계정 Cookie |
| `KUKU_STOKEN` | 선택 | Cookie와 함께 사용할 세션 토큰 |
| `KUKU_TOKENS` | 멀티 계정 | 멀티 계정 항목이며 설정 시 우선 사용 |
| `QYWX_TOKEN` | 선택 | WeCom 봇 key |
| `PLUSPLUS_TOKEN` | 선택 | PushPlus token |

포함된 워크플로는 기본적으로 수동 실행만 지원합니다. 먼저 **Actions → KukuAI Daily → Run workflow**로 검증합니다. 예약 실행을 켜려면 `.github/workflows/daily.yml`에서 `schedule:` 두 줄의 주석을 해제합니다.

```yaml
schedule:
  - cron: '15 0 * * *'
```

`15 0 * * *`는 UTC 기준이며 베이징 시간 매일 08:15입니다. Ubuntu runner에서도 순수 서명 교환을 실행할 수 있습니다. `KUKU_STOKEN`은 생략할 수 있으며 `KUKU_COOKIES`에서 실행 시 교환하고 캐시합니다.

## 주요 환경 변수

| 변수 | 필수 | 설명 |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | 단일 계정 | Cookie 헤더, Cookie 편집기 JSON 또는 `BDUSS` / `PTOKEN` 객체 |
| `KUKU_STOKEN` | 선택 | 교환한 `genflowpro` 세션 토큰 |
| `KUKU_TOKENS` | 멀티 계정 | `메모\|BDUSS\|PTOKEN[\|STOKEN]` 형식의 멀티 계정 |
| `KUKU_PROXY` | 선택 | HTTP(S) 또는 SOCKS5 프록시 URL |
| `KUKU_NO_NOTIFY` | 선택 | `1`로 설정하면 알림 비활성화 |
| `QYWX_TOKEN` | 선택 | WeCom 봇 key이며 `WECHAT_WEBHOOK`도 지원 |
| `PLUSPLUS_TOKEN` | 선택 | PushPlus token |

## 명령행 옵션

| 옵션 | 동작 |
| :--- | :--- |
| 없음 | 설정된 모든 계정의 매일 작업 실행 |
| `--only N` | N번째 계정만 실행 |
| `--token` | 체크인 없이 세션 토큰만 교환하고 출력 |

## 검증 범위

이전 README에는 Cookie 파싱, 요청 헤더, 자격 증명 우선순위, 성공, 멱등 응답, 세션 만료, HTTP 실패, 멀티 계정 파싱, 로그 마스킹을 다루는 13개 오프라인 자체 테스트가 기록되어 있습니다. `v1.2.0`은 DLL 호출을 순수 MD5 서명 교환으로 대체했습니다. 새 교환 경로의 실제 계정 온라인 종단 간 로그는 포함되어 있지 않으므로 온라인 검수를 완료했다고 주장하지 않습니다.

## 개인정보 보호

Cookie, STOKEN, 계정 목록은 환경 변수 또는 로컬 토큰 캐시에서만 읽습니다. 로그에는 마스킹된 BDUSS 일부만 표시됩니다. `.kuku_stoken.json`, 환경 변수 값, 전체 Cookie를 저장소, Issue, Actions 로그 또는 스크린샷에 공개하지 마세요.

## 사용 범위 및 재배포 안내

공식 저장소, 스크립트, 배포 안내, Release는 무료로 공개됩니다. 저자의 명시적 서면 허가 없이 이 프로젝트를 유료 자료, 유료 배포, 업데이트 대행으로 포장하거나, 출처와 저작자 표시를 삭제하고 원작자로 가장하거나, 저자의 신원, 이름, 아바타, 결제 QR 코드를 사용해 공식 승인으로 오인하게 하는 행위를 금지합니다. 관련 없는 계정, 그룹, 채널, 유료 플랫폼에 옮겨 팔로워 증가, 트래픽 유도, 재판매를 하는 행위도 금지됩니다. 위반 시 게시 중단 요청을 받을 수 있으며 저자는 업데이트 중단, 저장소 보관 또는 삭제를 결정할 수 있습니다. 전체 규칙은 [NOTICE.md](../NOTICE.md)를 확인하세요.

## 링크

- [Releases](https://github.com/L0NE-6/KukuAI-Daily/releases)
- [Issues](https://github.com/L0NE-6/KukuAI-Daily/issues)
- [중국어 README](../README.md)
- [변경 기록](../CHANGELOG.md)

## 면책 조항

이 프로젝트는 개인 학습과 자동화를 위한 것입니다. Kuku AI, Baidu Wenku 및 관련 서비스 약관을 확인하고 사용 위험은 사용자 본인이 부담하세요.
