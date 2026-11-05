#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KukuAI（百度文库 · 库库 AI / GenFlowPro）每日签到 —— 单文件青龙脚本

做什么：
  · 默认执行「库库 30 天签到」：读活动配置、查签到面板、取风控 token、签到
  · 成功只认 errno=0 且 data.signed_today 为布尔 true；10152 按已签中性处理
  · 旧「免费领积分」任务仅在显式传入 --legacy-freepoint 时执行

前置条件（重要）：
  · 30 天签到只使用完整网页 Cookie；其中必须包含 BDUSS 与网页 STOKEN。
  · KUKU_STOKEN 是旧 freepoint 的业务令牌，不会覆盖或替代网页 STOKEN。
  · 旧 freepoint 业务接口需要一个按产品签发的会话令牌（作用域 genflowpro）。
    网页登录拿到的 Cookie 里那份是通行证级的，业务接口会判未登录（errno=-6）。
    本脚本用**纯算法**换发（复刻官方引擎的 MD5 签名）—— 不再依赖
    genflowengine.dll，Windows / Linux / 青龙都能直接换发。

环境变量：
  KUKU_COOKIES     必填。完整网页 Cookie，至少包含 BDUSS 与 STOKEN；PTOKEN、
                   BAIDUID、PANPSC 等字段会原样保留。
  KUKU_STOKEN      可选。旧 freepoint 的业务 STOKEN；30 天链路永不读取。
  KUKU_TOKENS      可选。多账号，推荐 JSON 数组；也支持“备注|完整Cookie|业务STOKEN”。
  KUKU_PROXY       可选。http(s)/socks5 代理，例如 http://127.0.0.1:7890
  KUKU_NO_NOTIFY   可选。设 1 关闭推送。

推送：企业微信机器人（QYWX_TOKEN / WECHAT_WEBHOOK）/ PushPlus（PLUSPLUS_TOKEN），
      配了哪个推哪个；都没有则只打印。

用法：
  python kuku_daily.py                     # 30 天签到，全部账号
  python kuku_daily.py --only 1            # 只跑第 1 个账号
  python kuku_daily.py --legacy-freepoint  # 显式执行旧 freepoint 任务
  python kuku_daily.py --token             # 只尝试换发并打印令牌（任意平台）

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

VERSION = "1.3.0"
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
ACTIVITY_CONF_URL = BASE_URL + "/act/api/conf?conf_key=kukuSignConf"
ACTIVITY_HOME_URL = BASE_URL + "/act/v2/kukuai30/homepage"
ACTIVITY_TOKEN_URL = BASE_URL + "/operation/activitys/api/getJsToken"
ACTIVITY_SIGN_URL = BASE_URL + "/act/v2/kukuai30/signin"
ACTIVITY_REFERER = ("https://kuku.baidu.com/operation/activitys/"
                    "kukuPcSignAct/main")
ACTIVITY_AID = 15459
ACTIVITY_SIGN_POINT = 10
STOKEN_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".kuku_stoken.json")
MIN_BDUSS_LEN = 8


# ────────────────────────── 通用 ──────────────────────────
def log(msg):
    print(msg, flush=True)


def mask(value):
    """脱敏：只留尾 4 位。"""
    v = str(value or "")
    return ("*" * max(0, len(v) - 4)) + v[-4:] if len(v) > 4 else "*" * len(v)


def http(method, url, headers=None, body=None, timeout=30, opener=None):
    """返回 (status, text)。网络错误返回 (-1, 错误串)。"""
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        open_url = opener.open if opener else urllib.request.urlopen
        with open_url(req, timeout=timeout) as resp:
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


def request_json(method, url, headers, body=None, opener=None, label="响应"):
    """发起请求并解析 JSON 对象；失败返回 (status, None, 错误文案)。"""
    if opener:
        status, text = http(method, url, headers, body, opener=opener)
    else:
        status, text = http(method, url, headers, body)
    try:
        value = json.loads(text)
    except Exception:
        return status, None, "%s不是 JSON（http=%s）%s" % (label, status, text[:160])
    if not isinstance(value, dict):
        return status, None, "%s不是 JSON 对象（http=%s）" % (label, status)
    return status, value, ""


def integer(value):
    """只接受 JSON 整数或纯十进制字符串；缺失和布尔值都返回 None。"""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip(), 10)
        except ValueError:
            return None
    return None


def response_message(value, default="未知错误"):
    return str(value.get("show_msg") or value.get("errmsg") or default)


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


def parse_cookie_parts(raw):
    """把各种形态的 Cookie 归一到 (bduss, ptoken, web_stoken, extras)。"""
    raw = (raw or "").strip()
    pairs = _pairs_from_json(raw) if raw[:1] in "[{" else []
    if not pairs:
        pairs = _pairs_from_header(raw)
    bduss = ptoken = web_stoken = ""
    extras = []
    seen = set()
    for name, value in pairs:
        low = name.lower()
        if low == "bduss":
            bduss = value
        elif low == "ptoken":
            ptoken = value
        elif low == "stoken":
            web_stoken = value
        elif low != "gfprotpl":
            if low not in seen:
                seen.add(low)
                extras.append((name, value))
    return bduss, ptoken, web_stoken, extras


def parse_cookie(raw):
    """兼容旧调用：返回 (bduss, ptoken, extras)。"""
    bduss, ptoken, _, extras = parse_cookie_parts(raw)
    return bduss, ptoken, extras


def cookie_header(bduss, stoken, extras, ptoken=""):
    parts = ["BDUSS=" + bduss]
    if stoken:
        parts.append("STOKEN=" + stoken)
    if ptoken:
        parts.append("PTOKEN=" + ptoken)
    for name, value in extras:
        low = str(name).lower()
        if low in ("bduss", "stoken", "ptoken", "gfprotpl"):
            continue
        parts.append("%s=%s" % (name, value))
    parts.append("gfprotpl=genflowpro")
    return "; ".join(parts)


def request_headers(bduss, business_stoken, extras, ptoken=""):
    """旧 freepoint 请求头；只允许使用业务 STOKEN。"""
    return {
        "Cookie": cookie_header(bduss, business_stoken, extras, ptoken),
        "User-Agent": USER_AGENT,
        "Referer": BASE_URL + "/genflowpro",
        "Origin": BASE_URL,
        "Accept-Language": "zh-CN,zh;q=0.9",
    }


def activity_headers(bduss, web_stoken, extras, ptoken=""):
    """30 天签到请求头；只允许使用完整 Cookie 内的网页 STOKEN。"""
    return {
        "Cookie": cookie_header(bduss, web_stoken, extras, ptoken),
        "User-Agent": USER_AGENT,
        "Referer": ACTIVITY_REFERER,
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
def activity_config(value):
    """从活动配置响应中取 (activityTid, signPoint)。"""
    rows = value.get("data")
    if not isinstance(rows, list):
        return None
    for row in rows:
        if not isinstance(row, dict):
            continue
        config = row.get("conf_value")
        if not isinstance(config, dict):
            continue
        tid_value = config.get("activityTid")
        if isinstance(tid_value, bool) or not isinstance(tid_value, (int, str)):
            continue
        tid = str(tid_value).strip()
        if not tid:
            continue
        point = integer(config.get("signPoint"))
        if point is None or point < 0:
            point = ACTIVITY_SIGN_POINT
        return tid, point
    return None


def extract_js_token(raw):
    """从 URL 编码的 JS 片段中取最后一对双引号内的风控 token。"""
    decoded = urllib.parse.unquote(str(raw or ""))
    end = decoded.rfind('"')
    if end < 0:
        return ""
    start = decoded.rfind('"', 0, end)
    if start < 0:
        return ""
    return decoded[start + 1:end]


def checkin_thirty_days(bduss, web_stoken, extras=None, opener=None, ptoken=""):
    """执行库库 30 天签到主链路，返回 (ok, 摘要文本)。"""
    if not web_stoken:
        return False, (
            "网页 Cookie 缺少 STOKEN，请从活动页重新导出完整 Cookie；"
            "KUKU_STOKEN 仅用于旧 freepoint，不会替代网页 STOKEN"
        )
    headers = activity_headers(bduss, web_stoken, extras or [], ptoken)

    status, conf, error = request_json(
        "GET", ACTIVITY_CONF_URL, headers, opener=opener, label="活动配置响应")
    if error:
        return False, "30 天签到活动配置读取失败：%s" % error
    if status != 200:
        return False, "30 天签到活动配置读取失败：http=%s" % status
    conf_errno = integer(conf.get("errno"))
    if conf_errno not in (None, 0):
        return False, "30 天签到活动配置不可用：errno=%s %s" % (
            conf_errno, response_message(conf))
    config = activity_config(conf)
    if not config:
        return False, "30 天签到活动配置缺少 activityTid"
    tid, point = config

    home_url = ACTIVITY_HOME_URL + "?" + urllib.parse.urlencode({"tid": tid})
    status, home, error = request_json(
        "GET", home_url, headers, opener=opener, label="活动面板响应")
    if error:
        return False, "30 天签到活动面板读取失败：%s" % error
    if status != 200:
        return False, "30 天签到活动面板读取失败：http=%s" % status
    home_errno = integer(home.get("errno"))
    if home_errno != 0:
        return False, "30 天签到活动面板不可读：errno=%s %s" % (
            home_errno, response_message(home))
    data = home.get("data")
    if not isinstance(data, dict):
        data = {}
    continuous = max(0, integer(data.get("continuous_days")) or 0)
    total = max(0, integer(data.get("total_days")) or 0)
    if data.get("signed_today") is True:
        return True, "今日已签到（连续 %s 天，累计 %s 天）" % (continuous, total)

    status, token_value, error = request_json(
        "GET", ACTIVITY_TOKEN_URL, headers, opener=opener, label="签到凭证响应")
    if error:
        return False, "签到凭证获取失败：%s" % error
    if status != 200:
        return False, "签到凭证获取失败：http=%s" % status
    token_data = token_value.get("data")
    if not isinstance(token_data, dict):
        token_data = {}
    token = extract_js_token(token_data.get("jsToken"))
    if not token:
        return False, "签到凭证为空（jsToken 解析失败）"

    query = urllib.parse.urlencode({
        "tid": tid,
        "jsToken": token,
        "aid": str(ACTIVITY_AID),
    })
    sign_headers = dict(headers)
    sign_headers["Content-Type"] = "application/x-www-form-urlencoded;charset=UTF-8"
    status, signed, error = request_json(
        "POST", ACTIVITY_SIGN_URL + "?" + query, sign_headers,
        body=b"", opener=opener, label="签到响应")
    if error:
        return False, "签到请求失败：%s" % error
    errno = integer(signed.get("errno"))
    if errno == 0:
        sign_data = signed.get("data")
        if not isinstance(sign_data, dict):
            sign_data = {}
        if status != 200:
            return False, "上游未确认签到完成（http=%s）" % status
        if sign_data.get("signed_today") is not True:
            return False, "上游未确认签到完成（errno=0，signed_today 不是 true）"
        signed_continuous = integer(sign_data.get("continuous"))
        if signed_continuous is not None:
            continuous = max(0, signed_continuous)
        total = max(total, continuous)
        return True, "库库 30 天签到成功：+%s 积分（连续 %s 天，累计 %s 天）" % (
            point, continuous, total)
    if errno == 10152:
        return True, "今日已签到（errno=10152；连续 %s 天，累计 %s 天）" % (
            continuous, total)
    if errno in (8001, 8002):
        return False, "上游风控未通过（errno=%s：%s），请重新登录该账号后再试" % (
            errno, response_message(signed))
    if errno is None:
        return False, "签到响应缺少 errno（http=%s）" % status
    return False, "签到失败：errno=%s %s" % (errno, response_message(signed))


def panel_of(headers, opener=None):
    url = "%s/api/genflowpro/freepoint/homenew?%s" % (BASE_URL, WEB_QUERY)
    if opener:
        return http("GET", url, headers, opener=opener)
    return http("GET", url, headers)


def complete_task(task_type, headers, opener=None):
    url = "%s/api/genflowpro/freepoint/taskComplete?%s" % (BASE_URL, WEB_QUERY)
    body = urllib.parse.urlencode({"task_type": task_type}).encode("utf-8")
    h = dict(headers)
    h["Content-Type"] = "application/x-www-form-urlencoded"
    if opener:
        status, text = http("POST", url, h, body, opener=opener)
    else:
        status, text = http("POST", url, h, body)
    try:
        return status, json.loads(text)
    except Exception:
        return status, {"errno": -1, "show_msg": text[:160]}


def legacy_freepoint_one(
        name, bduss, ptoken, business_stoken, opener=None, extras=None):
    """显式执行旧 freepoint 任务，返回 (ok, 摘要文本)。"""
    try:
        stoken, _ = resolve_stoken(bduss, ptoken, business_stoken, opener)
    except Exception as e:
        return False, "会话令牌不可用：%s" % e
    headers = request_headers(bduss, stoken, extras or [], ptoken)
    status, text = panel_of(headers, opener)
    try:
        panel = json.loads(text)
    except Exception:
        return False, "任务面板响应异常（http=%s）%s" % (status, text[:120])
    errno = integer(panel.get("errno"))
    if errno != 0:
        hint = ""
        if errno == -6:
            hint = "（会话令牌失效，请在 Windows 上重跑 `--token` 换发后更新）"
        return False, "任务面板不可读：errno=%s %s %s" % (
            errno, response_message(panel), hint)
    panel_data = panel.get("data")
    activities = panel_data.get("activities") if isinstance(panel_data, dict) else None
    if isinstance(activities, list) and not activities:
        return True, "当前没有可参加的「免费领积分」活动（活动可能已结束）"
    gained = []
    already = False
    total = 0
    failures = []
    unresolved = []
    for task_type, task_label in DAILY_TASKS:
        _, value = complete_task(task_type, headers, opener)
        errno = integer(value.get("errno"))
        if errno != 0:
            message = response_message(value)
            log("⚠️  [%s] %s 领取失败：errno=%s %s" % (
                name, task_label, errno, message))
            failures.append("%s：errno=%s %s" % (task_label, errno, message))
            continue
        data = value.get("data")
        if not isinstance(data, dict):
            data = {}
        complete = str(data.get("complete_status") or "")
        reward = integer(data.get("reward_point")) or 0
        if complete.upper() == "SUCCESS" and reward > 0:
            gained.append("%s+%s" % (task_label, reward))
            total += reward
        elif ((complete.upper() == "SUCCESS" and reward == 0)
              or complete.upper() == "BADGE_ALREADY_RECEIVED"):
            already = True
        else:
            unresolved.append("%s：上游未确认完成（%s）" % (task_label, complete))
    if gained:
        message = "签到完成：%s（共 +%s）" % ("、".join(gained), total)
        if failures:
            message += "；部分任务失败：%s" % "；".join(failures)
        if unresolved:
            message += "；%s" % "；".join(unresolved)
        return True, message
    if already:
        message = "今日积分已领过（接口幂等，无新增）"
        if failures:
            message += "；部分任务失败：%s" % "；".join(failures)
        if unresolved:
            message += "；%s" % "；".join(unresolved)
        return True, message
    if failures:
        return False, "每日任务领取失败：%s" % "；".join(failures)
    if unresolved:
        return False, "上游未确认完成：%s" % "；".join(unresolved)
    return True, "本次没有可领取的每日任务"


def checkin_one(name, bduss, ptoken, web_stoken, opener=None, extras=None):
    """默认执行 30 天签到，返回 (ok, 摘要文本)。"""
    return checkin_thirty_days(bduss, web_stoken, extras, opener, ptoken)


# ────────────────────────── 账号 / 推送 / 入口 ──────────────────────────
def cookie_input_text(value):
    """把 Cookie 头、Cookie 编辑器 JSON 或对象统一成可解析文本。"""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return ""


def account_from_cookie(name, cookie, business_stoken="", index=1):
    """从一条完整 Cookie 构造账号；web/business 两个 STOKEN 永不混用。"""
    bduss, ptoken, web_stoken, extras = parse_cookie_parts(cookie_input_text(cookie))
    if len(bduss) < MIN_BDUSS_LEN:
        log("⚠️  [配置] 跳过第 %s 个账号：Cookie 缺少有效 BDUSS" % index)
        return None
    return {
        "name": str(name or ("账号%d" % index)),
        "bduss": bduss,
        "ptoken": ptoken,
        "web_stoken": web_stoken,
        "business_stoken": str(business_stoken or "").strip(),
        "extras": extras,
    }


def accounts_from_json(raw):
    """解析 KUKU_TOKENS JSON 数组；每条用 cookie + business_stoken 描述。"""
    try:
        value = json.loads(raw)
    except Exception as e:
        log("⚠️  [配置] KUKU_TOKENS 不是合法 JSON：%s" % e)
        return []
    if isinstance(value, dict) and isinstance(value.get("accounts"), list):
        value = value["accounts"]
    elif isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        log("⚠️  [配置] KUKU_TOKENS JSON 应为账号数组")
        return []

    accounts = []
    metadata = {"name", "remark", "note", "business_stoken", "businessStoken", "stoken"}
    for index, item in enumerate(value, 1):
        if isinstance(item, str):
            account = account_from_cookie("账号%d" % index, item, "", index)
        elif isinstance(item, dict):
            name = item.get("name") or item.get("remark") or item.get("note")
            business_stoken = (
                item.get("business_stoken")
                or item.get("businessStoken")
                or item.get("stoken")
                or ""
            )
            cookie = item.get("cookie")
            if cookie is None:
                cookie = item.get("cookieHeader")
            if cookie is None:
                cookie = {
                    key: val
                    for key, val in item.items()
                    if key not in metadata and key not in ("cookie", "cookieHeader")
                }
            account = account_from_cookie(name, cookie, business_stoken, index)
        else:
            log("⚠️  [配置] 跳过第 %s 个账号：KUKU_TOKENS 条目类型不正确" % index)
            continue
        if account:
            accounts.append(account)
    return accounts


def accounts_from_lines(raw):
    """解析换行/& 分隔的 KUKU_TOKENS；支持完整 Cookie 与旧位置字段。"""
    accounts = []
    for index, line in enumerate(re.split(r"[\n&]+", raw), 1):
        line = line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) == 1:
            if "=" not in parts[0]:
                log("⚠️  [配置] 跳过第 %s 个账号：无法识别 Cookie" % index)
                continue
            account = account_from_cookie("账号%d" % index, parts[0], "", index)
        elif "=" in parts[1] or ";" in parts[1]:
            business_stoken = parts[2] if len(parts) > 2 else ""
            account = account_from_cookie(parts[0], parts[1], business_stoken, index)
        elif len(parts) >= 3:
            # 兼容旧格式：备注|BDUSS|PTOKEN[|旧 freepoint 业务 STOKEN]
            cookie = "BDUSS=%s; PTOKEN=%s" % (parts[1], parts[2])
            business_stoken = parts[3] if len(parts) > 3 else ""
            account = account_from_cookie(parts[0], cookie, business_stoken, index)
        else:
            log("⚠️  [配置] 跳过第 %s 个账号：应为 备注|完整Cookie|业务STOKEN" % index)
            continue
        if account:
            accounts.append(account)
    return accounts


def load_accounts():
    raw = os.getenv("KUKU_TOKENS", "").strip()
    if raw:
        if raw[:1] in "[{":
            return accounts_from_json(raw)
        return accounts_from_lines(raw)
    cookie = os.getenv("KUKU_COOKIES", "").strip()
    if not cookie:
        return []
    account = account_from_cookie(
        "账号1",
        cookie,
        os.getenv("KUKU_STOKEN", "").strip(),
        1,
    )
    return [account] if account else []


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
    legacy_freepoint = False
    version_mode = False
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--only" and i < len(sys.argv) - 1:
            only = sys.argv[i + 1]
        elif arg == "--token":
            token_mode = True
        elif arg == "--legacy-freepoint":
            legacy_freepoint = True
        elif arg == "--version":
            version_mode = True
    if version_mode:
        log("KukuAI Daily v%s" % VERSION)
        return 0
    accounts = load_accounts()
    if not accounts:
        log("❌ 未配置 KUKU_COOKIES（或 KUKU_TOKENS）。")
        log("   获取方法：登录 kuku.baidu.com/operation/activitys/kukuPcSignAct/main "
            "后，从浏览器开发者工具复制完整 Cookie。")
        log("   默认 30 天签到使用网页 Cookie；--legacy-freepoint 还需要 PTOKEN/STOKEN。")
        return 1
    if token_mode:
        opener = proxy_opener()
        for idx, acc in enumerate(accounts, 1):
            if only and only != str(idx):
                continue
            log("🔑 [%s] 换发会话令牌 ..." % acc["name"])
            try:
                stoken, source = resolve_stoken(
                    acc["bduss"], acc["ptoken"], acc.get("business_stoken", ""), opener)
                log("   STOKEN=%s  （来源：%s）" % (stoken, source))
                log("   该业务 STOKEN 只供 --legacy-freepoint；30 天签到仍使用 Cookie 内的网页 STOKEN。")
            except Exception as e:
                log("   ❌ %s" % e)
                return 1
        return 0
    opener = proxy_opener()
    lines = []
    ok_count = 0
    mode = "旧 freepoint 任务" if legacy_freepoint else "库库 30 天签到"
    for idx, acc in enumerate(accounts, 1):
        if only and only != str(idx):
            continue
        bduss = acc["bduss"]
        if len(bduss) < MIN_BDUSS_LEN:
            lines.append("❌ %s：BDUSS 不完整" % acc["name"])
            continue
        log("📱 [%s] 开始%s（BDUSS %s）" % (
            acc["name"], mode, mask(bduss)))
        extras = acc.get("extras") or []
        if legacy_freepoint:
            ok, msg = legacy_freepoint_one(
                acc["name"], bduss, acc["ptoken"], acc.get("business_stoken", ""),
                opener, extras)
        else:
            ok, msg = checkin_one(
                acc["name"], bduss, acc["ptoken"], acc.get("web_stoken", ""),
                opener, extras)
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
