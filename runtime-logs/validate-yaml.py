"""
@description 历史脚本 validate-yaml.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python validate-yaml.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

import sys

try:

    import yaml

except ImportError:

    print("PY_YAML_MISSING")

    sys.exit(3)

ok = True

for f in sys.argv[1:]:

    try:

        with open(f, encoding="utf-8") as fh:

            yaml.safe_load(fh)

        print("OK  ", f)

    except Exception as e:

        ok = False

        print("FAIL", f, "->", type(e).__name__, e)

sys.exit(0 if ok else 1)

