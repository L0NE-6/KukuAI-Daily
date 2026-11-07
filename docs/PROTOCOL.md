# KukuAI kukuai30 签到协议证据

## 基线

- 本项目版本：`v1.4.0`
- 上游仓库：`watchern/Agent2Providers`
- 上游 release：`v3.4.2.1`
- 上游 commit：`5d2b55bc59d9dc5da214d2bff4c09e5679d77414`
- 证据文件：`crates/providers/src/providers/kuku/{tasks,credentials,session}.rs`
- 使用方式：只读取公开 HTTP 契约与字段语义；本项目为独立 Python 实现。

## 现行链路

```text
GET  /api/genflowpro/common/userreport?clienttype=400&app_id=123971023&web=1&channel=chunlei&version=1.4.4
POST /act/v2/kukuai30/homepage?uid=<uk>&tid=291651792210&<client-query>
POST /act/v2/kukuai30/signin?uid=<uk>&tid=291651792210&<client-query>
POST /act/v2/kukuai30/homepage?uid=<uk>&tid=291651792210&<client-query>
```

固定客户端参数：

```text
app_id=123971023
clienttype=401
version=1.7.3.107
channel=chunlei
tid=291651792210
```

`uid` 不是 Cookie 字段；它来自 `userreport.data.uk`，支持字符串或整数。

## 请求形态

```http
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) KuKuGenFlow/1.6.32 Chrome/146.0.7680.216 Electron/41.10.1 Safari/537.36
Referer: https://kuku.baidu.com/genflowpro
Origin: https://kuku.baidu.com
Accept-Language: zh-CN,zh;q=0.9
Accept: application/json
Content-Type: application/json
Cookie: BDUSS=...; STOKEN=<business-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...; gfprotpl=genflowpro
```

homepage 与 signin 都是 JSON POST，请求体固定为：

```json
{}
```

不存在 `getJsToken`、`activityTid`、`aid=15459` 或 `jsToken` 参数。

## 会话与 STOKEN

1. Cookie 中存在 `PTOKEN` 时，使用 `BDUSS + PTOKEN` 换发 `genflowpro` 业务 STOKEN。
2. 换发失败直接报错，不静默沿用旧令牌。
3. 没有 `PTOKEN` 时，允许使用完整 Cookie 中的 `STOKEN` 读取 `userreport`。
4. 两者都没有时，本地直接报“缺少可用会话令牌”。
5. `KUKU_STOKEN` / `business_stoken` 仍只供显式 `--legacy-freepoint` 和 `--token` 使用。

`userreport` 必须同时满足：

- HTTP 200
- `errno=0`
- `data.bdstoken` 非空
- `data.uk` 是非布尔字符串或整数，且非空

## 成功判据

签到前面板：

- `signed_today is true`：返回“今日已签到”，不发送 signin。
- 其他值：继续发送一次 signin。

signin 动作响应不是最终成功依据。脚本保存其中的 `errno / show_msg / errmsg / message` 作为拒绝原因，等待 `0.9s` 后再次读取 homepage。

| 签到后 homepage | 结论 |
| :--- | :--- |
| `signed_today is true` | 本次签到成功 |
| `signed_today is false` | 失败 |
| 缺 `signed_today` | 失败 |
| 外层 `errno != 0`、缺 `data`、HTTP 非 200 | 失败 |

动作返回 `errno=10152` 不能覆盖复读结果。动作返回 `errno=8001` 且复读仍为 false 时，错误消息保留服务端原文，例如“账号异常，无法参与活动”。

## 多账号

推荐每账号保存完整 Cookie：

```json
[
  {
    "name": "main",
    "cookie": "BDUSS=...; PTOKEN=...; STOKEN=...; BAIDUID=...; PANPSC=...",
    "business_stoken": ""
  }
]
```

默认签到只使用 `cookie` 与换发结果；`business_stoken` 不参与 `kukuai30` 请求头构造。

## 未采用项

- 不把动作响应 HTTP 200 当成功。
- 不把动作 `errno=0` 当成功。
- 不把 `errno=10152` 当成功。
- 不复用已经退役的 `getJsToken` 链路。
- 不在 `kukuai30` 失败时自动切换到旧 freepoint。
- 不生成空 `uid=` 请求。
