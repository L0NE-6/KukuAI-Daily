import json
import os
import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, quote, urlsplit


sys.path.insert(0, str(Path(__file__).resolve().parent))

from _loader import ROOT, FakeHttp, load_script


KD = load_script("kuku_daily_contract", "kuku_daily.py")
GC = load_script("kuku_get_cookie_contract", "kuku_get_cookie.py")


def conf_payload(tid="73001", point=10):
    return (200, {
        "errno": 0,
        "data": [{"conf_value": {"activityTid": tid, "signPoint": point}}],
    })


def home_payload(signed_today=False, continuous=2, total=2):
    return (200, {
        "errno": 0,
        "data": {
            "signed_today": signed_today,
            "continuous_days": continuous,
            "total_days": total,
        },
    })


def token_payload(token="deadbeef"):
    js = quote('function fn(a){return a};fn("%s")' % token)
    return (200, {"errno": 0, "data": {"jsToken": js}})


def sign_payload(errno=0, signed_today=True, continuous=3):
    data = {"continuous": continuous}
    if signed_today is not None:
        data["signed_today"] = signed_today
    return (200, {"errno": errno, "data": data})


class ThirtyDayContractTests(unittest.TestCase):
    def test_success_requires_errno_zero_and_signed_today_true(self):
        client = FakeHttp([
            conf_payload(),
            home_payload(),
            token_payload(),
            sign_payload(),
        ])
        with mock.patch.object(KD, "http", client):
            ok, message = KD.checkin_thirty_days(
                "BDUSS-test", "web-token", [], ptoken="ptoken-value")

        self.assertTrue(ok)
        self.assertIn("+10 积分", message)
        self.assertEqual(
            ["GET", "GET", "GET", "POST"],
            [call["method"] for call in client.calls],
        )
        self.assertEqual(KD.ACTIVITY_CONF_URL, client.calls[0]["url"])
        self.assertTrue(client.calls[1]["url"].startswith(KD.ACTIVITY_HOME_URL + "?"))
        self.assertEqual(KD.ACTIVITY_TOKEN_URL, client.calls[2]["url"])
        self.assertTrue(client.calls[3]["url"].startswith(KD.ACTIVITY_SIGN_URL + "?"))
        for call in client.calls:
            self.assertEqual(KD.ACTIVITY_REFERER, call["headers"]["Referer"])
            self.assertIn("STOKEN=web-token", call["headers"]["Cookie"])
            self.assertIn("PTOKEN=ptoken-value", call["headers"]["Cookie"])

        sign_call = client.calls[-1]
        query = parse_qs(urlsplit(sign_call["url"]).query)
        self.assertEqual(["73001"], query["tid"])
        self.assertEqual(["deadbeef"], query["jsToken"])
        self.assertEqual(["15459"], query["aid"])
        self.assertEqual(b"", sign_call["body"])

    def test_errno_zero_without_boolean_true_is_failure(self):
        for data, label in (
            ({"continuous": 3}, "missing"),
            ({"signed_today": False, "continuous": 3}, "false"),
            ({"signed_today": 1, "continuous": 3}, "non-boolean"),
        ):
            with self.subTest(label=label):
                client = FakeHttp([
                    conf_payload(),
                    home_payload(),
                    token_payload(),
                    (200, {"errno": 0, "data": data}),
                ])
                with mock.patch.object(KD, "http", client):
                    ok, message = KD.checkin_thirty_days(
                        "BDUSS-test", "web-token", [])
                self.assertFalse(ok)
                self.assertIn("signed_today 不是 true", message)

    def test_homepage_signed_today_is_neutral_without_token_request(self):
        client = FakeHttp([
            conf_payload(),
            home_payload(signed_today=True, continuous=7, total=9),
        ])
        with mock.patch.object(KD, "http", client):
            ok, message = KD.checkin_thirty_days(
                "BDUSS-test", "web-token", [])

        self.assertTrue(ok)
        self.assertIn("今日已签到", message)
        self.assertEqual(2, len(client.calls))
        self.assertFalse(any("/getJsToken" in call["url"] for call in client.calls))

    def test_10152_is_neutral_completion(self):
        client = FakeHttp([
            conf_payload(),
            home_payload(),
            token_payload(),
            sign_payload(errno=10152, signed_today=None, continuous=4),
        ])
        with mock.patch.object(KD, "http", client):
            ok, message = KD.checkin_thirty_days(
                "BDUSS-test", "web-token", [])

        self.assertTrue(ok)
        self.assertIn("errno=10152", message)

    def test_8001_and_8002_are_risk_failures(self):
        for errno in (8001, 8002):
            with self.subTest(errno=errno):
                client = FakeHttp([
                    conf_payload(),
                    home_payload(),
                    token_payload(),
                    sign_payload(errno=errno, signed_today=None),
                ])
                with mock.patch.object(KD, "http", client):
                    ok, message = KD.checkin_thirty_days(
                        "BDUSS-test", "web-token", [])
                self.assertFalse(ok)
                self.assertIn("风控", message)
                self.assertIn(str(errno), message)

    def test_config_failure_does_not_call_legacy_freepoint(self):
        client = FakeHttp([
            (200, {"errno": -6, "show_msg": "login required"}),
        ])
        with mock.patch.object(KD, "http", client):
            ok, message = KD.checkin_one(
                "acct", "BDUSS-test", "ptoken", "web-token", None, [])

        self.assertFalse(ok)
        self.assertIn("errno=-6", message)
        self.assertEqual(1, len(client.calls))
        self.assertIn("PTOKEN=ptoken", client.calls[0]["headers"]["Cookie"])
        self.assertIn("STOKEN=web-token", client.calls[0]["headers"]["Cookie"])
        self.assertFalse(any("/api/genflowpro" in call["url"] for call in client.calls))

    def test_missing_web_stoken_fails_without_http(self):
        client = FakeHttp([])
        with mock.patch.object(KD, "http", client):
            ok, message = KD.checkin_one(
                "acct", "BDUSS-test", "ptoken", "", None, [])

        self.assertFalse(ok)
        self.assertIn("重新导出完整 Cookie", message)
        self.assertIn("KUKU_STOKEN", message)
        self.assertEqual([], client.calls)

    def test_legacy_freepoint_uses_business_stoken_only(self):
        captured = {}

        def fake_panel(headers, opener=None):
            captured["headers"] = headers
            return 200, json.dumps({"errno": 0, "data": {"activities": []}})

        with mock.patch.object(KD, "panel_of", side_effect=fake_panel):
            ok, message = KD.legacy_freepoint_one(
                "acct",
                "BDUSS-test",
                "ptoken-value",
                "business-token",
                None,
                [("BAIDUID", "baiduid-value"), ("PANPSC", "panpsc-value")],
            )

        self.assertTrue(ok)
        self.assertIn("没有可参加", message)
        cookie = captured["headers"]["Cookie"]
        self.assertIn("STOKEN=business-token", cookie)
        self.assertNotIn("STOKEN=web-token", cookie)
        self.assertIn("PTOKEN=ptoken-value", cookie)
        self.assertIn("BAIDUID=baiduid-value", cookie)
        self.assertIn("PANPSC=panpsc-value", cookie)

    def test_activity_config_accepts_numeric_tid_and_string_point(self):
        value = {
            "data": [
                {"conf_value": {"activityTid": 73002, "signPoint": "15"}},
            ]
        }
        self.assertEqual(("73002", 15), KD.activity_config(value))

    def test_js_token_is_percent_decoded_without_execution(self):
        raw = quote('function fn(a){return a};fn("A1B2C3")')
        self.assertEqual("A1B2C3", KD.extract_js_token(raw))


class CliAndCompatibilityTests(unittest.TestCase):
    def accounts(self):
        return [{
            "name": "账号甲",
            "bduss": "BDUSS-123456",
            "ptoken": "ptoken",
            "web_stoken": "web-token",
            "business_stoken": "business-token",
            "extras": [],
        }]

    def run_main(self, argv, accounts, new_result=(True, "new"), legacy_result=(True, "old")):
        with ExitStack() as stack:
            stack.enter_context(mock.patch.dict(
                os.environ, {"KUKU_NO_NOTIFY": "0"}, clear=False))
            stack.enter_context(mock.patch.object(KD.sys, "argv", argv))
            stack.enter_context(mock.patch.object(
                KD, "load_accounts", return_value=accounts))
            stack.enter_context(mock.patch.object(
                KD, "proxy_opener", return_value=None))
            stack.enter_context(mock.patch.object(KD, "log"))
            notify = stack.enter_context(mock.patch.object(KD, "notify"))
            new_checkin = stack.enter_context(mock.patch.object(
                KD, "checkin_one", return_value=new_result))
            legacy = stack.enter_context(mock.patch.object(
                KD, "legacy_freepoint_one", return_value=legacy_result))
            code = KD.main()
        return code, new_checkin, legacy, notify

    def test_default_cli_runs_only_thirty_day_path(self):
        code, new_checkin, legacy, _ = self.run_main(
            ["kuku_daily.py"], self.accounts())
        self.assertEqual(0, code)
        new_checkin.assert_called_once()
        legacy.assert_not_called()
        self.assertEqual("web-token", new_checkin.call_args.args[3])

    def test_legacy_freepoint_requires_explicit_flag(self):
        code, new_checkin, legacy, _ = self.run_main(
            ["kuku_daily.py", "--legacy-freepoint"], self.accounts())
        self.assertEqual(0, code)
        new_checkin.assert_not_called()
        legacy.assert_called_once()
        self.assertEqual("business-token", legacy.call_args.args[3])

    def test_kuku_stoken_does_not_replace_missing_web_stoken(self):
        env = {
            "KUKU_COOKIES": "BDUSS=BDUSS-123456; PTOKEN=ptoken-value",
            "KUKU_STOKEN": "business-token",
            "KUKU_NO_NOTIFY": "0",
        }
        client = FakeHttp([])
        with mock.patch.dict(os.environ, env, clear=True):
            with ExitStack() as stack:
                stack.enter_context(mock.patch.object(
                    KD.sys, "argv", ["kuku_daily.py"]))
                stack.enter_context(mock.patch.object(KD, "http", client))
                stack.enter_context(mock.patch.object(
                    KD, "proxy_opener", return_value=None))
                stack.enter_context(mock.patch.object(KD, "log"))
                notify = stack.enter_context(mock.patch.object(KD, "notify"))
                code = KD.main()

        self.assertEqual(1, code)
        self.assertEqual([], client.calls)
        self.assertIn("网页 Cookie 缺少 STOKEN", notify.call_args.args[0])

    def test_multiple_accounts_are_kept_in_notification_summary(self):
        accounts = [
            {
                "name": "账号甲",
                "bduss": "BDUSS-123456",
                "ptoken": "ptoken-a",
                "web_stoken": "web-a",
                "business_stoken": "business-a",
                "extras": [],
            },
            {
                "name": "账号乙",
                "bduss": "BDUSS-654321",
                "ptoken": "ptoken-b",
                "web_stoken": "web-b",
                "business_stoken": "business-b",
                "extras": [],
            },
        ]
        code, new_checkin, _, notify = self.run_main(
            ["kuku_daily.py"], accounts)
        self.assertEqual(0, code)
        self.assertEqual(2, new_checkin.call_count)
        notify.assert_called_once()
        summary = notify.call_args.args[0]
        self.assertIn("账号甲", summary)
        self.assertIn("账号乙", summary)

    def test_multi_account_json_preserves_full_cookie_and_web_token(self):
        raw = json.dumps([
            {
                "name": "账号甲",
                "cookie": (
                    "BDUSS=BDUSS-AAAA; STOKEN=web-a; PTOKEN=ptoken-a; "
                    "BAIDUID=baiduid-a; PANPSC=panpsc-a"
                ),
                "business_stoken": "business-a",
            },
            {
                "name": "账号乙",
                "cookie": (
                    "BDUSS=BDUSS-BBBB; STOKEN=web-b; PTOKEN=ptoken-b; "
                    "BAIDUID=baiduid-b; PANPSC=panpsc-b"
                ),
                "business_stoken": "business-b",
            },
        ])
        env = {
            "KUKU_TOKENS": raw,
            "KUKU_STOKEN": "global-business-must-not-be-used",
            "KUKU_NO_NOTIFY": "1",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            accounts = KD.load_accounts()
            self.assertEqual(["账号甲", "账号乙"], [item["name"] for item in accounts])
            self.assertEqual(["web-a", "web-b"], [item["web_stoken"] for item in accounts])
            self.assertEqual(
                ["business-a", "business-b"],
                [item["business_stoken"] for item in accounts],
            )
            for item, marker in zip(accounts, ("a", "b")):
                self.assertIn(("BAIDUID", "baiduid-%s" % marker), item["extras"])
                self.assertIn(("PANPSC", "panpsc-%s" % marker), item["extras"])

            responses = [
                conf_payload(),
                home_payload(),
                token_payload(),
                sign_payload(),
            ] * 2
            client = FakeHttp(responses)
            with ExitStack() as stack:
                stack.enter_context(mock.patch.object(
                    KD.sys, "argv", ["kuku_daily.py"]))
                stack.enter_context(mock.patch.object(KD, "http", client))
                stack.enter_context(mock.patch.object(
                    KD, "proxy_opener", return_value=None))
                stack.enter_context(mock.patch.object(KD, "log"))
                stack.enter_context(mock.patch.object(KD, "notify"))
                code = KD.main()

        self.assertEqual(0, code)
        self.assertEqual(8, len(client.calls))
        for group, marker, business in (
            (client.calls[:4], "a", "business-a"),
            (client.calls[4:], "b", "business-b"),
        ):
            for call in group:
                cookie = call["headers"]["Cookie"]
                self.assertIn("STOKEN=web-%s" % marker, cookie)
                self.assertIn("PTOKEN=ptoken-%s" % marker, cookie)
                self.assertIn("BAIDUID=baiduid-%s" % marker, cookie)
                self.assertIn("PANPSC=panpsc-%s" % marker, cookie)
                self.assertNotIn(business, cookie)
                self.assertNotIn("global-business-must-not-be-used", cookie)

    def test_multi_account_line_format_preserves_extras(self):
        raw = (
            "账号甲|BDUSS=BDUSS-AAAA; STOKEN=web-a; PTOKEN=ptoken-a; "
            "BAIDUID=baiduid-a; PANPSC=panpsc-a|business-a\n"
            "账号乙|BDUSS=BDUSS-BBBB; STOKEN=web-b; PTOKEN=ptoken-b; "
            "BAIDUID=baiduid-b; PANPSC=panpsc-b|business-b"
        )
        with mock.patch.dict(os.environ, {"KUKU_TOKENS": raw}, clear=True):
            accounts = KD.load_accounts()

        self.assertEqual(2, len(accounts))
        self.assertEqual("web-a", accounts[0]["web_stoken"])
        self.assertEqual("business-b", accounts[1]["business_stoken"])
        self.assertIn(("BAIDUID", "baiduid-a"), accounts[0]["extras"])
        self.assertIn(("PANPSC", "panpsc-b"), accounts[1]["extras"])

    def test_mask_keeps_only_last_four_characters(self):
        self.assertEqual("********3456", KD.mask("BDUSS-123456"))

    def test_cookie_loader_splits_web_and_business_stokens(self):
        raw = (
            "BDUSS=BDUSS-123456; STOKEN=web-stoken-value; "
            "PTOKEN=ptoken-value; BAIDUID=baiduid-value; PANPSC=panpsc-value"
        )
        with mock.patch.dict(os.environ, {
                "KUKU_COOKIES": raw,
                "KUKU_STOKEN": "business-stoken-value",
        }, clear=True):
            accounts = KD.load_accounts()

        self.assertEqual(1, len(accounts))
        self.assertEqual("web-stoken-value", accounts[0]["web_stoken"])
        self.assertEqual("business-stoken-value", accounts[0]["business_stoken"])
        self.assertEqual("ptoken-value", accounts[0]["ptoken"])
        self.assertIn(("BAIDUID", "baiduid-value"), accounts[0]["extras"])
        self.assertIn(("PANPSC", "panpsc-value"), accounts[0]["extras"])
        self.assertEqual(
            ("BDUSS-123456", "ptoken-value", [
                ("BAIDUID", "baiduid-value"),
                ("PANPSC", "panpsc-value"),
            ]),
            KD.parse_cookie(raw),
        )

    def test_version_is_1_3_0(self):
        self.assertEqual("1.3.0", KD.VERSION)

    def test_cookie_rows_to_header_keeps_login_extras(self):
        rows = [
            (".baidu.com", "BDUSS", "bduss-value"),
            (".baidu.com", "STOKEN", "web-stoken-value"),
            (".baidu.com", "PTOKEN", "ptoken-value"),
            (".baidu.com", "BAIDUID", "baiduid-value"),
            (".baidu.com", "PANPSC", "panpsc-value"),
            (".baidu.com", "Hm_lvt_x", "analytics"),
            (".baidu.com", "HMACCOUNT", "analytics"),
            (".example.com", "OTHER", "ignored"),
        ]
        self.assertEqual(
            "BDUSS=bduss-value; STOKEN=web-stoken-value; PTOKEN=ptoken-value; "
            "BAIDUID=baiduid-value; PANPSC=panpsc-value",
            GC.cookie_rows_to_header(rows),
        )


class DocumentationContractTests(unittest.TestCase):
    def test_six_language_docs_use_30_day_main_flow(self):
        files = [
            ROOT / "README.md",
            ROOT / "docs" / "README.en.md",
            ROOT / "docs" / "README.zh-Hant.md",
            ROOT / "docs" / "README.ja.md",
            ROOT / "docs" / "README.ko.md",
            ROOT / "docs" / "README.pt-BR.md",
        ]
        for path in files:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIn("v1.3.0", text)
                self.assertIn("--legacy-freepoint", text)
                self.assertIn("30", text)

    def test_protocol_documents_strict_contract(self):
        text = (ROOT / "docs" / "PROTOCOL.md").read_text(encoding="utf-8")
        self.assertIn("v1.3.0", text)
        self.assertIn("3055f416841c1393ec04294a702603fd41e840aa", text)
        self.assertIn("aid=15459", text)
        self.assertIn("data.signed_today is true", text)
        self.assertIn("errno=10152", text)
        self.assertIn("errno=8001", text)
        self.assertIn("errno=8002", text)


if __name__ == "__main__":
    unittest.main()
