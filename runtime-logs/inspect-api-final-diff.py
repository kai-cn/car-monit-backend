#!/usr/bin/env python3
"""Inspect final api diff against remote master."""
import subprocess
from pathlib import Path
A=Path('/home/dev/IdeaProjects/car-monit-api')
paths=['.github/workflows/crosslang-full-parity-cloud.yml','car-monit-api-cpp/src/service/track.cpp','car-monit-api-go/configs/config.yaml','car-monit-api-go/internal/repo/zdata_trail_tracks.go','car-monit-api-python/pro-business-api/src/main/resources/com/ruoyi/base/mapper/xml/ZdataTrailTracksMapper.xml','pro-business-api/src/main/java/com/ruoyi/base/mapper/xml/ZdataTrailTracksMapper.xml','pro-business-api/src/main/resources/application.yml','scripts/v3/ops/junit/generate_junit_suite.py']
for p in paths:
 print('===',p,'===')
 r=subprocess.run(['git','-C',str(A),'diff','--',p],text=True,capture_output=True)
 print((r.stdout or r.stderr)[:4000])
