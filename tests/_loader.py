import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name, filename):
    path = ROOT / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeHttp:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, url, headers=None, body=None, timeout=30, opener=None):
        self.calls.append({
            "method": method,
            "url": url,
            "headers": headers or {},
            "body": body,
            "timeout": timeout,
            "opener": opener,
        })
        if not self.responses:
            raise AssertionError("unexpected request: %s %s" % (method, url))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        status, payload = response
        if isinstance(payload, str):
            text = payload
        else:
            text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        return status, text
