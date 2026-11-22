#!/usr/bin/env python3

"""
@description 历史脚本 fix-h8-typealiases.py：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python fix-h8-typealiases.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
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

