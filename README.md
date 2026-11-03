<div align="center">

<sub><strong>L0NE-6 · DAILY SIGNAL</strong></sub>

# 🧩 KukuAI Daily

**库库 AI（百度文库 GenFlowPro）每日登录与对话奖励领取，支持多账号和青龙 / Actions 定时运行。**

[简体中文](README.md) · [English](docs/README.en.md) · [繁體中文](docs/README.zh-Hant.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Português (BR)](docs/README.pt-BR.md)

<img src="https://img.shields.io/github/v/release/L0NE-6/KukuAI-Daily?style=for-the-badge&label=Release&color=2ea44f&logo=github" />
<img src="https://img.shields.io/github/stars/L0NE-6/KukuAI-Daily?style=for-the-badge&label=Stars&color=FFC75F&logo=github" />
<img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/%E9%9D%92%E9%BE%99-Qinglong-4EAA25?style=for-the-badge" />
<img src="https://img.shields.io/badge/GitHub%20Actions-Supported-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-F472B6?style=for-the-badge" />
<a href="https://github.com/L0NE-6/KukuAI-Daily/releases"><img src="https://img.shields.io/badge/%E2%AC%87%20Download-Releases-2ea44f?style=for-the-badge&logo=github" /></a>

[✨ 30 秒速览](#-30-秒速览) · [🚀 青龙面板](#-青龙面板) · [☁️ GitHub Actions](#-github-actions) · [🔑 获取凭据](#-获取凭据) · [🔧 环境变量](#-环境变量) · [❓ 常见问题](#-常见问题) · [🚫 使用边界](#usage-policy) · [✦ 星轨](#-星轨-star-trail)

</div>

---

<a id="usage-policy"></a>
## 🚫 使用边界与转载声明

> [!IMPORTANT]
> **官方版本永久免费。** 未经作者书面许可，禁止付费包装、搬运引流、冒充作者，或使用作者身份与二维码制造官方授权假象。违规内容可能被要求下架；作者可暂停更新、归档或删除仓库及相关 Release。

本项目仓库、脚本、部署说明和 Release 下载始终免费公开。未经作者明确书面许可，禁止将本项目包装为付费资源、内部版、独家版、会员权益、收费课程、付费部署或包更新服务；禁止搬运到其他账号、群组、频道、网盘、电商或付费平台进行涨粉、截流、倒卖和引流；禁止删除作者与版权信息后冒充原创；禁止使用作者昵称、头像、二维码和项目名称制造官方授权假象。

> 如需商业合作、品牌授权、联合分发或使用作者名义提供付费服务，请先取得作者明确书面授权。完整规则、收款码防诈骗说明和违规处理方式见 **[NOTICE.md](NOTICE.md)**。

> 官方仓库和 Release 始终免费。第三方以“下载费 / 激活费 / 内部版 / 代部署 / 会员门槛”等名义收费，均与作者无关，请停止付款并保留证据。

> 对上述违规行为，作者有权要求立即停止传播、删除内容并下架相关商品或页面；并可视情况暂停更新、归档或删除本仓库及相关 Release、向平台投诉或采取进一步必要措施。

---

## ✨ 30 秒速览

| 维度 | 说明 |
| :--- | :--- |
| **用途** | 领取库库 AI「免费领积分」活动中的每日登录与完成一次对话奖励。 |
| **输入** | 单账号 `KUKU_COOKIES` + 可选 `KUKU_STOKEN`，或多账号 `KUKU_TOKENS`。 |
| **输出** | 分账号领取结果、奖励积分摘要，以及可选的企业微信 / PushPlus 推送。 |
| **部署** | 青龙面板、GitHub Actions、Windows / Linux 本地运行。 |
| **依赖** | Python 3.8+，仅使用标准库，无需安装第三方包。 |
| **成功判据** | 任务接口返回有效奖励；当天已领取时按幂等结果处理，不把重复运行误报成新增积分。 |

## ✨ 核心能力

- **双任务领取**：每天执行 `LOGIN` 与 `CHAT` 两个活动任务。
- **幂等识别**：当天已领取时接收 `reward_point=0`，按「今日已领」处理。
- **多账号支持**：单账号使用 `KUKU_COOKIES`，多账号使用 `KUKU_TOKENS`。
- **令牌分层**：优先使用配置的 STOKEN，其次使用本机缓存，最后用纯签名算法自动换发。
- **跨平台运行**：MD5 签名换发不依赖 DLL，Windows、Linux、Docker 与青龙都能执行。
- **日志脱敏**：只展示 BDUSS 尾部片段，避免完整 Cookie 出现在日志里。
- **可选推送**：支持企业微信机器人与 PushPlus。

## 🔑 获取凭据

业务接口需要作用域为 `genflowpro` 的会话令牌。仅携带网页 Cookie 时，通用接口可能正常，但任务接口会报未登录。当前 `v1.2.0` 代码复刻了官方引擎的 MD5 签名，换发只需 `BDUSS` 与 `PTOKEN`，不依赖 `genflowengine.dll`。

| 步骤 | 运行位置 | 操作 |
| :--- | :--- | :--- |
| **1. 获取 Cookie** | 任意平台 | 浏览器登录后复制完整 Cookie，或在已登录客户端所在电脑读取本机登录态。 |
| **2. 换发 STOKEN** | 任意平台 | 手动粘贴 Cookie 时运行 `python kuku_get_cookie.py --paste --exchange`；本机客户端可读时运行 `python kuku_get_cookie.py --exchange`。 |
| **3. 每日签到** | 青龙 / Linux / Windows | 配置 `KUKU_COOKIES`；可预先填写 `KUKU_STOKEN`，也可由主脚本自动换发。 |

```bash
python kuku_get_cookie.py            # 读取本机客户端登录态
python kuku_get_cookie.py --paste    # 手动粘贴 Cookie
python kuku_get_cookie.py --exchange # 读取本机客户端后换发 STOKEN
python kuku_get_cookie.py --paste --exchange # 手动 Cookie 纯签名换发
python kuku_daily.py --token         # 直接为已配置账号换发并打印 STOKEN
```

`kuku_get_cookie.py` 还支持 `--stoken` 直接给出已有令牌。默认读取本机客户端 Cookie 数据库时会复制一份再读，客户端正在运行也可以尝试读取。

> [!IMPORTANT]
> 换发 STOKEN 不再要求在本机安装客户端。只要能提供包含 `BDUSS` 与 `PTOKEN` 的完整 Cookie，就可在青龙或 Linux 上直接换发。

## 🚀 青龙面板

1. 将 `kuku_daily.py` 上传到青龙脚本目录。
2. 在「环境变量」中添加 `KUKU_COOKIES` 和 `KUKU_STOKEN`；多账号改用 `KUKU_TOKENS`。
3. 新建定时任务，从脚本列表选择 `kuku_daily.py`，让面板生成 `task kuku_daily.py` 命令。

```cron
15 8 * * *
```

```bash
task kuku_daily.py
```

青龙用面板本地时间解释 cron。通过裸 `python` 启动时，面板环境变量不一定会注入，因此定时任务优先使用青龙运行器。

## 🚀 GitHub Actions

仓库内置 [`.github/workflows/daily.yml`](.github/workflows/daily.yml)，当前默认只保留 `workflow_dispatch` 手动触发。Fork 或导入后，在仓库 Secrets 中配置：

| Secret | 必填 | 说明 |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | 单账号 | 单账号 Cookie。 |
| `KUKU_STOKEN` | ➖ | 与单账号 Cookie 配套的会话令牌。 |
| `KUKU_TOKENS` | 多账号 | 多账号条目，配置后优先于单账号变量。 |
| `QYWX_TOKEN` | ➖ | 企业微信机器人 key。 |
| `PLUSPLUS_TOKEN` | ➖ | PushPlus token。 |

进入 **Actions → KukuAI Daily → Run workflow** 手动验证。需要云端定时时，自行取消工作流中这两行的注释：

```yaml
schedule:
  - cron: '15 0 * * *'
```

`15 0 * * *` 使用 UTC，对应北京时间每天 08:15。Actions 的 Ubuntu runner 可以执行纯签名换发；`KUKU_STOKEN` 可省略，由 `KUKU_COOKIES` 在运行时自动换取并写入缓存。

## 🔧 环境变量

| 变量 | 必填 | 说明 |
| :--- | :---: | :--- |
| `KUKU_COOKIES` | 单账号 ✅ | Cookie 头、Cookie 编辑器 JSON，或包含 `BDUSS` / `PTOKEN` 的对象。 |
| `KUKU_STOKEN` | ➖ | 已换发的 `genflowpro` 会话令牌。 |
| `KUKU_TOKENS` | 多账号 ✅ | 多账号，换行或 `&` 分隔；每条为 `备注\|BDUSS\|PTOKEN[\|STOKEN]`。 |
| `KUKU_PROXY` | ➖ | `http://`、`https://` 或 `socks5://` 代理地址。 |
| `KUKU_NO_NOTIFY` | ➖ | 设为 `1` 时关闭推送。 |
| `QYWX_TOKEN` | ➖ | 企业微信机器人 key；也兼容 `WECHAT_WEBHOOK`。 |
| `PLUSPLUS_TOKEN` | ➖ | PushPlus token。 |

多账号示例：

```text
主号|BDUSS_VALUE|PTOKEN_VALUE|STOKEN_VALUE
副号|BDUSS_VALUE|PTOKEN_VALUE|STOKEN_VALUE
```

## ⌨️ 命令行参数

| 参数 | 作用 |
| :--- | :--- |
| （无） | 运行所有已配置账号的每日任务。 |
| `--only N` | 只运行第 N 个账号。 |
| `--token` | 只换发并输出会话令牌，不执行签到。 |

| 登录工具参数 | 作用 |
| :--- | :--- |
| `--paste` | 手动粘贴 Cookie。 |
| `--exchange` | 用纯 MD5 签名换发 STOKEN。 |
| `--stoken VALUE` | 直接使用指定会话令牌。 |

## 🧪 验证范围

- 旧版 README 记录的 13 项离线自测覆盖 Cookie 解析、请求头拼装、令牌优先级、签到成功 / 幂等 / 会话失效 / HTTP 失败分支、多账号解析和日志脱敏。
- `v1.2.0` 的令牌换发改为官方引擎同款 MD5 签名，任意平台可执行，且不再调用 `genflowengine.dll`。
- 当前仓库没有附带 `v1.2.0` 真实账号端到端联网日志，因此 README 不宣称该链路已经完成线上验收。

## 🗂️ 数据与缓存

| 文件 | 内容 | 是否提交 |
| :--- | :--- | :---: |
| `.kuku_stoken.json` | 本机换发得到的会话令牌缓存 | ❌ 已忽略 |
| `kuku_tokens.json` | 可能的账号状态文件 | ❌ 已忽略 |
| `storage.json` / `*accounts*.json` | 本地登录态或账号数据 | ❌ 已忽略 |
| `*.log` | 运行日志 | ❌ 已忽略 |

## 🔒 隐私说明

- 脚本不收集、不上传额外的账号信息，请求直达库库 AI 官方接口。
- Cookie、STOKEN 与多账号数据只从环境变量或本地缓存读取。
- 日志只打印脱敏后的 BDUSS 片段。
- 不要把 Cookie、STOKEN、`.kuku_stoken.json` 或环境变量内容提交到仓库、Issue 或公开构建日志。

## 🔁 成功与幂等语义

- 命中有效奖励时，输出每个任务实际获得的积分。
- 当天已经领取时，业务回执中的 `reward_point=0` 会被识别为「今日已领」。
- 活动未开始、未投放或没有可领取任务时，输出中性说明，不虚构新增积分。
- 当所有已运行账号都未能返回有效结果时，进程以非零状态退出，便于青龙和 Actions 识别异常。

## ❓ 常见问题

<details>
<summary><b>出现 errno=-6，任务面板不可读</b></summary>

STOKEN 缺失或已经失效。可以手动粘贴 Cookie 重新换发：

```bash
python kuku_get_cookie.py --paste --exchange
```

然后把新的 `KUKU_STOKEN` 写入环境变量；主脚本在 `KUKU_STOKEN` 为空时也会尝试自动换发。
</details>

<details>
<summary><b>换发 STOKEN 是否必须安装 Windows 客户端</b></summary>

不需要。当前实现用 `BDUSS` + `PTOKEN` 做纯 MD5 签名换发，任意平台都可执行。客户端只用于默认读取本机已登录 Cookie 数据库。
</details>

<details>
<summary><b>只有网页 Cookie，没有 PTOKEN</b></summary>

换发会话令牌需要完整的 `BDUSS` 与 `PTOKEN`。请重新登录并复制完整 Cookie，确认两个字段都存在。
</details>

<details>
<summary><b>多账号为什么优先使用 KUKU_TOKENS</b></summary>

脚本检测到非空的 `KUKU_TOKENS` 后会直接按多账号列表运行；单账号 `KUKU_COOKIES` / `KUKU_STOKEN` 作为未配置多账号时的路径。
</details>

## 📦 版本与发布
- 当前发布版：`v1.2.1`（2026-11-04，文档发行版；脚本逻辑仍为 `v1.2.0`）。

- 当前仓库版本：`v1.2.0`。
- Release 页：[L0NE-6/KukuAI-Daily Releases](https://github.com/L0NE-6/KukuAI-Daily/releases)。
- 更新记录见 [CHANGELOG.md](CHANGELOG.md)。

## ⚠️ 免责声明

本项目用于个人学习与自动化实践。请自行遵守库库 AI、百度文库及相关服务的条款，并承担账号使用风险。

## ☕ 支持与反馈

脚本免费、无广告、无功能限制。遇到问题时，请提交 [Issue](https://github.com/L0NE-6/KukuAI-Daily/issues)，附上脱敏日志、复现步骤和运行环境；发现改进点也欢迎发起 [Pull Request](https://github.com/L0NE-6/KukuAI-Daily/pulls)。

如果这个项目节省了你的时间，可以自愿扫码支持；点 Star、补充文档或反馈真实运行结果同样重要。

<p align="center">
  <img src="assets/donate-wechat.png" width="260" alt="微信赞赏码" />
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/donate-alipay.jpg" width="260" alt="支付宝赞赏码" />
</p>
<p align="center"><sub>💚 微信支付（左） &nbsp;|&nbsp; 💙 支付宝（右，支持信用卡 / 花呗）</sub></p>

> ⚠️ 收款码仅用于向作者自愿赞赏。任何第三方以代下载、代部署、内部资源或会员群为由收费，均与作者无关，请停止付款并保留证据。

---

## ✦ 星轨 Star Trail

> 每颗 Star 都像一次新的会话。它们不替代成功日志，却让这段日常自动化路径更容易被后来者找到。

<a href="https://star-history.com/#L0NE-6/KukuAI-Daily&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=L0NE-6/KukuAI-Daily&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=L0NE-6/KukuAI-Daily&type=Date&theme=light" />
    <img alt="KukuAI Daily Star Trail" src="https://api.star-history.com/svg?repos=L0NE-6/KukuAI-Daily&type=Date&theme=light" />
  </picture>
</a>

---

<div align="center">
  <a href="https://github.com/L0NE-6/KukuAI-Daily/releases">Releases</a> ·
  <a href="https://github.com/L0NE-6/KukuAI-Daily/issues">Issues</a> ·
  <a href="https://github.com/L0NE-6/KukuAI-Daily">Star</a>
  <br />
  <sub>L0NE-6 · DAILY SIGNAL · 让每一次运行都留下可验证的信号</sub>
</div>
