<div align="center">

# 🧩 KukuAI Daily

**库库 AI（百度文库 GenFlowPro）每日签到 · 单文件青龙脚本 · 多账号**

<img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/%E9%9D%92%E9%BE%99%E9%9D%A2%E6%9D%BF-%E5%8D%95%E6%96%87%E4%BB%B6%E8%BF%90%E8%A1%8C-4EAA25?style=flat-square" />
<img src="https://img.shields.io/badge/License-MIT-F472B6?style=flat-square" />

</div>

---

## ✨ 这是什么

一个脚本完成库库 AI「免费领积分」活动的每日任务领取：

- **每日登录**（`LOGIN`）
- **完成一次对话**（`CHAT`）

任务接口是幂等的：当天已经领过会返回 `reward_point=0`，脚本按「今日已领」处理，不会重复报错。

---

## ⚠️ 先看这条：令牌换发需要在 Windows 上做一次

业务接口要的不是网页登录那份 Cookie，而是一个**按产品签发的会话令牌**（作用域 `genflowpro`）。
只带网页 Cookie 去调业务接口，一律被判「未登录」（`errno=-6`）；余额这类通用接口却正常，
所以症状通常是「能查余额、任务面板打不开」。

这个令牌只能借官方客户端的本地引擎（`genflowengine.dll`）换出来，因此：

| 步骤 | 在哪台机器 | 说明 |
| :--- | :--- | :--- |
| 取 Cookie | 任意 | 浏览器登录后复制，或用本机客户端导入 |
| **换发会话令牌** | **Windows + 已装库库 AI 客户端** | 跑一次 `kuku_get_cookie.py --exchange` |
| 每日签到 | 任意（青龙 / Linux / Windows） | 把令牌填进环境变量即可长期使用 |

> Linux / Docker 上没有这个引擎，脚本会如实提示「需要 Windows 换发」，
> 不会把失败伪装成签到成功。

---

## 🚀 快速开始

### 1. 拿 Cookie

在浏览器登录 <https://kuku.baidu.com/genflowpro>，开发者工具 → Network → 复制完整 Cookie；
或在一台装了库库 AI 客户端的 Windows 上直接读本机登录态：

```bash
python kuku_get_cookie.py            # 读客户端登录态（客户端需先完全退出）
python kuku_get_cookie.py --paste    # 或手动粘贴 Cookie
```

### 2. 换发会话令牌（Windows）

```bash
python kuku_get_cookie.py --exchange
# 输出：KUKU_STOKEN=…
```

### 3. 配置环境变量（青龙）

| 变量 | 必填 | 说明 |
| :--- | :--- | :--- |
| `KUKU_COOKIES` | ✅ | Cookie 头 / Cookie 编辑器 JSON / `{BDUSS,PTOKEN}` 对象都认 |
| `KUKU_STOKEN` | ➖ | 换发好的会话令牌；不填则脚本在本机尝试自动换发（需 Windows） |
| `KUKU_TOKENS` | ➖ | 多账号：每行 `备注\|BDUSS\|PTOKEN[\|STOKEN]`，换行或 `&` 分隔 |
| `KUKU_ENGINE_DLL` | ➖ | 显式指定 `genflowengine.dll` 路径（自动定位失败时用） |
| `KUKU_PROXY` | ➖ | 代理，如 `http://127.0.0.1:7890` |
| `KUKU_NO_NOTIFY` | ➖ | 设 `1` 关闭推送 |
| `QYWX_TOKEN` | ➖ | 企业微信机器人（也兼容 `WECHAT_WEBHOOK`） |
| `PLUSPLUS_TOKEN` | ➖ | PushPlus |

### 4. 定时任务

```cron
15 8 * * * python kuku_daily.py
```

---

## 🧪 验证情况

- 13 项离线自测通过：Cookie 三形态解析、请求头拼装、令牌优先级（配置 > 缓存 > 换发）、
  签到成功 / 幂等 / 会话失效 / HTTP 失败分支、多账号解析、日志脱敏。
- 换发链路依赖官方引擎，需在装有客户端的 Windows 上实测（脚本会在不支持的环境给出明确提示，不会静默失败）。

---

## 🛠 常见问题

<details>
<summary><b>提示 errno=-6 / 任务面板不可读</b></summary>

会话令牌失效或缺失。在 Windows 上重新跑 `kuku_get_cookie.py --exchange`，
把新的 `KUKU_STOKEN` 更新到环境变量。
</details>

<details>
<summary><b>提示「换发会话令牌需要在 Windows 上运行」</b></summary>

这是真话，不是脚本偷懒：换发必须调用官方客户端的本地引擎。
在装客户端的 Windows 上换一次，令牌可以直接复制到青龙用。
</details>

<details>
<summary><b>能不能用手机端 Cookie？</b></summary>

不行。手机端登录态与桌面端不是同一条会话链，业务接口不认。
</details>

---

## 🔒 隐私说明

- 脚本不收集、不上传任何信息，所有请求直达官方接口；
- Cookie / 令牌只从环境变量读取，或在脚本同目录的 `.kuku_stoken.json` 缓存（已加 `.gitignore`）；
- 日志里只打印 BDUSS 的尾 4 位，不会输出完整凭据。

---

## ☕ 支持与投喂

脚本是**完全免费、无广告、无任何功能限制**的（本仓库与发布包也不含你的任何数据）。
如果它确实帮你省了时间、多领了积分，欢迎请我喝杯咖啡 —— **纯自愿，不影响任何功能**，也不会影响我在 Issue 里的响应速度 🙌

<p align="center">
  <img src="assets/donate-wechat.png" width="260" alt="微信赞赏码" />
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/donate-alipay.jpg" width="260" alt="支付宝收款码" />
</p>
<p align="center"><sub>💚 微信支付（左） &nbsp;|&nbsp; 💙 支付宝（右，支持信用卡 / 花呗）</sub></p>

> 💡 **不花钱也能帮上很多忙**：点个 ⭐ Star、提一个带日志的 Issue、发一个 Pull Request、或者把脚本分享给需要的朋友 —— 这些同样是最好的支持。

---

## 📄 License

MIT