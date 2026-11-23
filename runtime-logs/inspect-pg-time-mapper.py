#!/usr/bin/env python3
"""Inspect PostgreSQL time arithmetic candidates in api mappers."""
from pathlib import Path
paths=[
 Path('/home/dev/IdeaProjects/car-monit-api/pro-business-api/src/main/java/com/ruoyi/base/mapper/xml/OdsLwzxsfsjFeeRecords01Mapper.xml'),
 Path('/home/dev/IdeaProjects/car-monit-api/car-monit-api-python/pro-business-api/src/main/resources/com/ruoyi/base/mapper/xml/OdsLwzxsfsjFeeRecords01Mapper.xml')]
for p in paths:
 print('===',p,'===')
 for i,l in enumerate(p.read_text(encoding='utf-8',errors='replace').splitlines(),1):
  if any(k in l.lower() for k in ['interval','timestamp','days',' - #{','- #{']): print(i,l.strip()[:300])
