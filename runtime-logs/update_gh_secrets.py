#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Update an existing remote/local value in place.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""Rotate GitHub Actions Secrets after external credential rotation.

Usage:
  1) Create a local values file (NEVER put it in any repo / git dir):
       D:\work\runtime-logs\secret-values.env
     with one KEY=VALUE per line, e.g.:
       JWT_SECRET=myNewRandomValue
       OSS_ACCESS_KEY=myNewAk
       ALIYUN_SMS_ACCESS_KEY_SECRET=myNewSk
     Only include the secrets you are updating. Values are read from this file,
     never printed, and the file is not committed anywhere.
  2) Run: python update_gh_secrets.py <repo: api|backend|both>

Supported repo -> secret name mapping (the ones that need rotation):
  api:     CI_OPENGAUSS_PASSWORD, SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD,
           CI_INTERNAL_TOKEN, TRAFFIC_INTERNAL_TOKEN
  backend: JWT_SECRET, OSS_ACCESS_KEY, OSS_SECRET_KEY, HENDA_SECRET,
           ALIYUN_SMS_ACCESS_KEY_ID, ALIYUN_SMS_ACCESS_KEY_SECRET,
           DRUID_LOGIN_USERNAME, DRUID_LOGIN_PASSWORD,
           SPRING_DATASOURCE_DRUID_MASTER_PASSWORD, CI_MYSQL_PASSWORD,
           EXPORT_DOWNLOAD_SECRET, CI_EXPORT_SECRET,
           TRAFFIC_API_INTERNAL_TOKEN, CI_INTERNAL_TOKEN

NOTE: CI_INTERNAL_TOKEN (api) and TRAFFIC_API_INTERNAL_TOKEN (backend) must be the
SAME value as each other; set both keys in the env file to the same new token.
"""
import base64, json, os, subprocess, sys, tempfile, urllib.request, urllib.error
from nacl.public import SealedBox, PublicKey

API = "https://api.github.com"
REPOS = {"api": "kai-cn/car-monit-api", "backend": "kai-cn/car-monit-backend"}
VALUES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secret-values.env")


def get_token():
    # Fixed account (kai-cn) cached token; avoids GCM account picker.
    from gh_cred import get_token as _cached_get_token
    return _cached_get_token()

def load_values():
    vals = {}
    with open(VALUES_FILE, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip()
    return vals


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "both"
    if target not in ("api", "backend", "both"):
        print("usage: python update_gh_secrets.py <api|backend|both>")
        sys.exit(2)
    if not os.path.exists(VALUES_FILE):
        print("MISSING values file:", VALUES_FILE)
        print("Create it with KEY=VALUE lines (see script docstring).")
        sys.exit(2)

    vals = load_values()
    if not vals:
        print("No KEY=VALUE entries found in", VALUES_FILE)
        sys.exit(2)

    tok = get_token()
    if not tok:
        print("NO_TOKEN")
        sys.exit(1)
    headers = {"Authorization": "Bearer " + tok, "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "carmonit-secret-rotate"}

    def api_call(method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode(errors="replace")

    repos = [REPOS[target]] if target != "both" else list(REPOS.values())
    for repo in repos:
        print("== %s ==" % repo)
        for name, value in vals.items():
            st, key = api_call("GET", "/repos/%s/actions/secrets/public-key" % repo)
            if st != 200:
                print("  [ERR] public-key", st)
                continue
            pk = PublicKey(base64.b64decode(key["key"]))
            enc = base64.b64encode(SealedBox(pk).encrypt(value.encode())).decode()
            st, resp = api_call("PUT", "/repos/%s/actions/secrets/%s" % (repo, name),
                                {"encrypted_value": enc, "key_id": key["key_id"]})
            print("  [%s] %s" % ("OK" if st in (201, 204) else "ERR " + str(st), name))

    print("Done. Reminder: delete secret-values.env after use if it holds live values.")
    print("Location:", VALUES_FILE)


if __name__ == "__main__":
    main()
