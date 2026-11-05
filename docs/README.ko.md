# 🧩 KukuAI Daily

**Kuku AI 30일 체크인을 실행하는 단일 파일 스크립트입니다. 멀티 계정, Qinglong, GitHub Actions를 지원합니다.**

[简体中文](../README.md) | [English](README.en.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Português (BR)](README.pt-BR.md)

> 전체 중국어 문서는 [../README.md](../README.md)에서 확인할 수 있습니다.

## 개요

KukuAI Daily는 활동 설정, 활동 홈페이지, JS 토큰, 실제 체크인 API를 순서대로 호출합니다. 기존 freepoint 작업은 `--legacy-freepoint`를 명시한 경우에만 실행되며 자동으로 폴백하지 않습니다.

`errno=0`과 불리언 `data.signed_today=true`가 모두 확인되어야 성공입니다. `errno=10152`는 오늘 이미 체크인된 중립 상태이고, `8001` / `8002`는 업스트림 위험 제어 실패입니다.

## 요청 흐름

```text
GET  /act/api/conf?conf_key=kukuSignConf
GET  /act/v2/kukuai30/homepage?tid=<activityTid>
GET  /operation/activitys/api/getJsToken
POST /act/v2/kukuai30/signin?tid=<activityTid>&jsToken=<token>&aid=15459
```

Referer는 항상 다음과 같습니다.

```text
https://kuku.baidu.com/operation/activitys/kukuPcSignAct/main
```

## 두 종류의 STOKEN

| 구분 | 출처 | 사용 |
| :--- | :--- | :--- |
| Web STOKEN | 전체 Cookie 내부의 `STOKEN` | 30일 체크인 전용 |
| Business STOKEN | `KUKU_STOKEN`, 멀티 계정의 `business_stoken`, 캐시 또는 교환 결과 | `--legacy-freepoint` 전용 |

`KUKU_STOKEN`은 Web STOKEN을 덮어쓰지 않습니다. Cookie에 Web STOKEN이 없으면 기본 흐름은 전체 Cookie를 다시 내보내라는 오류로 종료하며 Business STOKEN으로 대체하지 않습니다.

## 단일 계정

```text
KUKU_COOKIES=BDUSS=...; STOKEN=<web-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...
```

기존 freepoint용 Business STOKEN은 별도로 설정합니다.

```text
KUKU_STOKEN=<business-stoken>
```

## 멀티 계정

JSON 배열을 권장합니다. 전체 Cookie는 `cookie`, 기존 freepoint 토큰은 `business_stoken`에 분리합니다.

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

줄 형식도 지원합니다.

```text
main|BDUSS=...; STOKEN=<web-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...|optional-business-stoken
second|BDUSS=...; STOKEN=<web-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...|optional-business-stoken
```

기존 `name|BDUSS|PTOKEN[|business-stoken]` 형식은 호환용으로만 파싱합니다. Web STOKEN과 나머지 브라우저 필드를 포함하지 않으므로 기본 30일 흐름에는 부족하며 `--legacy-freepoint`에만 적합합니다.

## Qinglong / GitHub Actions

1. `kuku_daily.py`를 업로드하고, Cookie 갱신이 필요하면 `kuku_get_cookie.py`도 함께 둡니다.
2. 단일 계정은 `KUKU_COOKIES`, 멀티 계정은 `KUKU_TOKENS`를 설정합니다.
3. `task kuku_daily.py`를 예약 실행합니다.

```cron
15 8 * * *
```

| Secret | 필수 | 설명 |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | 단일 계정 | Web STOKEN을 포함한 전체 Cookie |
| `KUKU_TOKENS` | 멀티 계정 | JSON 배열 또는 줄 형식 |
| `KUKU_STOKEN` | 선택 | 단일 계정 기존 freepoint 전용 Business STOKEN |
| `QYWX_TOKEN` | 선택 | WeCom 봇 key |
| `PLUSPLUS_TOKEN` | 선택 | PushPlus token |

## 명령행

| 옵션 | 동작 |
| :--- | :--- |
| 없음 | 모든 계정의 30일 체크인 |
| `--only N` | N번째 계정만 실행 |
| `--legacy-freepoint` | Business STOKEN을 사용하는 기존 freepoint 실행 |
| `--token` | 기존 freepoint Business STOKEN을 교환해 출력 |
| `--version` | 스크립트 버전 출력 |

## 성공 판정

| 업스트림 결과 | 로컬 처리 |
| :--- | :--- |
| `errno=0`, `data.signed_today=true` | 성공 |
| 홈페이지 `signed_today=true` | 중립 완료, POST하지 않음 |
| `errno=10152` | 중립 완료, 오늘 이미 체크인 |
| `errno=8001` / `8002` | 위험 제어 실패 |
| `signed_today` 누락 또는 비불리언 | 실패 |

## 검증

```powershell
python -m unittest discover -s tests -v
python -m pytest -q
python -m py_compile kuku_daily.py kuku_get_cookie.py tests\_loader.py tests\test_kuku_contract.py
ruff check .
```

모든 테스트는 가짜 응답을 사용합니다. 4단계 흐름, 엄격한 성공 판정, 10152, 8001/8002, 명시적 레거시, Web/Business STOKEN 분리, 멀티 계정 전체 Cookie, 마스킹, 알림을 검증합니다. 자세한 내용은 [PROTOCOL.md](PROTOCOL.md)를 확인하세요.

## 개인정보

로그는 BDUSS를 마스킹합니다. `.kuku_stoken.json`, 전체 Cookie, STOKEN, 계정 내보내기 파일을 공개하지 마세요.

## 사용 범위

공식 저장소, 스크립트, 배포 안내와 Release는 무료입니다. 저자의 서면 허가 없이 유료 판매, 유료 배포, 업데이트 대행, 저자 사칭, 결제 QR을 통한 공식 승인 오인을 금지합니다. 자세한 규칙은 [NOTICE.md](../NOTICE.md)를 확인하세요.

## 버전

- 저장소 버전: `v1.3.0`
- Release 상태: 메인 스레드에서 통합 발행
- 변경 기록: [CHANGELOG.md](../CHANGELOG.md)

## 면책 조항

이 프로젝트는 개인 학습과 자동화를 위한 것입니다. Kuku AI, Baidu Wenku 및 관련 서비스 약관을 확인하고 사용 위험은 사용자 본인이 부담하세요.
