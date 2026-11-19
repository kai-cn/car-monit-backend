#!/usr/bin/env python3
# 用途：把 parity 夹具/探针部署到 V3 分支（这些分支原本没有 parity 目录）。
# 用法：python deploy_parity_assets_v3.py <api|backend> <target_branch>
import os
import subprocess
import sys

key, target = sys.argv[1:3]
CFGS = {
    "api": dict(repo=r"D:\work\IdeaProjects\car-monit-api-jdk25",
                src=r"D:\work\IdeaProjects\car-monit-api-jdk25",
                files=["scripts/v3/ops/parity/parity_probe.py",
                       "scripts/v3/ops/parity/parity_compare.py",
                       "scripts/v3/ops/parity/endpoints/api.txt",
                       "scripts/v3/ops/parity/sql/mysql_dict.sql",
                       "scripts/v3/ops/parity/sql/schema_jl_data01.sql",
                       "scripts/v3/ops/parity/sql/seed_jl_data01.sql.gz"]),
    "backend": dict(repo=r"D:\work\IdeaProjects\car-monit-backend-jdk25",
                    src=r"D:\work\IdeaProjects\car-monit-backend-jdk25",
                    files=["scripts/v3/ops/parity/parity_probe.py",
                           "scripts/v3/ops/parity/parity_compare.py",
                           "scripts/v3/ops/parity/endpoints/backend.txt",
                           "scripts/v3/ops/parity/sql/schema_carmonitdb.sql",
                           "scripts/v3/ops/parity/sql/seed_carmonitdb.sql"]),
}
cfg = CFGS[key]
repo, src = cfg["repo"], cfg["src"]
tref = "refs/remotes/origin/" + target

def git(*a, binary=False, **kw):
    if binary:
        return subprocess.run(["git", "-C", repo, *a], capture_output=True, **kw)
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True,
                          errors="replace", **kw)

git("fetch", "origin", target)
base = git("rev-parse", tref).stdout.strip()
if not base:
    sys.exit("no ref " + tref)
print("%s/%s base=%s" % (key, target, base[:10]))

blobs = {}
for f in cfg["files"]:
    raw = open(os.path.join(src, f), "rb").read()
    h = git("hash-object", "-w", "--stdin", binary=True, input=raw)
    if h.returncode:
        sys.exit("hash-object failed " + f)
    blobs[f] = h.stdout.decode().strip()
    print("  blob", f, len(raw))

env = os.environ.copy()
idx = os.path.join(os.environ.get("TEMP", "/tmp"), "idx_parity_v3_%s_%s" % (key, target))
env["GIT_INDEX_FILE"] = idx
subprocess.run(["git", "-C", repo, "read-tree", base], env=env, check=True, capture_output=True)
for f, blob in blobs.items():
    subprocess.run(["git", "-C", repo, "update-index", "--add", "--cacheinfo",
                    "100644,%s,%s" % (blob, f)], env=env, check=True, capture_output=True)
tree = subprocess.run(["git", "-C", repo, "write-tree"], env=env, capture_output=True,
                      text=True, check=True).stdout.strip()
os.remove(idx)
c = git("commit-tree", tree, "-p", base, "-m", "test(dbupgrade): deploy parity fixtures to V3 branch")
sha = c.stdout.strip()
git("update-ref", tref, sha)
print("committed %s -> %s (%d files)" % (target, sha[:10], len(blobs)))
