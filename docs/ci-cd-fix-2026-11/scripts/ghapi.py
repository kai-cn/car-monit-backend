#!/usr/bin/env python3
"""GitHub Actions 只读诊断工具：查询 workflow runs / jobs / logs。

用法：
  export GH_TOKEN_OVERRIDE=<有效 PAT>   # 若仓库 remote 里的 token 已失效
  python3 ghapi.py runs  <backend|api> <workflow.yml> [条数] [branch]
  python3 ghapi.py jobs  <backend|api> <run_id>
  python3 ghapi.py log   <backend|api> <job_id> [grep关键字]

token 来源优先级：环境变量 GH_TOKEN_OVERRIDE > 本地仓库 git remote 中的 oauth2 token。
"""
import sys, os, json, urllib.request, urllib.error, base64, subprocess

REPOS = {"backend": "/workspace/cbm", "api": "/workspace/cbm-api"}
FULL = {"backend": "kai-cn/car-monit-backend", "api": "kai-cn/car-monit-api"}


def token(repo):
    if os.environ.get("GH_TOKEN_OVERRIDE"):
        return os.environ["GH_TOKEN_OVERRIDE"]
    url = subprocess.check_output(["git", "-C", REPOS[repo], "remote", "get-url", "origin"], text=True).strip()
    return url.split("oauth2:", 1)[1].split("@", 1)[0]


def api(path, repo="backend", method="GET"):
    req = urllib.request.Request("https://api.github.com" + path, method=method)
    req.add_header("Authorization", "Basic " + base64.b64encode(("oauth2:" + token(repo)).encode()).decode())
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "ghapi-diag")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode()), r.status
    except urllib.error.HTTPError as e:
        return {"_error": e.read().decode()[:500], "_status": e.code}, e.code


def runs(repo, wf, n=15, branch=None):
    data, _ = api(f"/repos/{FULL[repo]}/actions/workflows/{wf}/runs?per_page={n}", repo)
    if "_error" in data:
        print("ERR", data); return
    for r in data.get("workflow_runs", []):
        if branch and r["head_branch"] != branch:
            continue
        print(f"{r['id']}\t{r.get('conclusion') or r['status']}\t{r['head_branch']}\t{r['event']}\t{r['created_at']}\t{r['html_url']}")


def jobs(repo, run_id):
    data, _ = api(f"/repos/{FULL[repo]}/actions/runs/{run_id}/jobs?per_page=100", repo)
    if "_error" in data:
        print("ERR", data); return
    for j in data.get("jobs", []):
        print(f"{j['id']}\t{j['name']}\t{j.get('conclusion') or j['status']}\t{j['started_at']}")


def log(repo, job_id, grep=None):
    tok = token(repo)
    out = subprocess.run(
        ["curl", "-sL", "--retry", "3", "-u", "oauth2:" + tok,
         "-H", "Accept: application/vnd.github+json",
         f"https://api.github.com/repos/{FULL[repo]}/actions/jobs/{job_id}/logs"],
        capture_output=True)
    text = out.stdout.decode("utf-8", "replace")
    lines = [l for l in text.splitlines() if grep.lower() in l.lower()] if grep else text.splitlines()
    for l in (lines[-80:] if grep else lines[-200:]):
        print(l)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "runs":
        runs(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 15, sys.argv[5] if len(sys.argv) > 5 else None)
    elif cmd == "jobs":
        jobs(sys.argv[2], sys.argv[3])
    elif cmd == "log":
        log(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
