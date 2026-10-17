#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KukuAI（百度文库 · 库库 AI / GenFlowPro）每日签到 —— 单文件青龙脚本

做什么：
  · 领取「免费领积分」活动的每日任务奖励：每日登录（LOGIN）+ 完成一次对话（CHAT）
  · 任务接口幂等：重复领取返回 reward_point=0，不算失败

前置条件（重要）：
  · 业务接口需要一个按产品签发的会话令牌（STOKEN，作用域 genflowpro）。
    网页登录拿到的 Cookie 里那份是通行证级的，业务接口会判未登录（errno=-6）。
    本脚本用**纯算法**换发（复刻官方引擎的 MD5 签名）—— 不再依赖
    genflowengine.dll，Windows / Linux / 青龙都能直接换发。

环境变量：
  KUKU_COOKIES     必填。Cookie 头（`BDUSS=…; PTOKEN=…`）、Cookie 编辑器 JSON、
                   或 {"BDUSS":"…","PTOKEN":"…"} 对象都认。
  KUKU_STOKEN      可选。已换发好的 genflowpro 会话令牌；没有则本机尝试自动换发。
  KUKU_TOKENS      可选。多账号，换行或 & 分隔，每条形如 `备注|BDUSS|PTOKEN[|STOKEN]`。
  KUKU_PROXY       可选。http(s)/socks5 代理，例如 http://127.0.0.1:7890
  KUKU_NO_NOTIFY   可选。设 1 关闭推送。

推送：企业微信机器人（QYWX_TOKEN / WECHAT_WEBHOOK）/ PushPlus（PLUSPLUS_TOKEN），
      配了哪个推哪个；都没有则只打印。

用法：
  python kuku_daily.py            # 全部账号
  python kuku_daily.py --only 1   # 只跑第 1 个
  python kuku_daily.py --token    # 只尝试换发并打印令牌（任意平台）

依赖：Python 3.8+，仅标准库。
"""

import json
import hashlib
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

BASE_URL = "https://kuku.baidu.com"
PASSPORT_AUTH_URL = "https://passport.baidu.com/v3/login/api/auth"
WEB_QUERY = ("clienttype=400&app_id=123971023&web=1&channel=chunlei&version=1.4.4")
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36")
ENGINE_DLL_NAME = "genflowengine.dll"
# 官方引擎内置签名密钥（真实 DLL 与抓包双重验证）
ENGINE_SIGN_KEY = "34868b316de55815273b2616954b0286"
# passport 换发接口对客户端引擎 UA 敏感，浏览器 UA 不可靠
ENGINE_UA = "genflow;1.6.5;PC;PC-Windows;10.0.26200;GenFlowPro"
DAILY_TASKS = (("LOGIN", "每日登录"), ("CHAT", "完成一次对话"))
STOKEN_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".kuku_stoken.json")
MIN_BDUSS_LEN = 8


# ────────────────────────── 通用 ──────────────────────────
def log(msg):
    print(msg, flush=True)


def mask(value):
    """脱敏：只留尾 4 位。"""
    v = str(value or "")
    return ("*" * max(0, len(v) - 4)) + v[-4:] if len(v) > 4 else "*" * len(v)


def http(method, url, headers=None, body=None, timeout=30):
    """返回 (status, text)。网络错误返回 (-1, 错误串)。"""
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, str(e)


def proxy_opener():
    """按 KUKU_PROXY 建一个 opener；未配置返回 None。"""
    url = os.getenv("KUKU_PROXY", "").strip()
    if not url:
        return None
    return urllib.request.build_opener(urllib.request.ProxyHandler({"http": url, "https": url}))


# ────────────────────────── Cookie 解析 ──────────────────────────
def _pairs_from_header(text):
    out = []
    for seg in str(text).split(";"):
        if "=" not in seg:
            continue
        name, value = seg.split("=", 1)
        name, value = name.strip(), value.strip()
        if name and value:
            out.append((name, value))
    return out


def _pairs_from_json(raw):
    pairs = []
    try:
        data = json.loads(raw)
    except Exception:
        return pairs
    if isinstance(data, dict):
        if isinstance(data.get("cookies"), list):
            data = data["cookies"]
        elif isinstance(data.get("cookie"), (dict, list)):
            data = data["cookie"]
        else:
            items = []
            for k, v in data.items():
                if isinstance(v, str) and v.strip():
                    items.append((k, v.strip()))
            return items
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or item.get("Name") or "").strip()
            value = str(item.get("value") or item.get("Value") or "").strip()
            if name and value:
                pairs.append((name, value))
    return pairs


def parse_cookie(raw):
    """把各种形态的 Cookie 归一到 (bduss, ptoken, extras)。"""
    raw = (raw or "").strip()
    pairs = _pairs_from_json(raw) if raw[:1] in "[{" else []
    if not pairs:
        pairs = _pairs_from_header(raw)
    bduss = ptoken = ""
    extras = []
    seen = set()
    for name, value in pairs:
        low = name.lower()
        if low == "bduss":
            bduss = value
        elif low == "ptoken":
            ptoken = value
        elif low not in ("gfprotpl", "stoken"):
            if low not in seen:
                seen.add(low)
                extras.append((name, value))
    return bduss, ptoken, extras


def cookie_header(bduss, stoken, extras):
    parts = ["BDUSS=" + bduss]
    if stoken:
        parts.append("STOKEN=" + stoken)
    for name, value in extras:
        parts.append("%s=%s" % (name, value))
    parts.append("gfprotpl=genflowpro")
    return "; ".join(parts)


def request_headers(bduss, stoken, extras):
    return {
        "Cookie": cookie_header(bduss, stoken, extras),
        "User-Agent": USER_AGENT,
        "Referer": BASE_URL + "/genflowpro",
        "Origin": BASE_URL,
        "Accept-Language": "zh-CN,zh;q=0.9",
    }


# ────────────────────────── 引擎 DLL（仅 Windows） ──────────────────────────
def find_engine_dll():
    """定位 genflowengine.dll：环境变量 → 注册表卸载项 → 常见安装目录。"""
    explicit = os.getenv("KUKU_ENGINE_DLL", "").strip() or os.getenv("WORKBUDDY_GENFLOW_ENGINE_DLL", "").strip()
    if explicit and os.path.isfile(explicit):
        return explicit
    if sys.platform != "win32":
        return ""
    try:
        import winreg
        hives = (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER)
        prefixes = (
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        )
        for hive in hives:
            for prefix in prefixes:
                try:
                    root = winreg.OpenKey(hive, prefix)
                except OSError:
                    continue
                try:
                    index = 0
                    while True:
                        try:
                            sub_name = winreg.EnumKey(root, index)
                        except OSError:
                            break
                        index += 1
                        try:
                            sub = winreg.OpenKey(root, sub_name)
                        except OSError:
                            continue
                        try:
                            for value_name in ("InstallLocation", "DisplayIcon"):
                                try:
                                    value, _ = winreg.QueryValueEx(sub, value_name)
                                except OSError:
                                    continue
                                path = str(value).split(",")[0].strip()
                                directory = path if os.path.isdir(path) else os.path.dirname(path)
                                candidate = os.path.join(directory, ENGINE_DLL_NAME)
                                if directory and os.path.isfile(candidate):
                                    return candidate
                        finally:
                            winreg.CloseKey(sub)
                finally:
                    winreg.CloseKey(root)
    except Exception:
        pass
    for base in (os.environ.get("ProgramFiles", r"C:\Program Files"),
                 os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                 os.environ.get("LOCALAPPDATA", "")):
        if not base or not os.path.isdir(base):
            continue
        try:
            entries = os.listdir(base)
        except OSError:
            continue
        for entry in entries:
            if not re.search(r"genflow|kuku|库库|baidugenflowpro", entry, re.I):
                continue
            candidate = os.path.join(base, entry, ENGINE_DLL_NAME)
            if os.path.isfile(candidate):
                return candidate
    return ""


def build_auth_param(bduss, ptoken):
    """构造 passport 换发用的签名参数体（复刻官方引擎 MD5 签名，无需 DLL）。"""
    signed = ("appid=1&bduss=%s&ptoken=%s&return_type=1&tpl=genflowpro"
              "&tpl_list=genflowpro|netdisk&sign_key=%s"
              % (bduss, ptoken, ENGINE_SIGN_KEY))
    signature = hashlib.md5(signed.encode("utf-8")).hexdigest()
    return ("appid=1&bduss=%s&ptoken=%s&return_type=1&tpl=genflowpro"
            "&tpl_list=genflowpro|netdisk&sig=%s" % (bduss, ptoken, signature))


def exchange_stoken(bduss, ptoken, opener=None):
    """用 BDUSS + PTOKEN 换发 genflowpro 作用域的 STOKEN。"""
    body = build_auth_param(bduss, ptoken).encode("utf-8")
    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "User-Agent": ENGINE_UA,
        "Referer": BASE_URL + "/genflowpro",
        "Origin": BASE_URL,
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    if opener:
        req = urllib.request.Request(PASSPORT_AUTH_URL, data=body, headers=headers, method="POST")
        try:
            with opener.open(req, timeout=30) as resp:
                status, text = resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            status, text = e.code, e.read().decode("utf-8", "replace")
        except Exception as e:
            status, text = -1, str(e)
    else:
        status, text = http("POST", PASSPORT_AUTH_URL, headers, body)
    if status != 200:
        raise RuntimeError("换发会话令牌失败：http=%s %s" % (status, text[:160]))
    try:
        data = json.loads(text)
    except Exception:
        raise RuntimeError("换发会话令牌失败：响应不是 JSON %s" % text[:160])
    stoken = str((data.get("stoken_list") or {}).get("genflowpro") or "").strip()
    if not stoken:
        errno = data.get("errno") or data.get("error_code") or ""
        msg = data.get("errmsg") or data.get("show_msg") or ""
        raise RuntimeError("换发会话令牌失败：errno=%s %s" % (errno, msg))
    return stoken


# ────────────────────────── STOKEN 缓存 ──────────────────────────
def load_cache():
    try:
        with open(STOKEN_CACHE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_cache(cache):
    try:
        with open(STOKEN_CACHE, "w", encoding="utf-8") as fh:
            json.dump(cache, fh, ensure_ascii=False, indent=2)
    except Exception as e:
        log("⚠️  [缓存] 写入失败: %s" % e)


def key_of(bduss):
    import hashlib
    return hashlib.sha256(bduss.encode("utf-8")).hexdigest()[:16]


def resolve_stoken(bduss, ptoken, manual, opener=None):
    """令牌优先级：环境变量 > 本机缓存 > 本机换发（纯签名，任意平台）。"""
    if manual:
        return manual, "配置"
    cache = load_cache()
    slot = cache.get(key_of(bduss)) or {}
    stoken = str(slot.get("stoken") or "").strip()
    if stoken:
        return stoken, "缓存"
    if not ptoken:
        raise RuntimeError("缺少 PTOKEN，无法换发会话令牌（请重新粘贴完整 Cookie）")
    stoken = exchange_stoken(bduss, ptoken, opener)
    cache[key_of(bduss)] = {"stoken": stoken, "at": int(time.time())}
    save_cache(cache)
    return stoken, "换发"


# ────────────────────────── 签到 ──────────────────────────
def panel_of(headers, opener=None):
    url = "%s/api/genflowpro/freepoint/homenew?%s" % (BASE_URL, WEB_QUERY)
    req = urllib.request.Request(url, headers=headers, method="GET")
    if opener:
        try:
            with opener.open(req, timeout=30) as resp:
                return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")
        except Exception as e:
            return -1, str(e)
    return http("GET", url, headers)


def complete_task(task_type, headers, opener=None):
    url = "%s/api/genflowpro/freepoint/taskComplete?%s" % (BASE_URL, WEB_QUERY)
    body = urllib.parse.urlencode({"task_type": task_type}).encode("utf-8")
    h = dict(headers)
    h["Content-Type"] = "application/x-www-form-urlencoded"
    if opener:
        req = urllib.request.Request(url, data=body, headers=h, method="POST")
        try:
            with opener.open(req, timeout=30) as resp:
                status, text = resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            status, text = e.code, e.read().decode("utf-8", "replace")
        except Exception as e:
            status, text = -1, str(e)
    else:
        status, text = http("POST", url, h, body)
    try:
        return status, json.loads(text)
    except Exception:
        return status, {"errno": -1, "show_msg": text[:160]}


def checkin_one(name, bduss, ptoken, manual_stoken, opener=None):
    """返回 (ok, 摘要文本)。"""
    try:
        stoken, source = resolve_stoken(bduss, ptoken, manual_stoken, opener)
    except Exception as e:
        return False, "会话令牌不可用：%s" % e
    headers = request_headers(bduss, stoken, [])
    status, text = panel_of(headers, opener)
    try:
        panel = json.loads(text)
    except Exception:
        return False, "任务面板响应异常（http=%s）%s" % (status, text[:120])
    errno = panel.get("errno")
    if errno != 0:
        msg = panel.get("show_msg") or panel.get("errmsg") or "未知错误"
        hint = ""
        if errno == -6:
            hint = "（会话令牌失效，请在 Windows 上重跑 `--token` 换发后更新）"
        return False, "任务面板不可读：errno=%s %s %s" % (errno, msg, hint)
    gained = []
    already = False
    total = 0
    for task_type, label in DAILY_TASKS:
        t_status, value = complete_task(task_type, headers, opener)
        errno = value.get("errno")
        if errno != 0:
            log("⚠️  [%s] %s 领取失败：errno=%s %s" % (
                name, label, errno, value.get("show_msg") or value.get("errmsg") or ""))
            continue
        data = value.get("data") or {}
        complete = str(data.get("complete_status") or "")
        reward = int(data.get("reward_point") or 0)
        if complete.upper() == "SUCCESS" and reward > 0:
            gained.append("%s+%s" % (label, reward))
            total += reward
        else:
            already = True
    if gained:
        return True, "签到完成：%s（共 +%s）" % ("、".join(gained), total)
    if already:
        return True, "今日积分已领过（接口幂等，无新增）"
    return True, "本次没有可领取的每日任务（活动可能未开始或已结束）"


# ────────────────────────── 账号 / 推送 / 入口 ──────────────────────────
def load_accounts():
    raw = os.getenv("KUKU_TOKENS", "").strip()
    if raw:
        accounts = []
        for line in re.split(r"[\n&]+", raw):
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 3:
                log("⚠️  [配置] 跳过格式不正确的条目（应为 备注|BDUSS|PTOKEN[|STOKEN]）")
                continue
            accounts.append({"name": parts[0] or ("账号%d" % (len(accounts) + 1)),
                             "bduss": parts[1], "ptoken": parts[2],
                             "stoken": parts[3] if len(parts) > 3 else ""})
        return accounts
    cookie = os.getenv("KUKU_COOKIES", "").strip()
    if not cookie:
        return []
    bduss, ptoken, _ = parse_cookie(cookie)
    return [{"name": "账号1", "bduss": bduss, "ptoken": ptoken,
             "stoken": os.getenv("KUKU_STOKEN", "").strip()}]


def notify(text, title="KukuAI 签到"):
    raw = text.encode("utf-8")[:1800].decode("utf-8", "ignore")
    key = os.getenv("QYWX_TOKEN", "").strip() or os.getenv("WECHAT_WEBHOOK", "").strip()
    if key:
        key = key.split("key=")[-1]
        url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=" + key
        _post_json(url, {"msgtype": "text", "text": {"content": title + "\n" + raw}})
    token = os.getenv("PLUSPLUS_TOKEN", "").strip()
    if token:
        _post_json("http://www.pushplus.plus/send",
                   {"token": token, "title": title, "content": raw, "template": "txt"})


def _post_json(url, payload):
    try:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=15).read()
    except Exception as e:
        log("⚠️  推送失败: %s" % e)


def main():
    only = ""
    token_mode = False
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--only" and i < len(sys.argv) - 1:
            only = sys.argv[i + 1]
        elif arg == "--token":
            token_mode = True
    accounts = load_accounts()
    if not accounts:
        log("❌ 未配置 KUKU_COOKIES（或 KUKU_TOKENS）。")
        log("   获取方法：登录 kuku.baidu.com/genflowpro 后，从浏览器开发者工具复制 Cookie；")
        log("   缺少 PTOKEN 时无法换发会话令牌，请确认复制了完整 Cookie。")
        return 1
    if token_mode:
        opener = proxy_opener()
        for idx, acc in enumerate(accounts, 1):
            if only and only != str(idx):
                continue
            log("🔑 [%s] 换发会话令牌 ..." % acc["name"])
            try:
                stoken, source = resolve_stoken(acc["bduss"], acc["ptoken"], acc["stoken"], opener)
                log("   STOKEN=%s  （来源：%s）" % (stoken, source))
                log("   把它填进环境变量 KUKU_STOKEN（多账号用 KUKU_TOKENS 的第 4 段）即可长期使用。")
            except Exception as e:
                log("   ❌ %s" % e)
                return 1
        return 0
    opener = proxy_opener()
    lines = []
    ok_count = 0
    for idx, acc in enumerate(accounts, 1):
        if only and only != str(idx):
            continue
        bduss = acc["bduss"]
        if len(bduss) < MIN_BDUSS_LEN:
            lines.append("❌ %s：BDUSS 不完整" % acc["name"])
            continue
        log("📱 [%s] 开始签到（BDUSS %s）" % (acc["name"], mask(bduss)))
        ok, msg = checkin_one(acc["name"], bduss, acc["ptoken"], acc["stoken"], opener)
        ok_count += 1 if ok else 0
        lines.append(("%s %s：%s" % ("✅" if ok else "❌", acc["name"], msg)))
        log("   " + lines[-1])
    summary = "\n".join(lines)
    log("\n===== KukuAI 签到汇总 =====\n" + summary)
    if os.getenv("KUKU_NO_NOTIFY", "").strip() != "1" and lines:
        notify(summary)
    return 0 if ok_count else 1


if __name__ == "__main__":
    sys.exit(main())
