"""Bring a single-node Garage to the state in Git: one layout role, then per client an S3 key
imported from OpenBao and a bucket of the same name it owns. Safe to run again: each step
checks first and changes nothing when already done."""

import json
import os
import time
import urllib.error
import urllib.request

URL = os.environ["GARAGE_ADMIN_URL"]
TOKEN = os.environ["admin_token"]


def call(method, path, body=None):
    req = urllib.request.Request(
        URL + "/v2/" + path,
        method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        raw = r.read()
        return json.loads(raw) if raw else None


def get_or_none(path):
    try:
        return call("GET", path)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def wait_for_garage():
    for _ in range(60):
        try:
            return call("GET", "GetClusterStatus")
        except (urllib.error.URLError, ConnectionError):
            time.sleep(5)
    raise SystemExit("garage admin API not reachable")


def ensure_layout(status, capacity_bytes):
    node = status["nodes"][0]["id"]
    layout = call("GET", "GetClusterLayout")
    if any(r["id"] == node for r in layout["roles"]):
        print("layout: node already has a role")
        return
    call("POST", "UpdateClusterLayout",
         {"roles": [{"id": node, "zone": "home", "capacity": capacity_bytes, "tags": []}]})
    call("POST", "ApplyClusterLayout", {"version": layout["version"] + 1})
    print(f"layout: assigned {node[:16]} with {capacity_bytes} bytes")


def ensure_client(name):
    key_id = os.environ[f"{name}_key_id"]
    if get_or_none(f"GetKeyInfo?id={key_id}") is None:
        call("POST", "ImportKey", {"accessKeyId": key_id,
                                   "secretAccessKey": os.environ[f"{name}_secret_key"], "name": name})
        print(f"{name}: key imported")
    bucket = get_or_none(f"GetBucketInfo?globalAlias={name}")
    if bucket is None:
        bucket = call("POST", "CreateBucket", {"globalAlias": name})
        print(f"{name}: bucket created")
    # granting an existing permission again is a no-op
    call("POST", "AllowBucketKey", {"bucketId": bucket["id"], "accessKeyId": key_id,
                                    "permissions": {"read": True, "write": True, "owner": True}})
    print(f"{name}: key owns bucket")


if __name__ == "__main__":
    ensure_layout(wait_for_garage(), int(os.environ["CAPACITY_GB"]) * 10**9)
    for client in os.environ["CLIENTS"].split():
        ensure_client(client)
