#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Scan branches/workflows for a pattern or risk.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""Compact exposure matrix: which remote branches contain which sensitive values."""
import subprocess

VALS = {
    'henda': 'b48381c4b98311ea90b100155d14fa3b',
    'minioAK': 'jtwl_access_key',
    'minioSK': 'minio.prod',
    'druidPW': 'Sys#2024Test',
    'oldMyPW': 'carmonitUser@202507',
    'redisPW': 'redis321',
    'ogPW': 'OpenGauss@123',
    'aliyun1': 'LTAIh427',
    'aliyun2': 'LTAIP8qu',
    'aliyun3': 'LTAI4FpW',
    'ip_20_14': '36.200.20.14',
    'ip_30_117': '36.200.30.117',
    'ip_150_189': '223.84.150.189',
}
REPOS = [r'D:\work\IdeaProjects\car-monit-api-java-V3',
         r'D:\work\IdeaProjects\car-monit-backend-java-V3']

for repo in REPOS:
    br = subprocess.run(['git','-C',repo,'for-each-ref','--format=%(refname:short)',
                         'refs/remotes/origin'], capture_output=True, text=True).stdout.split()
    br = [b for b in br if b.startswith('origin/') and b not in ('origin','origin/HEAD')]
    print('\n########', repo.split('\\')[-1], '########')
    print('branch'.ljust(42), ' '.join(k[:6].ljust(7) for k in VALS))
    for b in br:
        hits = []
        for name, v in VALS.items():
            r = subprocess.run(['git','-C',repo,'grep','-q','-I','--fixed-strings',v,
                                'refs/remotes/'+b], capture_output=True)
            hits.append('Y'.ljust(7) if r.returncode == 0 else '.'.ljust(7))
        print(b.replace('origin/','').ljust(42), ' '.join(hits))
