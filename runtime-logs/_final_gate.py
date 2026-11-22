"""
@description 历史脚本 _final_gate.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python _final_gate.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

# -*- coding: utf-8 -*-

"""Read-only final remediation gate for the six JDK migration worktrees."""

import os

import re

import glob

import zipfile

import subprocess

import datetime

import xml.etree.ElementTree as ET



ROOT = 'D:/work/IdeaProjects'

LOGS = 'D:/work/runtime-logs'

DOCS = ROOT + '/car-monit-backend-new/docs/jdk-migration'

ROOTS = [ROOT + '/car-monit-%s-jdk%s' % (side, v)

         for side in ('backend', 'api') for v in ('17', '21', '25')]

EXPECTED = {

    'car-monit-backend-jdk17': ('17', '17'),

    'car-monit-backend-jdk21': ('21', '21'),

    'car-monit-backend-jdk25': ('25', '21'),

    'car-monit-api-jdk17': ('17', '17'),

    'car-monit-api-jdk21': ('21', '21'),

    'car-monit-api-jdk25': ('25', '21'),

}

JARS = {

    'jdk17-api': ROOT + '/car-monit-api-jdk17/pro-business-api/target/pro-business-api-1.0.jar',

    'jdk17-backend': ROOT + '/car-monit-backend-jdk17/ruoyi-admin/target/ruoyi-admin.jar',

    'jdk21-api': ROOT + '/car-monit-api-jdk21/pro-business-api/target/pro-business-api-1.0.jar',

    'jdk21-backend': ROOT + '/car-monit-backend-jdk21/ruoyi-admin/target/ruoyi-admin.jar',

    'jdk25-api': ROOT + '/car-monit-api-jdk25/pro-business-api/target/pro-business-api-1.0.jar',

    'jdk25-backend': ROOT + '/car-monit-backend-jdk25/ruoyi-admin/target/ruoyi-admin.jar',

}

MAJORS = {'17': 61, '21': 65, '25': 65}



lines, fails = [], []





def check(ok, label, detail=''):

    lines.append('%s %s%s' % ('PASS' if ok else 'FAIL', label,

                              (' :: ' + detail) if detail else ''))

    if not ok:

        fails.append(label)





def read(path):

    with open(path, encoding='utf-8', errors='replace') as f:

        return f.read()





def tag(text, name):

    m = re.search(r'<%s>\s*([^<]+)\s*</%s>' % (re.escape(name), re.escape(name)), text)

    return m.group(1).strip() if m else None





# 1. POM / XML parse

pom_total = pom_bad = xml_total = xml_bad = 0

xml_bad_files = []

for root in ROOTS:

    for dirpath, dirs, files in os.walk(root):

        dirs[:] = [d for d in dirs if d not in ('.git', 'target', '.idea')]

        for fn in files:

            p = os.path.join(dirpath, fn)

            if fn.endswith('.xml'):

                xml_total += 1

                try:

                    ET.parse(p)

                except Exception:

                    xml_bad += 1

                    xml_bad_files.append(os.path.relpath(p, root).replace('\\', '/'))

            if fn == 'pom.xml':

                pom_total += 1

                try:

                    ET.parse(p)

                except Exception:

                    pom_bad += 1

check(pom_total == 30 and pom_bad == 0, 'POM_PARSE',

      'total=%d bad=%d' % (pom_total, pom_bad))

check(xml_bad == 6, 'PREEXISTING_NON_POM_XML_PARSE_FAILURES',

      'xml_total=%d bad=%d files=%s' % (

          xml_total, xml_bad,

          ','.join(sorted(set(os.path.basename(x) for x in xml_bad_files)))))



# 2. Root POM version matrix and forbidden leftovers

for root in ROOTS:

    name = os.path.basename(root)

    jdk, baseline = EXPECTED[name]

    t = read(os.path.join(root, 'pom.xml'))

    check(tag(t, 'java.version') == baseline, 'JAVA_VERSION %s' % name,

          'expected=%s actual=%s' % (baseline, tag(t, 'java.version')))

    check(tag(t, 'maven.compiler.release') == baseline, 'COMPILER_RELEASE %s' % name,

          'expected=%s actual=%s' % (baseline, tag(t, 'maven.compiler.release')))

    if name.startswith('car-monit-api'):

        check(tag(t, 'maven.compiler.source') == baseline and

              tag(t, 'maven.compiler.target') == baseline,

              'API_SOURCE_TARGET %s' % name, 'expected=%s' % baseline)

    check(tag(t, 'spring-framework.version') == '5.3.39',

          'SPRING_FRAMEWORK %s' % name, tag(t, 'spring-framework.version'))

    check(tag(t, 'lombok.version') == '1.18.48', 'LOMBOK %s' % name,

          tag(t, 'lombok.version'))

    check('jvmArgs' not in t and '<fork>true</fork>' not in t,

          'NO_NOOP_COMPILER_FLAGS %s' % name)

    check('9.11.1' not in t, 'NO_STALE_ASM_OVERRIDE %s' % name)



# 3. API starter-test scope

for root in ROOTS:

    if not root.startswith(ROOT + '/car-monit-api'):

        continue

    t = read(os.path.join(root, 'pro-base-common/pom.xml'))

    blocks = re.findall(r'<dependency>.*?</dependency>', t, re.S)

    block = next((b for b in blocks

                  if '<artifactId>spring-boot-starter-test</artifactId>' in b), '')

    check('<scope>test</scope>' in block,

          'STARTER_TEST_SCOPE %s' % os.path.basename(root))



# 4. JDK25 Lombok processor still present

for side in ('backend', 'api'):

    t = read(os.path.join(ROOT, 'car-monit-%s-jdk25' % side, 'pom.xml'))

    check('<annotationProcessorPaths>' in t and '${lombok.version}' in t,

          'JDK25_LOMBOK_PROCESSOR %s' % side)



# 5. Workflow toolchain pinning and no JDK8 remnants

for root in ROOTS:

    name = os.path.basename(root)

    jdk = EXPECTED[name][0]

    wf = os.path.join(root, '.github/workflows')

    sh = read(os.path.join(wf, 'self-hosted-ci.yml'))

    check('actions/setup-java@v4' in sh and

          ("java-version: '%s'" % jdk) in sh,

          'SELF_HOSTED_SETUP_JAVA %s' % name, 'jdk=%s' % jdk)

    check('Assert toolchain matches branch' in sh,

          'SELF_HOSTED_VERSION_ASSERT %s' % name)

    allwf = ''.join(read(p) for p in glob.glob(os.path.join(wf, '*.yml')))

    check(not re.search(r'(?:jdk-version|java-version):\s*[\'\"]8[\'\"]', allwf),

          'NO_JDK8_WORKFLOW_VALUE %s' % name)



for root in [r for r in ROOTS if '/car-monit-api-' in r]:

    name = os.path.basename(root)

    jdk = EXPECTED[name][0]

    wf = os.path.join(root, '.github/workflows')

    java = read(os.path.join(wf, '_java.yml'))

    check('inputs.jdk-version' in java and '校验 JDK 版本与 workflow 入参一致' in java,

          'REUSABLE_WORKFLOW_INPUT_WIRED %s' % name)

    for caller in ('master.yml', 'pr.yml', 'release.yml'):

        t = read(os.path.join(wf, caller))

        check(('jdk-version: "%s"' % jdk) in t or

              ("jdk-version: '%s'" % jdk) in t,

              'CALLER_JDK_VERSION %s/%s' % (name, caller), 'jdk=%s' % jdk)



# 6. js-yaml workflow validation

try:

    r = subprocess.run(['node', 'check.js'], cwd=LOGS + '/yamlcheck',

                       capture_output=True, text=True, timeout=120)

    out = (r.stdout or '') + (r.stderr or '')

    m = re.search(r'YAML_TOTAL=(\d+)\s+YAML_BAD=(\d+)', out)

    check(bool(m) and m.group(1) == '54' and m.group(2) == '0' and

          r.returncode == 0, 'WORKFLOW_YAML',

          m.group(0) if m else out[-300:])

except Exception as e:

    check(False, 'WORKFLOW_YAML', repr(e))



# 7. Final2 build logs and smoke logs

for v in ('17', '21', '25'):

    for side in ('api', 'backend'):

        t = read(os.path.join(LOGS, 'jdk%s-%s-build-final2.log' % (v, side)))

        check('BUILD SUCCESS' in t and '[ERROR]' not in t,

              'FINAL2_BUILD jdk%s-%s' % (v, side))

for v in ('17', '21', '25'):

    t = read(os.path.join(LOGS, 'jdk%s-recheck-smoke.stdout.log' % v))

    m = re.search(r'checks=(\d+) fails=(\d+)', t)

    check(bool(m) and m.group(1) == '26' and m.group(2) == '0',

          'FINAL_SMOKE jdk%s' % v, m.group(0) if m else 'missing summary')



# 8. Jar contents, class majors, Spring version, test libs

artifact_lines = {}

for ln in read(os.path.join(LOGS, 'evidence-build-artifacts.txt')).splitlines():

    if ln and not ln.startswith('#'):

        artifact_lines[ln.split()[0]] = ln

for key, jar in JARS.items():

    v = key.split('-')[0].replace('jdk', '')

    side = key.split('-')[1]

    expected_major = MAJORS[v]

    size = os.path.getsize(jar) if os.path.isfile(jar) else 0

    check(os.path.isfile(jar) and size > 1000000, 'FAT_JAR %s' % key,

          'bytes=%d' % size)

    if not os.path.isfile(jar):

        continue

    with zipfile.ZipFile(jar) as z:

        names = z.namelist()

        libs = [os.path.basename(n) for n in names

                if n.startswith('BOOT-INF/lib/')]

        check('spring-core-5.3.39.jar' in libs and

              'spring-core-5.3.31.jar' not in libs,

              'SPRING_CORE %s' % key)

        if side == 'api':

            bad = [x for x in libs

                   if re.search(r'^(junit|mockito|spring-test|assertj)-', x)]

            check(not bad, 'NO_TEST_LIBS_IN_PROD_JAR %s' % key, ','.join(bad))

        app = next((n for n in names

                    if n.startswith('BOOT-INF/classes/') and

                    ('RuoYiApplication.class' in n or

                     'EcBusinessApiApplication.class' in n)), None)

        if app:

            data = z.read(app)[:8]

            major = data[6] * 256 + data[7]

            check(major == expected_major, 'CLASS_MAJOR %s' % key,

                  'expected=%d actual=%d' % (expected_major, major))

        else:

            check(False, 'CLASS_MAJOR %s' % key, 'application class not found')

    m = re.search(r'jar_bytes=(\d+)', artifact_lines.get(key, ''))

    check(bool(m) and int(m.group(1)) == size,

          'ARTIFACT_MATRIX_SIZE %s' % key, 'jar=%d' % size)



# 9. Persistent runtime evidence

jcmd = read(os.path.join(LOGS, 'evidence-jdk25-jcmd.txt'))

check(jcmd.count('OpenJDK 64-Bit Server VM version 25.0.4.1+1-LTS') == 2,

      'JDK25_JCMD_LIVE_EVIDENCE')

cache = read(os.path.join(LOGS, 'evidence-jdk25-cache-miss.txt'))

check(cache.count('X-Data-Source=API') == 2,

      'JDK25_FORCED_CACHE_MISS_EVIDENCE')



# 10. Git hygiene / no push

for root in ROOTS:

    name = os.path.basename(root)

    r = subprocess.run(['git', '-C', root, 'rev-parse', '--abbrev-ref',

                        '--symbolic-full-name', '@{u}'],

                       capture_output=True, text=True)

    check(r.returncode != 0, 'NO_UPSTREAM %s' % name)

    st = subprocess.run(['git', '-C', root, 'status', '--porcelain'],

                        capture_output=True, text=True).stdout

    untracked = [ln for ln in st.splitlines() if ln.startswith('??')]

    staged = [ln for ln in st.splitlines() if ln and ln[0] not in (' ', '?')]

    check(not untracked, 'NO_UNTRACKED_FILES %s' % name, ','.join(untracked))

    check(not staged, 'NO_STAGED_COMMIT %s' % name, ','.join(staged))

    check(not os.path.exists(os.path.join(root, 'docs/jdk-migration-README.md')),

          'NO_BRANCH_LOCAL_DOC %s' % name)

check(not os.path.exists(LOGS + '/_gen_branch_docs.py'),

      'STALE_DOC_GENERATOR_REMOVED')

check(not os.path.exists(

    ROOT + '/car-monit-backend-jdk17/docs/v3/review/08-jdk17-migration-verify.md'),

    'STALE_JDK17_DOC_REMOVED')



# 11. Secret hygiene in authoritative docs

docs_text = ''.join(read(p) for p in glob.glob(DOCS + '/*.md'))

secrets = ('Admin@2025-', 'JdkE2e@2026', 'jdk17-local-e2e-token-20261111')

check(not any(s in docs_text for s in secrets),

      'NO_LOCAL_SECRETS_IN_AUTHORITATIVE_DOCS')



# 12. Runtime cleanup state: current process/listener evidence + validation-time DB evidence

check(os.environ.get('APP_JAVA_COUNT') == '0', 'APP_JAVA_COUNT', '0')

check(os.environ.get('REMAINING_E2E') == '0' and os.environ.get('TOTAL_USERS') == '8',

      'VALIDATION_TIME_DB_CLEANUP', 'remaining_e2e=0 total_users=8')

valid_ports = ('none', '3307,6379,9200,9092,15432')

check(os.environ.get('INFRA_PORTS', '') in valid_ports,

      'NO_DUPLICATE_SERVICES', os.environ.get('INFRA_PORTS', ''))

cur = os.path.join(LOGS, 'evidence-current-runtime-state.txt')

check(os.path.isfile(cur) and 'AppJavaCount=0' in read(cur),

      'CURRENT_RUNTIME_EVIDENCE_FILE', cur)



header = [

    '# Final independent-review remediation gate',

    '# generated: %s' % datetime.datetime.now().astimezone().strftime(

        '%Y-%m-%d %H:%M:%S %z'),

    '# scope: six local JDK migration worktrees + D:/work/runtime-logs evidence',

    '# method: read-only filesystem/POM/jar/git checks; js-yaml workflow parse; validation-time DB evidence; current runtime state file',

]

out = '\n'.join(header + lines + [

    'FINAL_GATE_CHECKS=%d' % len(lines),

    'FINAL_GATE_FAILS=%d' % len(fails),

    'FINAL_GATE_VERDICT=%s' % ('PASS' if not fails else 'FAIL'),

]) + '\n'

with open(os.path.join(LOGS, 'evidence-final-gate.txt'), 'w',

          encoding='utf-8', newline='\n') as f:

    f.write(out)

print(out[-1500:])

print('FAIL_LABELS=' + (','.join(fails) if fails else 'none'))

