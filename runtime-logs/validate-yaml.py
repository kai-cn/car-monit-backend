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
