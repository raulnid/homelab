"""Runs bootstrap.py twice against a fake admin API: the first run sets everything up, the second
changes nothing. Run with: python3 bootstrap_test.py"""

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

state = {"version": 0, "roles": [], "keys": {}, "buckets": {}, "writes": []}


class Fake(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply(self, code, body=None):
        self.send_response(code)
        self.end_headers()
        if body is not None:
            self.wfile.write(json.dumps(body).encode())

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        assert self.headers["Authorization"] == "Bearer tok"
        if u.path == "/v2/GetClusterStatus":
            return self.reply(200, {"layoutVersion": state["version"], "nodes": [{"id": "a" * 64}]})
        if u.path == "/v2/GetClusterLayout":
            return self.reply(200, {"version": state["version"], "roles": state["roles"]})
        if u.path == "/v2/GetKeyInfo":
            return self.reply(200, {}) if q["id"] in state["keys"] else self.reply(404)
        if u.path == "/v2/GetBucketInfo":
            b = state["buckets"].get(q["globalAlias"])
            return self.reply(200, {"id": b}) if b else self.reply(404)
        self.reply(400)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        path = urlparse(self.path).path.removeprefix("/v2/")
        if path != "AllowBucketKey":
            state["writes"].append(path)
        if path == "UpdateClusterLayout":
            state["staged"] = body["roles"]
        elif path == "ApplyClusterLayout":
            assert body["version"] == state["version"] + 1
            state["version"], state["roles"] = body["version"], state.pop("staged")
        elif path == "ImportKey":
            state["keys"][body["accessKeyId"]] = body["secretAccessKey"]
        elif path == "CreateBucket":
            state["buckets"][body["globalAlias"]] = "id-" + body["globalAlias"]
            return self.reply(200, {"id": state["buckets"][body["globalAlias"]]})
        elif path == "AllowBucketKey":
            assert body["permissions"]["owner"] and body["accessKeyId"] in state["keys"]
        self.reply(200, {})


srv = HTTPServer(("127.0.0.1", 0), Fake)
threading.Thread(target=srv.serve_forever, daemon=True).start()
env = dict(os.environ, GARAGE_ADMIN_URL=f"http://127.0.0.1:{srv.server_port}", admin_token="tok",
           CAPACITY_GB="300", CLIENTS="longhorn cnpg",
           longhorn_key_id="GK1", longhorn_secret_key="s1", cnpg_key_id="GK2", cnpg_secret_key="s2")
script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bootstrap.py")

subprocess.run([sys.executable, "-I", script], env=env, check=True)
assert state["version"] == 1 and state["roles"][0]["capacity"] == 300 * 10**9
assert state["keys"] == {"GK1": "s1", "GK2": "s2"} and set(state["buckets"]) == {"longhorn", "cnpg"}
first = len(state["writes"])

subprocess.run([sys.executable, "-I", script], env=env, check=True)
assert len(state["writes"]) == first, state["writes"][first:]
print("ok: second run changed nothing")
