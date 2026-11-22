#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Scan branches/workflows for a pattern or risk.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""Scan all jars in a Spring Boot fat jar for native-image.properties that define -H:Class= main classes."""
import io
import os
import re
import sys
import zipfile

PAT = re.compile(r"-H:Class\s*=\s*([\w.$]+)")


def main():
    jar = sys.argv[1]
    hits = []
    with zipfile.ZipFile(jar) as z:
        for n in z.namelist():
            if not (n.startswith("BOOT-INF/lib/") and n.endswith(".jar")):
                continue
            try:
                inner = zipfile.ZipFile(io.BytesIO(z.read(n)))
            except Exception:
                continue
            for rn in inner.namelist():
                if rn.endswith("native-image.properties"):
                    txt = inner.read(rn).decode("utf-8", "replace")
                    for m in PAT.finditer(txt):
                        hits.append((n, rn, m.group(1)))
    print("HITS=%d" % len(hits))
    for jarname, rn, cls in hits:
        print("%s | %s | %s" % (os.path.basename(jarname), rn, cls))


if __name__ == "__main__":
    sys.exit(main())
