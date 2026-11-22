#!/usr/bin/env python3
# 用途：把 db-upgrade harness 以 git plumbing 方式部署到指定分支（保持远端为权威基线）。
# 用法：python deploy_dbupgrade_to_branch.py <api|backend> <target_branch>
import os
import subprocess
import sys

key, target = sys.argv[1:3]
CFGS = {
    "api": dict(path=r"D:\work\IdeaProjects\car-monit-api-jdk25",
                source=r"D:\work\IdeaProjects\car-monit-api-jdk25",
                files=[".github/workflows/db-upgrade-cloud.yml",
                       "scripts/v3/ops/dbupgrade/db_cell.sh",
                       "scripts/v3/ops/dbupgrade/db_dump.sh",
                       "scripts/v3/ops/dbupgrade/gate.py",
                       "scripts/v3/ops/dbupgrade/report.py",
                       "docs/v3/review/12-db-upgrade-verification.md"]),
    "backend": dict(path=r"D:\work\IdeaProjects\car-monit-backend-jdk25",
                    source=r"D:\work\IdeaProjects\car-monit-backend-jdk25",
                    files=[".github/workflows/db-upgrade-cloud.yml",
                           "scripts/v3/ops/dbupgrade/db_cell.sh",
                           "scripts/v3/ops/dbupgrade/db_dump.sh",
                           "scripts/v3/ops/dbupgrade/gate.py",
                           "scripts/v3/ops/dbupgrade/report.py"]),
}
cfg = CFGS[key]
repo = cfg["path"]
src = cfg["source"]
tref = "refs/remotes/origin/" + target


def git(*a, cwd=repo, input=None):
    if isinstance(input, bytes):
        return subprocess.run(["git", "-C", cwd, *a], input=input, capture_output=True)
    return subprocess.run(["git", "-C", cwd, *a], input=input, capture_output=True,
                          text=True, errors="replace")


# 确保拿到最新远端 ref。
git("fetch", "origin", target)
base = git("rev-parse", tref).stdout.strip()
if not base:
    sys.exit("no target ref " + tref)
print("%s/%s base=%s" % (key, target, base[:10]))

blobs = {}
for f in cfg["files"]:
    raw = open(os.path.join(src, f), "rb").read()
    if f.endswith(".sh"):
        raw = raw.replace(b"\r\n", b"\n")
    h = git("hash-object", "-w", "--stdin", input=raw)
    if h.returncode:
        sys.exit("hash-object failed for " + f)
    blobs[f] = h.stdout.decode().strip()

env = os.environ.copy()
idx = os.path.join(os.environ.get("TEMP", "/tmp"), "idx_dbup_%s_%s" % (key, target))
env["GIT_INDEX_FILE"] = idx
subprocess.run(["git", "-C", repo, "read-tree", base], env=env, check=True, capture_output=True)
for f, blob in blobs.items():
    subprocess.run(["git", "-C", repo, "update-index", "--add", "--cacheinfo",
                    "100644,%s,%s" % (blob, f)], env=env, check=True, capture_output=True)
tree = subprocess.run(["git", "-C", repo, "write-tree"], env=env, capture_output=True,
                      text=True, check=True).stdout.strip()
os.remove(idx)
c = git("commit-tree", tree, "-p", base, "-m",
        "ci(dbupgrade): deploy DB upgrade verification harness")
if c.returncode:
    sys.exit("commit-tree failed: " + c.stderr)
sha = c.stdout.strip()
git("update-ref", tref, sha)
print("committed %s -> %s (%d files)" % (target, sha[:10], len(blobs)))
