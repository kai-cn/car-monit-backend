#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Apply a targeted configuration/source patch produced during the native/CICD investigation.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
from pathlib import Path
p = Path(r'D:\work\runtime-logs\DruidConfig-plain.java')
t = p.read_text(encoding='utf-8')

if 'import org.springframework.beans.factory.annotation.Value;' not in t:
    t = t.replace('import org.springframework.context.annotation.Bean;',
                  'import org.springframework.beans.factory.annotation.Value;\nimport org.springframework.context.annotation.Bean;', 1)

fields = '''
    @Value("${spring.datasource.druid.master.url}")
    private String masterUrl;
    @Value("${spring.datasource.druid.master.username}")
    private String masterUsername;
    @Value("${spring.datasource.druid.master.password}")
    private String masterPassword;
    @Value("${spring.datasource.druid.master.driverClassName:com.mysql.cj.jdbc.Driver}")
    private String masterDriverClassName;
'''
needle_class = 'public class DruidConfig\n{\n'
if 'private String masterUrl;' not in t:
    t = t.replace(needle_class, needle_class + fields, 1)

old = '''        DruidDataSource dataSource = DruidDataSourceBuilder.create().build();
        return druidProperties.dataSource(dataSource);'''
new_master = '''        DruidDataSource dataSource = new DruidDataSource();
        dataSource.setUrl(masterUrl);
        dataSource.setUsername(masterUsername);
        dataSource.setPassword(masterPassword);
        dataSource.setDriverClassName(masterDriverClassName);
        return druidProperties.dataSource(dataSource);'''
# replace first occurrence only (master); slave stays as-is
if new_master not in t:
    t = t.replace(old, new_master, 1)
p.write_text(t, encoding='utf-8')
print('patched plain+@Value', '@Value("${spring.datasource.druid.master.url}")' in t)
