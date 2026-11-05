# KukuAI 30 天签到协议证据

## 基线

- 本项目版本：`v1.3.0`
- 仓库：`ProvidersPlugin/Agent2Providers`
- tag：`v3.4.2`
- commit：`3055f416841c1393ec04294a702603fd41e840aa`
- tag 时间：`2026-11-05T16:38:49+08:00`
- 使用方式：只读 Rust 文件作为 HTTP 契约证据，不复制源码、注释或内部抽象。

上游证据文件：

- `crates/providers/src/providers/kuku/checkin.rs`
- `crates/providers/src/providers/kuku/credentials.rs`
- `crates/providers/src/providers/kuku/mod.rs`

## 主签到链路

| 顺序 | 方法 | 路径 | 用途 |
| :---: | :--- | :--- | :--- |
| 1 | `GET` | `/act/api/conf?conf_key=kukuSignConf` | 读取 `activityTid` 与 `signPoint` |
| 2 | `GET` | `/act/v2/kukuai30/homepage?tid=<activityTid>` | 读取 `signed_today`、连续天数、累计天数 |
| 3 | `GET` | `/operation/activitys/api/getJsToken` | 获取风控 JS token |
| 4 | `POST` | `/act/v2/kukuai30/signin?tid=<activityTid>&jsToken=<token>&aid=15459` | 提交签到 |

根地址：

```text
https://kuku.baidu.com
```

固定请求头：

```http
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36
Referer: https://kuku.baidu.com/operation/activitys/kukuPcSignAct/main
Origin: https://kuku.baidu.com
Accept-Language: zh-CN,zh;q=0.9
Cookie: BDUSS=...; STOKEN=<网页STOKEN>; PTOKEN=...; BAIDUID=...; PANPSC=...; gfprotpl=genflowpro
```

签到 POST 使用空表单 body，`Content-Type` 为：

```text
application/x-www-form-urlencoded;charset=UTF-8
```

## 双 STOKEN 边界

`checkin.rs` 先取得账号 Cookie 快照，然后直接执行 `signin_thirty_days(&credentials)`。只有在 30 天链路不可用并进入旧 freepoint 分支后，代码才调用 `with_business_stoken(&credentials)`。

上游 v3.4.2 会把旧任务作为自动备用路径；本项目为青龙/Actions 的确定性验收口径，改为只允许显式 `--legacy-freepoint` 进入旧链路，默认流程不自动回退。

因此本项目固定两条边界：

| 链路 | Cookie | STOKEN |
| :--- | :--- | :--- |
| 30 天签到 | 完整网页 Cookie | Cookie 内网页 `STOKEN` |
| 旧 freepoint | 业务请求 Cookie | `KUKU_STOKEN` / 多账号 `business_stoken` / 换发结果 |

实现约束：

- `KUKU_STOKEN` 是业务 STOKEN，不覆盖 Cookie 内网页 `STOKEN`。
- 30 天链路缺少网页 `STOKEN` 时明确失败，提示重新导出完整 Cookie。
- 30 天链路不读取本机业务 STOKEN 缓存。
- `PTOKEN`、`BAIDUID`、`PANPSC` 等同一会话 Cookie 字段保留在网页 Cookie 中。
- 旧 freepoint 只在 `--legacy-freepoint` 显式启用。

## 活动配置

响应读取：

```json
{
  "data": [
    {
      "conf_value": {
        "activityTid": "73001",
        "signPoint": 10
      }
    }
  ]
}
```

规则：

- `activityTid` 接受字符串或整数。
- `signPoint` 接受整数或十进制字符串。
- `signPoint` 缺失时仅用于展示默认 `10`，不影响签到成功判据。

## 风控 Token

`getJsToken` 的有效值位于：

```text
data.jsToken
```

实际内容是 URL 编码的 JS 片段：

```text
function fn(a){...};fn("HEX_TOKEN")
```

本项目只做 `%XX` 解码并取最后一对双引号中的值，不执行 JavaScript。

## 成功与中性判据

签到响应示例：

```json
{
  "errno": 0,
  "data": {
    "continuous": 3,
    "signed_today": true
  }
}
```

| 条件 | 本地结论 |
| :--- | :--- |
| `errno=0` 且 `data.signed_today is true` | 唯一签到成功 |
| 首页 `data.signed_today is true` | 中性完成，不再请求 token / POST |
| `errno=10152` | 中性完成，今日已签 |
| `errno=8001` | 风控失败 |
| `errno=8002` | 风控失败 |
| `errno=0` 但缺少 `signed_today` | 失败 |
| `errno=0` 但 `signed_today=false` 或非布尔值 | 失败 |
| 其它 `errno` | 失败 |

HTTP 200 不能单独作为成功证据。

## 多账号 Cookie

推荐每账号保存完整 Cookie：

```json
[
  {
    "name": "main",
    "cookie": "BDUSS=...; STOKEN=<web-stoken>; PTOKEN=...; BAIDUID=...; PANPSC=...",
    "business_stoken": ""
  }
]
```

业务 STOKEN 只在 `--legacy-freepoint` 或 `--token` 模式读取，不参与 30 天链路的请求头构造。

## 未采用项

- 不把 `errno=0` 单独当成成功。
- 不把缺省 `signed_today` 当成 `true`。
- 不让 `KUKU_STOKEN` 替代网页 STOKEN。
- 不在 30 天链路失败时自动切到旧 freepoint。
- 不把 HTTP 状态码代替业务响应判据。
