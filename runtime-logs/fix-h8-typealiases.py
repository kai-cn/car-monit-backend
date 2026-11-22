#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：fix-h8-typealiases.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""H8: replace MyBatis package-scanning aliases with explicit native-safe class aliases."""
import json
from pathlib import Path

SRC = Path(r'D:\work\IdeaProjects\car-monit-backend-jdk25')
CFG = Path(r'D:\work\runtime-logs\MyBatisConfig.java')
REFLECT = Path(r'D:\work\runtime-logs\bk25-reflect-h8.json')
ALIASES = Path(r'D:\work\runtime-logs\NativeTypeAliases.java')

# Collect all top-level domain/bean classes from the source tree.
classes = set()
for f in SRC.rglob('*.java'):
    s = f.as_posix()
    if '/src/main/java/com/ruoyi/' not in s:
        continue
    if '/domain/' not in s and '/bean/' not in s:
        continue
    rel = s.split('/src/main/java/', 1)[1]
    classes.add(rel[:-5].replace('/', '.'))
classes = sorted(classes)
print('alias classes', len(classes))

lines = ['package com.ruoyi.framework.config;', '',
         '/** Native-safe MyBatis type alias class list (generated from com.ruoyi.**.domain/bean). */',
         'public final class NativeTypeAliases', '{',
         '    private NativeTypeAliases() {}', '',
         '    public static final String[] CLASSES = {']
for c in classes:
    lines.append(f'        "{c}",')
lines += ['    };', '}', '']
ALIASES.write_text('\n'.join(lines), encoding='utf-8')

t = CFG.read_text(encoding='utf-8')
old = '        sessionFactory.setTypeAliasesPackage(typeAliasesPackage);'
new = '''        // Native images cannot enumerate **/*.class resources, so MyBatis TypeAliasRegistry
        // cannot build aliases from the package string. Register the exact domain/bean classes
        // explicitly; the JVM path keeps the package string for diagnostics only.
        java.util.List<Class<?>> aliasClasses = new java.util.ArrayList<>();
        for (String className : NativeTypeAliases.CLASSES) {
            try {
                aliasClasses.add(Class.forName(className, false, MyBatisConfig.class.getClassLoader()));
            } catch (ClassNotFoundException ignored) {
                // Optional module not present in this branch; skip it.
            }
        }
        sessionFactory.setTypeAliases(aliasClasses.toArray(new Class<?>[0]));'''
if old in t:
    t = t.replace(old, new, 1)
CFG.write_text(t, encoding='utf-8')
print('MyBatisConfig patched', old not in t)

data = json.loads(REFLECT.read_text(encoding='utf-8'))
existing = {e.get('name') for e in data}
added = 0
for c in classes:
    if c not in existing:
        data.append({'name': c, 'allDeclaredConstructors': True,
                     'allDeclaredMethods': True, 'allDeclaredFields': True})
        added += 1
REFLECT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('reflect added', added, 'total', len(data))
