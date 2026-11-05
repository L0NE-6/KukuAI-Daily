<div align="center">

<sub><strong>L0NE-6 · DAILY SIGNAL</strong></sub>

# 🧩 KukuAI Daily

**库库 AI（百度文库 GenFlowPro）「库库 30 天签到」单文件脚本，支持多账号、青龙与 GitHub Actions。**

[简体中文](README.md) · [English](docs/README.en.md) · [繁體中文](docs/README.zh-Hant.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Português (BR)](docs/README.pt-BR.md)

<img src="https://img.shields.io/github/v/release/L0NE-6/KukuAI-Daily?style=for-the-badge&label=Release&color=2ea44f&logo=github" />
<img src="https://img.shields.io/github/stars/L0NE-6/KukuAI-Daily?style=for-the-badge&label=Stars&color=FFC75F&logo=github" />
<img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/%E9%9D%92%E9%BE%99-Qinglong-4EAA25?style=for-the-badge" />
<img src="https://img.shields.io/badge/GitHub%20Actions-Supported-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-F472B6?style=for-the-badge" />

[✨ 30 秒速览](#quick-overview) · [🔁 签到流程](#flow) · [🔑 凭据格式](#credentials) · [🚀 部署](#deploy) · [✅ 成功判据](#result) · [🧪 验证](#verify) · [✦ 星轨](#star-trail)

</div>

---

<a id="policy"></a>
## 🚫 使用边界与转载声明

> [!IMPORTANT]
> 官方版本永久免费。未经作者书面许可，禁止付费包装、搬运引流、冒充作者，或使用作者身份与二维码制造官方授权假象。完整规则见 [NOTICE.md](NOTICE.md)。

本项目仓库、脚本、部署说明和 Release 始终免费公开。未经作者明确书面许可，禁止将本项目包装为付费资源、内部版、独家版、会员权益、收费课程、付费部署或包更新服务；禁止删除作者与版权信息后冒充原创；禁止使用作者昵称、头像、二维码和项目名称制造官方授权假象。

---

<a id="quick-overview"></a>
## ✨ 30 秒速览

| 维度 | 说明 |
| :--- | :--- |
| **主用途** | 执行库库 AI「库库 30 天签到」。 |
| **默认链路** | 配置 → 活动首页 → `getJsToken` → 签到。 |
| **输入** | 单账号 `KUKU_COOKIES`，或多账号 `KUKU_TOKENS`。 |
| **成功判据** | 签到响应 `errno=0` 且 `data.signed_today` 为布尔 `true`。 |
| **中性状态** | `errno=10152` 视为今日已签；首页 `signed_today=true` 时不重复提交。 |
| **失败状态** | `errno=8001` / `8002` 按上游风控失败处理。 |
| **旧链路** | 仅 `--legacy-freepoint` 显式启用，不自动回退。 |
| **依赖** | Python 3.8+，仅标准库。 |

<a id="flow"></a>
## 🔁 默认签到流程

```text
GET  /act/api/conf?conf_key=kukuSignConf
GET  /act/v2/kukuai30/homepage?tid=<activityTid>
GET  /operation/activitys/api/getJsToken
POST /act/v2/kukuai30/signin?tid=<activityTid>&jsToken=<token>&aid=15459
```

所有请求固定使用活动页 Referer：

```text
https://kuku.baidu.com/operation/activitys/kukuPcSignAct/main
```

只有当签到响应同时满足 `errno=0` 和 `data.signed_today=true` 才算签到成功。HTTP 200、空响应或缺少 `signed_today` 都不能代替业务成功。

<a id="credentials"></a>
## 🔑 凭据模型

脚本严格区分两种 STOKEN：

| 名称 | 来源 | 用途 |
| :--- | :--- | :--- |
| **网页 STOKEN** | `KUKU_COOKIES` / 多账号 Cookie 内的 `STOKEN` | 仅供 30 天签到；必须来自同一份完整网页 Cookie。 |
| **业务 STOKEN** | `KUKU_STOKEN`、多账号 `business_stoken`、本机缓存或换发结果 | 仅 `--legacy-freepoint` 使用。 |

> [!IMPORTANT]
> `KUKU_STOKEN` 不会覆盖网页 `STOKEN`。如果 Cookie 缺少网页 `STOKEN`，默认 30 天签到会直接失败并提示重新导出完整 Cookie，不会静默换成业务 STOKEN。

### 单账号

```text
KUKU_COOKIES=BDUSS=...; STOKEN=<网页STOKEN>; PTOKEN=...; BAIDUID=...; PANPSC=...
```

`KUKU_STOKEN` 可选，仅用于旧 freepoint：

```text
KUKU_STOKEN=<旧freepoint业务STOKEN>
```

### 多账号

推荐使用 JSON 数组。每条账号把完整 Cookie 放进 `cookie`，业务 STOKEN 单独放进 `business_stoken`：

```json
[
  {
    "name": "主号",
    "cookie": "BDUSS=...; STOKEN=<网页STOKEN>; PTOKEN=...; BAIDUID=...; PANPSC=...",
    "business_stoken": ""
  },
  {
    "name": "副号",
    "cookie": "BDUSS=...; STOKEN=<网页STOKEN>; PTOKEN=...; BAIDUID=...; PANPSC=...",
    "business_stoken": ""
  }
]
```

也支持一行一个账号：

```text
主号|BDUSS=...; STOKEN=<网页STOKEN>; PTOKEN=...; BAIDUID=...; PANPSC=...|旧freepoint业务STOKEN（可空）
副号|BDUSS=...; STOKEN=<网页STOKEN>; PTOKEN=...; BAIDUID=...; PANPSC=...|旧freepoint业务STOKEN（可空）
```

旧位置格式 `备注|BDUSS|PTOKEN[|业务STOKEN]` 仍可解析，但它不包含网页 STOKEN 与其它 Cookie，因此只适合显式 `--legacy-freepoint`；默认 30 天签到会明确报缺少网页 STOKEN。

<a id="deploy"></a>
## 🚀 青龙 / Actions

1. 上传 `kuku_daily.py`，需要更新客户端 Cookie 时同时上传 `kuku_get_cookie.py`。
2. 单账号配置 `KUKU_COOKIES`；多账号配置 `KUKU_TOKENS`。
3. 新建定时任务 `task kuku_daily.py`，或运行 `python kuku_daily.py`。
4. 需要推送时配置企业微信或 PushPlus 变量。

```cron
15 8 * * *
```

GitHub Actions Secrets：

| Secret | 必填 | 说明 |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | 单账号 | 完整网页 Cookie，必须含网页 `STOKEN`。 |
| `KUKU_TOKENS` | 多账号 | 推荐 JSON 数组；配置后优先于单账号变量。 |
| `KUKU_STOKEN` | 可选 | 仅单账号旧 freepoint 使用的业务 STOKEN；默认 30 天链路不读取。 |
| `QYWX_TOKEN` | 可选 | 企业微信机器人 key。 |
| `PLUSPLUS_TOKEN` | 可选 | PushPlus token。 |

<a id="result"></a>
## ✅ 成功、幂等与退出码

| 上游结果 | 本地处理 |
| :--- | :--- |
| `errno=0` 且 `data.signed_today=true` | 本次签到成功。 |
| 首页 `signed_today=true` | 中性完成，不再 POST。 |
| `errno=10152` | 中性完成，视为今日已签。 |
| `errno=8001` / `8002` | 风控失败，提示重新登录或重新导出 Cookie。 |
| 其它 `errno` | 失败，保留脱敏后的业务原因。 |
| 缺少 `signed_today` / 非布尔 `true` | 失败，不把缺省值当成功。 |

只要至少一个账号得到成功或中性完成，主进程通常返回 `0`；全部账号失败时返回非零，便于青龙和 Actions 识别。

## ⌨️ 命令行

| 参数 | 作用 |
| :--- | :--- |
| 无 | 运行所有账号的库库 30 天签到。 |
| `--only N` | 只运行第 N 个账号。 |
| `--legacy-freepoint` | 显式运行旧 freepoint 任务，使用业务 STOKEN。 |
| `--token` | 换发并输出旧 freepoint 业务 STOKEN，不执行签到。 |
| `--version` | 输出脚本版本。 |

## 🛠️ 凭据工具

```bash
python kuku_get_cookie.py
python kuku_get_cookie.py --paste
python kuku_get_cookie.py --exchange
python kuku_get_cookie.py --paste --exchange
```

默认 30 天签到不需要换发业务 STOKEN。`--exchange` 和 `kuku_get_cookie.py --stoken` 产出的 `KUKU_STOKEN` 只供旧 freepoint 使用。工具读取客户端 Cookie 数据库时会保留百度域完整字段，包括 `BAIDUID`、`PTOKEN`、`PANPSC` 等。

<a id="verify"></a>
## 🧪 本地验证

```powershell
python -m unittest discover -s tests -v
python -m pytest -q
python -m py_compile kuku_daily.py kuku_get_cookie.py tests\_loader.py tests\test_kuku_contract.py
ruff check .
```

测试全部使用假响应，不访问真实签到接口。覆盖四步主链路、严格成功判据、10152、8001/8002、旧链路显式开关、双 STOKEN 隔离、多账号完整 Cookie/Extras、脱敏和通知汇总。

协议证据与字段说明见 [docs/PROTOCOL.md](docs/PROTOCOL.md)。

## 🔒 隐私

- 日志只显示脱敏后的 BDUSS 尾部。
- Cookie、网页 STOKEN、业务 STOKEN 不从外部服务器收集。
- `.kuku_stoken.json`、环境变量、完整 Cookie 和多账号导出文件不要提交到仓库、Issue 或公开日志。
- `--token` 会主动打印业务 STOKEN，只应在可信终端中使用。

## 📦 版本与发布

- 当前仓库版本：`v1.3.0`。
- Release 状态：由主线程统一发布，本文档不宣称已经上线。
- Release 页：[L0NE-6/KukuAI-Daily Releases](https://github.com/L0NE-6/KukuAI-Daily/releases)。
- 更新记录：[CHANGELOG.md](CHANGELOG.md)。

## ⚠️ 免责声明

本项目用于个人学习与自动化实践。请自行遵守库库 AI、百度文库及相关服务的条款，并承担账号使用风险。

<a id="star-trail"></a>
## ✦ 星轨 Star Trail

<a href="https://star-history.com/#L0NE-6/KukuAI-Daily&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=L0NE-6/KukuAI-Daily&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=L0NE-6/KukuAI-Daily&type=Date&theme=light" />
    <img alt="KukuAI Daily Star Trail" src="https://api.star-history.com/svg?repos=L0NE-6/KukuAI-Daily&type=Date&theme=light" />
  </picture>
</a>

## ☕ 支持与反馈

脚本免费、无广告。Issue 请附脱敏日志、复现步骤和运行环境，不要提交 Cookie、STOKEN 或账号导出文件。

<p align="center">
  <img src="assets/donate-wechat.png" width="260" alt="微信赞赏码" />
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/donate-alipay.jpg" width="260" alt="支付宝赞赏码" />
</p>
<p align="center"><sub>💚 微信支付（左） &nbsp;|&nbsp; 💙 支付宝（右，支持信用卡 / 花呗）</sub></p>

> ⚠️ 收款码仅用于向作者自愿赞赏。任何第三方以代下载、代部署、内部资源或会员群为由收费，均与作者无关，请停止付款并保留证据。

---

<div align="center">
  <a href="https://github.com/L0NE-6/KukuAI-Daily/releases">Releases</a> ·
  <a href="https://github.com/L0NE-6/KukuAI-Daily/issues">Issues</a> ·
  <a href="https://github.com/L0NE-6/KukuAI-Daily">Star</a>
  <br />
  <sub>L0NE-6 · DAILY SIGNAL · 让每一次运行都留下可验证的信号</sub>
</div>
