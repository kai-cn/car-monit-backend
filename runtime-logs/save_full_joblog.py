#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Persist a job log or artifact for later inspection.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""Save full job log to a file (UTF-8) for grepping."""
import os, subprocess, sys, tempfile, urllib.request, urllib.error


def token():
    # Fixed account (kai-cn) cached token; avoids GCM account picker.
    from gh_cred import get_token as _cached_get_token
    return _cached_get_token()

repo, jid, outp = sys.argv[1], sys.argv[2], sys.argv[3]
url = 'https://api.github.com/repos/%s/actions/jobs/%s/logs' % (repo, jid)
req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token(),
                                           'Accept': 'application/vnd.github+json',
                                           'User-Agent': 'carmonit-log'})


class NR(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return urllib.request.Request(newurl, headers={'User-Agent': 'carmonit-log'})


data = urllib.request.build_opener(NR).open(req, timeout=60).read().decode(errors='replace')
open(outp, 'w', encoding='utf-8').write(data)
print('saved', len(data), 'chars ->', outp)
