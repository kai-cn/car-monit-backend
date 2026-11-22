#!/usr/bin/env python3
"""
@description 历史脚本 patch-druid-config2.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python patch-druid-config2.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Apply a targeted configuration/source patch produced during the native/CICD investigation.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
from pathlib import Path
p = Path(r'D:\work\runtime-logs\DruidConfig-original.java')
t = p.read_text(encoding='utf-8')

# import Environment
needle_import = 'import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;'
if 'import org.springframework.core.env.Environment;' not in t:
    t = t.replace(needle_import, 'import org.springframework.core.env.Environment;\n' + needle_import, 1)

# autowired environment
needle_class = 'public class DruidConfig\n{\n'
if 'private Environment environment;' not in t:
    t = t.replace(needle_class, needle_class + '    @Autowired\n    private Environment environment;\n\n', 1)
if 'import org.springframework.beans.factory.annotation.Autowired;' not in t:
    t = t.replace('import jakarta.servlet.ServletRequest;', 'import org.springframework.beans.factory.annotation.Autowired;\nimport jakarta.servlet.ServletRequest;', 1)

old_master = 'DruidDataSource dataSource = DruidDataSourceBuilder.create().build();\n        return druidProperties.dataSource(dataSource);'
new_master = ('DruidDataSource dataSource = DruidDataSourceBuilder.create().build();\n'
              '        applyConnectionProperties(dataSource, "master");\n'
              '        return druidProperties.dataSource(dataSource);')
t = t.replace(old_master, new_master)

helper = '''
    private void applyConnectionProperties(DruidDataSource ds, String prefix)
    {
        String base = "spring.datasource.druid." + prefix + ".";
        ds.setUrl(environment.getProperty(base + "url"));
        ds.setUsername(environment.getProperty(base + "username"));
        ds.setPassword(environment.getProperty(base + "password"));
        ds.setDriverClassName(environment.getProperty(base + "driverClassName"));
    }
'''
t = t.replace('\n    /**\n     * 设置数据源', helper + '\n    /**\n     * 设置数据源', 1)
p.write_text(t, encoding='utf-8')
print('patched', 'applyConnectionProperties' in t)
