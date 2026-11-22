#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""Add local SSH public key as a write deploy key to both repos via GitHub API."""
import base64
import json
import os
import subprocess
import tempfile
import urllib.request
import urllib.error

API = "https://api.github.com"

def get_token():
    # Fixed account (kai-cn) cached token; avoids GCM account picker.
    from gh_cred import get_token as _cached_get_token
    return _cached_get_token()

TOKEN = get_token()
HEADERS = {"Authorization": "Bearer " + TOKEN, "Accept": "application/vnd.github+json",
           "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "carmonit-deploykey"}

def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")

import sys
keyfile = sys.argv[1] if len(sys.argv) > 1 else "id_ed25519"
repos = [sys.argv[2]] if len(sys.argv) > 2 else ["kai-cn/car-monit-api", "kai-cn/car-monit-backend"]
pub = open(os.path.expanduser("~/.ssh/" + keyfile), encoding="utf-8").read().strip()
keytype, b64, *comment = pub.split()
fingerprint = base64.b64decode(b64)
import hashlib
fp = base64.b64encode(hashlib.md5(fingerprint).digest()).decode().rstrip("=")
print("key md5:", ":".join(fp[i:i+2] for i in range(0, len(fp), 2)))

for repo in repos:
    status, keys = api("GET", "/repos/%s/keys" % repo)
    already = False
    if status == 200:
        for k in keys:
            if k.get("key", "").split()[1] == b64:
                already = True
                print("already exists on", repo, "id", k["id"])
    if not already:
        status, resp = api("POST", "/repos/%s/keys" % repo,
                           {"title": "ci-push-key-20261116", "key": pub, "read_only": False})
        if status == 201:
            print("ADDED write deploy key to", repo, "id", resp.get("id"))
        else:
            print("ERR add key", repo, status, str(resp)[:300])
