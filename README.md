<div align="center">

<sub><strong>L0NE-6 · DAILY SIGNAL</strong></sub>

# 🧩 KukuAI Daily

**库库 AI（百度文库 GenFlowPro）现行 `kukuai30` 每日签到，单文件、多账号、服务端复读与显式旧链路开关。**

> 当前版本：**v1.4.1**（2026-11-16） · 核心能力：userreport → homepage → signin → homepage、STOKEN 换发、风控错误说明

[简体中文](README.md) · [English](docs/README.en.md) · [繁體中文](docs/README.zh-Hant.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Português (BR)](docs/README.pt-BR.md)

<img src="https://img.shields.io/github/v/release/L0NE-6/KukuAI-Daily?style=for-the-badge&label=Release&color=2ea44f&logo=github" alt="Release" />
<img src="https://img.shields.io/github/stars/L0NE-6/KukuAI-Daily?style=for-the-badge&label=Stars&color=FFC75F&logo=github" alt="Stars" />
<img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
<img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Qinglong-4EAA25?style=for-the-badge&logo=linux&logoColor=white" alt="Platform" />
<img src="https://img.shields.io/github/license/L0NE-6/KukuAI-Daily?style=for-the-badge&label=License&color=F472B6" alt="License" />
<a href="https://github.com/L0NE-6/KukuAI-Daily/releases"><img src="https://img.shields.io/badge/Download-Releases-2ea44f?style=for-the-badge&logo=github" alt="Download" /></a>

[🚫 使用边界](#usage-policy) · [✨ 30 秒速览](#overview) · [🧭 这是什么](#what-is-this) · [🔁 协议](#protocol) · [🔑 凭据](#credentials) · [🚀 本地](#local) · [🐧 青龙](#qinglong) · [☁️ Actions](#actions) · [⌨️ CLI](#cli-output) · [🧾 结果码](#result-codes) · [✅ 成功判据](#success) · [🧪 测试](#tests) · [🧱 设计原则](#design) · [🔒 隐私](#privacy) · [📁 目录](#layout) · [📦 版本](#release) · [⚠️ 免责声明](#disclaimer) · [☕ 赞赏](#donate) · [💬 反馈与 Star](#feedback)

</div>

---

<a id="usage-policy"></a>
## 🚫 使用边界与转载声明

> [!IMPORTANT]
> **官方版本永久免费。** 未经作者书面许可，禁止付费包装、搬运引流、冒充作者，或使用作者身份与二维码制造官方授权假象。

本项目仓库、脚本、部署说明和 Release 下载始终免费公开。未经作者明确书面许可，禁止将其包装为付费资源、内部版、独家版、会员权益、收费课程、付费部署或包更新服务；禁止搬运到其他账号、群组、频道、网盘、电商或付费平台进行涨粉、截流、倒卖和引流。

如需商业合作、品牌授权、联合分发或使用作者名义提供付费服务，请先取得作者明确书面授权。完整规则见 [NOTICE.md](NOTICE.md)。

---

<a id="overview"></a>
## ✨ 30 秒速览

| 维度 | 说明 |
| :--- | :--- |
| **做什么** | 执行库库 AI 客户端同款 `kukuai30` 每日签到。 |
| **输入** | `KUKU_COOKIES` 单账号，或 `KUKU_TOKENS` 多账号；完整 Cookie 推荐包含 `BDUSS`、`PTOKEN` 和同会话字段。 |
| **输出** | 账号结果、`uk` 读取状态、动作 `errno`、签到后 homepage 状态和汇总。 |
| **部署** | Windows、Linux、青龙面板、GitHub Actions。 |
| **依赖** | Python 3.8+，仅标准库。 |
| **成功判据** | 签到后 homepage 复读 `signed_today=true`。 |

---

<a id="what-is-this"></a>
## 🧭 这是什么

默认流程为：

```text
userreport 获取 uk
  → homepage 预读
  → signed_today=true：今日已完成
  → 否则 signin 一次
  → 等待 0.9 秒
  → homepage 复读
```

旧 freepoint 任务只在显式传入 `--legacy-freepoint` 时执行，默认链路失败不会自动切换。脚本不会把 HTTP 200、动作 `errno=0` 或 `errno=10152` 当成今日签到成功。

---

<a id="protocol"></a>
## 🔁 协议、工作原理与回读

基址为 `https://kuku.baidu.com`，固定活动 `tid=291651792210`。

```text
GET  /api/genflowpro/common/userreport?<client-query>
POST /act/v2/kukuai30/homepage?uid=<uk>&tid=291651792210&<client-query>
POST /act/v2/kukuai30/signin?uid=<uk>&tid=291651792210&<client-query>
POST /act/v2/kukuai30/homepage?uid=<uk>&tid=291651792210&<client-query>
```

`uk` 来自 `userreport.data.uk`，支持字符串或整数。请求使用客户端同款 User-Agent、`/genflowpro` Referer、Origin 和 JSON 空对象 body。

完整 Cookie 存在 `PTOKEN` 时，脚本先通过 `BDUSS + PTOKEN` 换发本次运行使用的 `genflowpro` 业务 STOKEN。换发失败直接终止，不静默沿用旧令牌。完整协议字段见 [docs/PROTOCOL.md](docs/PROTOCOL.md)。

---

<a id="credentials"></a>
## 🔑 凭据与环境变量

| 变量 | 必填 | 说明 |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | 单账号 | 完整 Cookie |
| `KUKU_TOKENS` | 多账号 | JSON 数组或一行一个账号 |
| `KUKU_STOKEN` | 否 | 只供 `--legacy-freepoint` 与 `--token` |
| `KUKU_PROXY` | 否 | HTTP(S) 或 SOCKS 代理 |
| `KUKU_ENGINE_DLL` | 否 | 换发时指定 GenFlow 引擎 DLL |
| `WORKBUDDY_GENFLOW_ENGINE_DLL` | 兼容 | 引擎 DLL 兼容变量 |
| `KUKU_NO_NOTIFY` | 否 | `1` 表示关闭通知 |
| `QYWX_TOKEN` / `WECHAT_WEBHOOK` | 否 | 企业微信 |
| `PLUSPLUS_TOKEN` | 否 | PushPlus |

单账号：

```text
KUKU_COOKIES=BDUSS=...; PTOKEN=...; STOKEN=...; BAIDUID=...; PANPSC=...
```

多账号 JSON：

```json
[
  {
    "name": "主号",
    "cookie": "BDUSS=...; PTOKEN=...; STOKEN=...; BAIDUID=...; PANPSC=...",
    "business_stoken": ""
  }
]
```

`business_stoken` 不参与默认 `kukuai30` 请求。

---

<a id="local"></a>
## 🚀 本地快速开始

```bash
python kuku_daily.py
python kuku_daily.py --only 1
python kuku_daily.py --version
```

更新客户端 Cookie：

```bash
python kuku_get_cookie.py
python kuku_get_cookie.py --paste
python kuku_get_cookie.py --exchange
python kuku_get_cookie.py --paste --exchange
```

旧 freepoint 只显式运行：

```bash
python kuku_daily.py --legacy-freepoint
```

---

<a id="qinglong"></a>
## 🐧 青龙面板

1. 上传 `kuku_daily.py`。
2. 需要更新 Cookie 时同时上传 `kuku_get_cookie.py`。
3. 配置 `KUKU_COOKIES` 或 `KUKU_TOKENS`。
4. 创建任务：

```text
15 8 * * * task kuku_daily.py
```

脚本仅使用标准库，无需安装第三方依赖。需要企业微信或 PushPlus 时再配置对应变量。

---

<a id="actions"></a>
## ☁️ GitHub Actions

工作流位于 [`.github/workflows/daily.yml`](.github/workflows/daily.yml)，当前只启用 `workflow_dispatch`；定时段保持注释，启用时使用 UTC。

| Secret | 必填 | 说明 |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | 单账号 | 完整 Cookie |
| `KUKU_TOKENS` | 多账号 | JSON 数组或一行一个账号 |
| `KUKU_STOKEN` | 否 | 仅旧 freepoint / `--token` |
| `QYWX_TOKEN` | 否 | 企业微信 |
| `PLUSPLUS_TOKEN` | 否 | PushPlus |

工作流使用 Python 3.11，不安装第三方依赖。

---

<a id="cli-output"></a>
## ⌨️ CLI 与输出

| 参数 | 作用 |
| :--- | :--- |
| 无 | 运行所有账号的现行 `kukuai30` 签到 |
| `--only N` | 只运行第 N 个账号 |
| `--legacy-freepoint` | 显式运行旧 freepoint 任务 |
| `--token` | 换发并输出旧 freepoint 业务 STOKEN，不执行签到 |
| `--version` | 输出版本 |

输出包含脱敏 Cookie 尾部、`uk` 读取、homepage 预读、signin 动作、homepage 复读和账号汇总。

---

<a id="result-codes"></a>
## 🧾 结果码

| 结果 | 含义 |
| :--- | :--- |
| 签到前 `signed_today=true` | 中性完成，不发送 signin |
| 签到后 `signed_today=true` | 本次签到成功 |
| 签到后 `signed_today=false` | 失败，保留动作 `errno/errmsg` |
| `errno=10152` 且复读 false | 失败，不能直接当已签 |
| `errno=8001/8002` | 活动侧风控拒绝，保留服务端原因 |
| 缺 `uk`、缺 `data`、HTTP 非 200 | 失败，不发送后续无效请求 |
| 退出码 `0` | 至少一个账号成功或中性完成 |
| 退出码 `1` | 配置错误或全部账号失败 |

---

<a id="success"></a>
## ✅ 成功判据

唯一完成证据是签到后 homepage 的 `signed_today` 为布尔 `true`。

签到前已经是 `true` 时按幂等完成处理，不重复提交。动作响应 `errno=0`、`errno=10152`、HTTP 200 或返回文案都不能覆盖最终 homepage 复读结果。

---

<a id="tests"></a>
## 🧪 测试

```bash
python -m unittest discover -s tests -v
python -m pytest -q
python -m py_compile kuku_daily.py kuku_get_cookie.py
ruff check .
git diff --check
```

现有 25 项离线测试覆盖主链路、字符串/整数 `uk`、缺 `uk` 短路、签到后复读、`10152` 不覆盖复读、`8001/8002` 提示、旧链路显式开关、多账号 Cookie/Extras、脱敏与通知汇总。全部使用假响应。

---

<a id="design"></a>
## 🧱 设计原则

- **服务端复读定成败**：动作回执不能单独判定完成。
- **旧链路显式启用**：默认流程不自动切换。
- **完整会话优先**：推荐完整 Cookie，换发失败立即报错。
- **账号隔离**：单账号异常不阻断其他账号。
- **零第三方依赖**：主脚本只使用 Python 标准库。
- **最小泄露**：日志只显示脱敏 Cookie 尾部。

---

<a id="privacy"></a>
## 🔒 隐私与数据边界

- Cookie、会话 STOKEN 与换发结果不从外部服务器收集。
- 日志只显示脱敏后的 BDUSS 尾部。
- `.kuku_stoken.json`、环境变量、完整 Cookie 和多账号导出文件不要提交。
- `--token` 会主动打印业务 STOKEN，只应在可信终端使用。
- 提交 Issue 前移除 Cookie、STOKEN、`uk` 和账号导出内容。

---

<a id="layout"></a>
## 📁 目录结构

```text
KukuAI-Daily/
├── .github/workflows/daily.yml
├── assets/
├── docs/
│   ├── PROTOCOL.md
│   └── README.*.md
├── tests/
├── kuku_daily.py
├── kuku_get_cookie.py
├── CHANGELOG.md
├── LICENSE
├── NOTICE.md
├── requirements.txt
├── ruff.toml
└── README.md
```

---

<a id="release"></a>
## 📦 版本与发布

- 当前版本：`v1.4.1`。
- 历史版本保留在 [Releases](https://github.com/L0NE-6/KukuAI-Daily/releases)。
- 更新记录见 [CHANGELOG.md](CHANGELOG.md)。

---

<a id="disclaimer"></a>
## ⚠️ 免责声明

本项目用于个人学习与合法自动化实践。使用者应自行遵守库库 AI、百度文库及相关服务条款，并承担误配置、凭据泄露或账号异常带来的风险。

---

<a id="donate"></a>
## ☕ 支持与投喂：微信与支付宝赞赏码

脚本完全免费，赞赏纯自愿，不影响任何功能。

<p align="center">
  <img src="assets/donate-wechat.png" width="260" alt="微信赞赏码" />
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/donate-alipay.jpg" width="260" alt="支付宝赞赏码" />
</p>

<p align="center"><sub>微信支付（左） · 支付宝（右）</sub></p>

> [!WARNING]
> 收款码仅用于向作者自愿赞赏。任何第三方以代下载、代部署、内部资源、会员群或官方授权为由收费，均与作者无关。

---

<a id="feedback"></a>
## 💬 反馈与贡献：Star History

- [Issues](https://github.com/L0NE-6/KukuAI-Daily/issues)
- [Pull Requests](https://github.com/L0NE-6/KukuAI-Daily/pulls)
- [Releases](https://github.com/L0NE-6/KukuAI-Daily/releases)

<a href="https://star-history.com/#L0NE-6/KukuAI-Daily&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=L0NE-6/KukuAI-Daily&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=L0NE-6/KukuAI-Daily&type=Date&theme=light" />
    <img alt="KukuAI Daily Star History" src="https://api.star-history.com/svg?repos=L0NE-6/KukuAI-Daily&type=Date&theme=light" />
  </picture>
</a>

<div align="center">

[⭐ Star](https://github.com/L0NE-6/KukuAI-Daily) · [🍴 Fork](https://github.com/L0NE-6/KukuAI-Daily/fork) · L0NE-6 · DAILY SIGNAL

</div>
