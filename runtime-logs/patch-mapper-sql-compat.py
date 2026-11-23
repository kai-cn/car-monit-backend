#!/usr/bin/env python3
"""
@description 修复 api Java/Python mapper 的 PostgreSQL 列名大小写与整数参数类型错误。
@author AI Assistant
@date 2026-11-23
@usage python3 runtime-logs/patch-mapper-sql-compat.py
@dependencies api master 的 Java/Python mapper XML；不访问网络。
"""
from pathlib import Path

REPO = Path('/home/dev/IdeaProjects/car-monit-api')
WEIGHT = 'OdsSzdnProvinceBorderVehicleWeightNewstructureMapper.xml'
FWQ = 'DwdLcztFwqjcxxMapper.xml'
PATHS = [
    REPO / 'pro-business-api/src/main/java/com/ruoyi/base/mapper/xml' / WEIGHT,
    REPO / 'car-monit-api-python/pro-business-api/src/main/resources/com/ruoyi/base/mapper/xml' / WEIGHT,
    REPO / 'pro-business-api/src/main/java/com/ruoyi/base/mapper/xml' / FWQ,
    REPO / 'car-monit-api-python/pro-business-api/src/main/resources/com/ruoyi/base/mapper/xml' / FWQ,
]
for p in PATHS:
    t = p.read_text(encoding='utf-8')
    if p.name == WEIGHT:
        for name in ['dataSource', 'dataType', 'plateNo', 'siteId', 'driveNo', 'plateColor',
                     'plateColorCode', 'plateType', 'plateTypeCode', 'vehicleColor',
                     'vehicleColorCode', 'vehicleType', 'vehicleTypeCode', 'vehicleSpeed',
                     'isOverweight', 'axleNum', 'overWeight', 'vehicleWeight', 'limitWeight',
                     'checkTimeUnix', 'checkTime', 'axleModel', 'loadRate', 'axleArray',
                     'weighingImagesArry', 'datauuid', 'reserve1', 'reserve2', 'reserve3']:
            t = t.replace(f't."{name}"', f't.{name.lower()}')
            t = t.replace(f't.{name} ', f't.{name.lower()} ')
        t = t.replace('column="dataSource"', 'column="datasource"')
    else:
        t = t.replace('where t.id = #{agentPk}', 'where t.id = CAST(#{agentPk} AS INTEGER)')
    p.write_text(t, encoding='utf-8')
    print('PATCHED', p)
