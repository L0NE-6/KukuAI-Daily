#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KukuAI 登录态获取工具

三条路径，按场景挑一条：

  python kuku_get_cookie.py                 # ① 读本机库库 AI 客户端登录态（复制副本读，客户端开着也行）
  python kuku_get_cookie.py --paste         # ② 手动粘贴 Cookie（浏览器开发者工具复制）
  python kuku_get_cookie.py --exchange      # ③ 换发会话令牌（纯签名，任意平台，无需客户端）

输出：
  · KUKU_COOKIES=…     直接填环境变量
  · KUKU_STOKEN=…      旧 freepoint 的业务 STOKEN，仅 --legacy-freepoint 使用

说明：默认签到推荐完整网页 Cookie，其中至少包含 BDUSS；PTOKEN 用于换发业务 STOKEN。
      KUKU_STOKEN 仍只供旧 freepoint。旧 freepoint 的业务令牌按产品签发，
      本工具用官方引擎同款 MD5 签名换发（不再依赖 genflowengine.dll）。
"""

import argparse
import os
import sqlite3
import shutil
import sys
import tempfile

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from kuku_daily import (
        exchange_stoken,
        parse_cookie_parts,
        proxy_opener,
    )
except Exception as e:
    print("❌ 需要与 kuku_daily.py 放在同一目录：%s" % e)
    sys.exit(1)


def client_cookie_db():
    """定位客户端 Cookie 数据库（%APPDATA%\\baidugenflowpro\\Network\\Cookies）。"""
    appdata = os.environ.get("APPDATA", "")
    cands = [
        os.path.join(appdata, "baidugenflowpro", "Network", "Cookies"),
        os.path.join(appdata, "baidugenflowpro", "Cookies"),
        os.path.join(appdata, "genflowpro", "Network", "Cookies"),
    ]
    for p in cands:
        if os.path.isfile(p):
            return p
    return ""


def cookie_rows_to_header(rows):
    """把浏览器 Cookie 行归一成 Cookie 头，保留百度域完整登录态。"""
    picked = []
    seen = set()
    for host, name, value in rows:
        if not value or "baidu.com" not in str(host):
            continue
        if name == "HMACCOUNT" or name.lower().startswith("hm_"):
            continue
        low = name.lower()
        if low in seen:
            continue
        seen.add(low)
        picked.append((name, value))
    if not any(name.lower() == "bduss" for name, _ in picked):
        return ""
    return "; ".join("%s=%s" % (name, value) for name, value in picked)


def read_from_client():
    """从客户端 SQLite 读取明文 Cookie（复制副本再读，客户端开着也能读）。"""
    path = client_cookie_db()
    if not path:
        print("❌ 没找到客户端 Cookie 数据库。")
        print("   确认已安装并登录过库库 AI 客户端，或用 --paste 手动粘贴。")
        return None
    tmpdir = tempfile.mkdtemp(prefix="kuku-cookie-")
    db_copy = os.path.join(tmpdir, "Cookies")
    conn = None
    try:
        shutil.copy2(path, db_copy)
        for suffix in ("-wal", "-shm"):
            if os.path.isfile(path + suffix):
                shutil.copy2(path + suffix, db_copy + suffix)
        conn = sqlite3.connect(db_copy)
        rows = conn.execute("SELECT host_key, name, value FROM cookies").fetchall()
    except Exception as e:
        print("❌ 读取 Cookie 失败：%s" % e)
        return None
    finally:
        if conn is not None:
            conn.close()
        shutil.rmtree(tmpdir, ignore_errors=True)
    cookie = cookie_rows_to_header(rows)
    if not cookie:
        print("❌ 数据库里没有找到 BDUSS，说明客户端还没登录。")
        return None
    bduss, _, web_stoken, _ = parse_cookie_parts(cookie)
    note = "" if web_stoken else "；未发现 STOKEN，将优先使用 PTOKEN 换发"
    print("✅ 已从客户端读取完整 Cookie（BDUSS %s%s）" % (bduss[-4:], note))
    return cookie


def read_pasted():
    print("请粘贴完整 Cookie（至少含 BDUSS，推荐含 PTOKEN；也接受 Cookie 编辑器 JSON），粘贴完按回车：")
    try:
        text = input().strip()
    except EOFError:
        return ""
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paste", action="store_true", help="手动粘贴 Cookie")
    ap.add_argument("--exchange", action="store_true", help="换发 genflowpro 会话令牌")
    ap.add_argument("--stoken", default="", help="已有旧 freepoint 业务 STOKEN 时直接给出")
    args = ap.parse_args()

    cookie = read_pasted() if args.paste else read_from_client()
    if not cookie:
        return 1
    bduss, ptoken, web_stoken, _ = parse_cookie_parts(cookie)
    if len(bduss) < 8:
        print("❌ Cookie 里没有有效的 BDUSS，请确认复制完整。")
        return 1
    print()
    print("KUKU_COOKIES=%s" % cookie)
    if not web_stoken:
        print()
        print("⚠️ Cookie 缺少 STOKEN；建议保留 PTOKEN 以便默认签到换发业务令牌。")
    print()
    if args.stoken:
        print("KUKU_STOKEN=%s" % args.stoken)
        print()
        print("该业务 STOKEN 只供 kuku_daily.py --legacy-freepoint。")
        return 0
    if not args.exchange:
        print("（需要会话令牌时：加 --exchange 运行本工具，纯算法换发，任意平台都可）")
        return 0
    if not ptoken:
        print("❌ 换发需要 PTOKEN，但当前 Cookie 里没有。请重新复制完整 Cookie。")
        return 1
    try:
        stoken = exchange_stoken(bduss, ptoken, proxy_opener())
    except Exception as e:
        print("❌ 换发失败：%s" % e)
        return 1
    print("✅ 换发成功")
    print()
    print("KUKU_STOKEN=%s" % stoken)
    print()
    print("该业务 STOKEN 只供 kuku_daily.py --legacy-freepoint 与 --token。")
    print("默认签到会在运行时按完整 Cookie 自动准备会话。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
