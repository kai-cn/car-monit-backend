#!/usr/bin/env python3
"""Complete confirmed non-200 fixes in WSL master and retest harness.

@description 修复生成器/导出空数据空指针，补本机 sys_upgrade_info fixture 与环境变量。
@author Tencent Hunyuan Hy
@date 2026-11-23 07:38:02
@usage python3 runtime-logs/patch-remaining-non200-2.py
@dependencies WSL master clones 与 Python 3。
"""
import subprocess
from pathlib import Path

B = Path('/home/dev/IdeaProjects/car-monit-backend')
GEN = B / 'ruoyi-generator/src/main/java/com/ruoyi/generator/service/GenTableServiceImpl.java'
FLOW = B / 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowMessageInfoController.java'
SUS = B / 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSuspiciousController.java'
RETEST = Path('/mnt/d/work/runtime-logs/wsl-local-retest-with-downstream.py')


def replace(path, old, new):
    """Replace exact source text while preserving line endings."""
    raw = path.read_bytes()
    crlf = b'\r\n' in raw
    t = raw.decode('utf-8', errors='replace')
    if old not in t:
        print('NOT_FOUND', path, old[:60])
        return False
    t = t.replace(old, new)
    data = (t.replace('\r\n', '\n').replace('\n', '\r\n') if crlf else t).encode('utf-8')
    path.write_bytes(data)
    print('OK', path)
    return True


replace(GEN,
        '''        GenTable table = genTableMapper.selectGenTableById(tableId);
        // 过滤字段信息
        this.initFilterColumnInfo(table);
''',
        '''        GenTable table = genTableMapper.selectGenTableById(tableId);
        if (table == null) {
            return dataMap;
        }
        // 过滤字段信息
        this.initFilterColumnInfo(table);
''')
replace(GEN,
        '''        GenTable table = genTableMapper.selectGenTableByName(tableName);
        // 将字典的key转换成驼峰类型
''',
        '''        GenTable table = genTableMapper.selectGenTableByName(tableName);
        if (table == null) {
            return;
        }
        // 将字典的key转换成驼峰类型
''')
replace(FLOW,
        '''        FlowMessageInfo messageInfo = flowMessageInfoService.selectFlowMessageInfoById(flowMessageInfo.getId());
        map.put("applyName",messageInfo.getApplyName());
''',
        '''        FlowMessageInfo messageInfo = flowMessageInfoService.selectFlowMessageInfoById(flowMessageInfo.getId());
        if (messageInfo == null) {
            return AjaxResult.success(map);
        }
        map.put("applyName",messageInfo.getApplyName());
''')
replace(SUS,
        '''        CarSuspicious carSuspicious = carSuspiciousService.getById(carSuspiciousId);

        CarSuspiciousCheck querybo = new CarSuspiciousCheck();
''',
        '''        CarSuspicious carSuspicious = carSuspiciousService.getById(carSuspiciousId);
        if (carSuspicious == null) {
            carSuspicious = new CarSuspicious();
        }

        CarSuspiciousCheck querybo = new CarSuspiciousCheck();
''')

# Native fixture: create sys_upgrade_info if the local DB still lacks it.
sql = '''CREATE TABLE IF NOT EXISTS `sys_upgrade_info` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `ver` varchar(64) DEFAULT NULL,
  `info` text,
  `back_col1` varchar(255) DEFAULT NULL,
  `eps_id` bigint DEFAULT NULL,
  `del_flag` char(1) DEFAULT '0',
  `create_by` varchar(64) DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  `update_by` varchar(64) DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  `tenant_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''
r = subprocess.run(['docker', 'exec', '-i', 'mysql_wsl', 'mysql', '-uroot', '-proot', '-D', 'carmonitdb'],
                   input=sql, text=True, capture_output=True)
print('FIXTURE_RC', r.returncode, r.stderr[-200:])

# Retest harness: exclude Kafka autoconfiguration from api jar and pass export secret from environment.
replace(RETEST,
        '''                        '--spring.main.lazy-initialization=true'],
''',
        '''                        '--spring.main.lazy-initialization=true',
                        '--spring.autoconfigure.exclude=org.springframework.boot.autoconfigure.kafka.KafkaAutoConfiguration'],
''')
replace(RETEST,
        '''    'TOKEN__SECRET': 'junit-cloud-secret-deterministic-0123456789abcdef',
})
''',
        '''    'TOKEN__SECRET': 'junit-cloud-secret-deterministic-0123456789abcdef',
})
if os.environ.get('EXPORT_DOWNLOAD_SECRET'):
    base_env['EXPORT_DOWNLOAD_SECRET'] = os.environ['EXPORT_DOWNLOAD_SECRET']
''')
