# KukuAI Daily

**Kuku AI의 현재 `kukuai30` 일일 체크인을 실행하는 단일 파일 스크립트입니다. 멀티 계정, Qinglong, GitHub Actions를 지원합니다.**

[简体中文](../README.md) | [English](README.en.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Português (BR)](README.pt-BR.md)

## 개요

기본 흐름은 세션 신원을 읽고 체크인 패널을 확인합니다. 아직 체크인하지 않은 경우에만 signin을 한 번 전송하고, 대기 후 패널을 다시 읽습니다. 유일한 성공 기준은 체크인 후 패널의 `signed_today=true`입니다.

기존 freepoint 작업은 명시적인 `--legacy-freepoint` 옵션에서만 실행되며, 기본 흐름은 이전 API로 자동 전환하지 않습니다.

## 요청 흐름

```text
GET  /api/genflowpro/common/userreport?<client-query>
POST /act/v2/kukuai30/homepage?uid=<uk>&tid=291651792210&<client-query>
POST /act/v2/kukuai30/signin?uid=<uk>&tid=291651792210&<client-query>
POST /act/v2/kukuai30/homepage?uid=<uk>&tid=291651792210&<client-query>
```

`uk`는 `userreport.data.uk`에서 가져옵니다. 고정 패널 ID는 `291651792210`입니다. 폐기된 `getJsToken`, `activityTid`, `aid=15459`, `jsToken`은 사용하지 않습니다.

## 인증 정보

```text
KUKU_COOKIES=BDUSS=...; PTOKEN=...; STOKEN=...; BAIDUID=...; PANPSC=...
```

여러 계정은 JSON 배열을 권장합니다.

```json
[
  {
    "name": "main",
    "cookie": "BDUSS=...; PTOKEN=...; STOKEN=...; BAIDUID=...; PANPSC=...",
    "business_stoken": ""
  }
]
```

`PTOKEN`이 있으면 `genflowpro` 비즈니스 STOKEN으로 교환합니다. 교환 실패는 명시적인 오류로 처리됩니다. `KUKU_STOKEN` / `business_stoken`은 기존 freepoint와 `--token` 경로 전용입니다.

## 성공 판정

| 패널 상태 | 결과 |
| :--- | :--- |
| 체크인 전 이미 `signed_today=true` | 중립 완료, signin을 보내지 않음 |
| 체크인 후 `signed_today=true` | 이번 체크인 성공 |
| 체크인 후에도 `false` | 실패, action 응답의 이유 표시 |
| action이 `10152`여도 재조회가 false | 실패 |
| action이 `8001` | 서버 거부 사유를 그대로 표시 |
| `uk`, `data`, 응답 형식이 잘못됨 | 실패 |

HTTP 200, action `errno=0`, `errno=10152`만으로는 성공이 아닙니다.

## 실행 및 검증

```text
python kuku_daily.py
python -m unittest discover -s tests -v
python -m pytest -q
python -m py_compile kuku_daily.py kuku_get_cookie.py tests\_loader.py tests\test_kuku_contract.py
ruff check .
```

## 개인정보와 재배포

전체 Cookie, STOKEN, `.kuku_stoken.json`, 계정 내보내기 파일, 인증 정보가 보이는 스크린샷을 공개하지 마세요. 공식 저장소와 Release는 무료입니다. 유료 포장, 작성자 사칭, 작성자 이름이나 결제 QR을 이용한 공식 승인 오인을 금지합니다. 자세한 내용은 [NOTICE.md](../NOTICE.md)를 확인하세요.

## 버전

- 저장소 버전: `v1.4.0`
- 변경 기록: [CHANGELOG.md](../CHANGELOG.md)

이 프로젝트는 개인 자동화용입니다. 관련 서비스 약관을 확인하고 사용 위험은 사용자 본인이 부담합니다.
