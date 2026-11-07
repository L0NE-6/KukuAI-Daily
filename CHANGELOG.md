# 更新日志

## v1.4.0（2026-11-07）

- 签到主链路迁移到现行 `kukuai30`：`userreport` 获取 `uk` → homepage 预读 → 按需 signin → homepage 复读。
- 固定签到活动 `tid=291651792210`，对齐客户端 `1.7.3.107` query、`KuKuGenFlow/1.6.32` User-Agent、`/genflowpro` Referer 与 JSON 空对象 body。
- 成功判据改为唯一可信的签到后 homepage `signed_today=true`；动作 `errno=0`、HTTP 200 或 `errno=10152` 都不能单独代表成功。
- `errno=8001` 等拒绝原因在复读仍为 `signed_today=false` 时如实透出，不再伪装成“今日已签到”。
- 退役 `getJsToken`、`activityTid`、`aid=15459` 与 `jsToken` 主链路；旧 freepoint 仍需显式 `--legacy-freepoint`。
- `PTOKEN` 存在时先换发 `genflowpro` 业务 STOKEN；换发失败、缺 `uk`、缺 `bdstoken` 或面板外层 `errno` 异常均在错误请求前明确终止。
- 六语文档与协议证据同步到 `watchern/Agent2Providers` `v3.4.2.1` / commit `5d2b55b`。
- 验证：unittest、pytest、py_compile、ruff、YAML、diff-check 与敏感扫描；全部使用假响应，不含真实账号 Cookie。

## v1.3.0（2026-11-05）

- 主链路切换到「库库 30 天签到」：活动配置 → 活动首页 → `getJsToken` → 签到，固定活动页 Referer 与 `aid=15459`。
- 成功判据收紧为 `errno=0` 且 `data.signed_today=true`；`10152` 中性完成，`8001` / `8002` 风控失败，缺省 `signed_today` 不再视为成功。
- 旧 freepoint 改为仅显式 `--legacy-freepoint` 运行，不再自动兜底。
- 拆分网页 STOKEN 与旧 freepoint 业务 STOKEN：`KUKU_STOKEN` 只供 legacy，不再覆盖 Cookie 内网页 STOKEN；缺少网页 STOKEN 时明确提示重新导出 Cookie。
- `KUKU_TOKENS` 支持 JSON 数组与完整 Cookie 行格式，保留 `PTOKEN`、`BAIDUID`、`PANPSC` 及其它 Cookie 字段。
- `kuku_get_cookie.py` 读取客户端 Cookie 时保留百度域完整登录态，并明确标注输出的是 legacy 业务 STOKEN。
- 新增六语文档与 `docs/PROTOCOL.md`，补充协议证据、成功判据、双 STOKEN 边界和多账号格式。
- 验证：unittest、pytest、py_compile、ruff、YAML、diff-check 与敏感扫描；全部使用假响应，不含真实账号 Cookie。

## v1.2.1（2026-11-04）

- 文档发行版：同步首屏使用边界、反收费/反搬运声明、`NOTICE.md`、微信/支付宝赞赏码防诈骗提醒与六语导航。
- Release 完整包现在包含最新 README、NOTICE、docs 与图片资产；签到/领取主逻辑未变更，脚本版本仍为 `v1.2.0`。
- 验证：Markdown 渲染、相对链接、二维码资产与发布包清单检查通过；本版未使用真实账号执行签到。

## v1.1.0（2026-10-13）

- 文档补齐：README 新增「☕ 支持与投喂」板块（微信 / 支付宝收款码）与「🔒 隐私说明」完善。
- 新增：`assets/` 收款码素材、`requirements.txt`（说明实际零第三方依赖）。

## v1.0.0（2026-10-10）

- 首个公开版本：库库 AI「免费领积分」每日任务领取（每日登录 / 完成一次对话）；
- 任务接口幂等处理：当天已领过按「今日已领」处理，不重复报错；
- 会话令牌分层：配置 > 本机缓存 > 本机换发（换发需 Windows + 官方客户端引擎）；
- 配套 `kuku_get_cookie.py`：读本机客户端登录态 / 手动粘贴 / 换发会话令牌；
- 多账号、代理、企业微信与 PushPlus 推送、日志脱敏。
