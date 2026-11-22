#!/usr/bin/env python3

"""
@description 历史脚本 annotate_cicd.py：批量补充脚本或代码注释；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python annotate_cicd.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Docker CLI 与已启动的守护进程；Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""给 CI/CD workflow 和脚本加中文注释（文件头说明块 + 关键节点行内注释）。



- 只加注释，不改任何逻辑；基于远端 ref 读取、git plumbing 写回，避免覆盖 worktree 未提交改动。

- 按内容哈希去重：同一文件内容只注释一次，应用到所有含它的分支。

- 支持 --dry-run（默认，打印样例/统计）和 --apply（建 commit + 更新 ref）。

"""

import subprocess, hashlib, collections, os, re, sys, tempfile



APPLY = '--apply' in sys.argv

ONLY = None

if '--only' in sys.argv:

    ONLY = sys.argv[sys.argv.index('--only')+1].split(',')



REPOS = {

    'api': dict(repo=r'D:\work\IdeaProjects\car-monit-api-java-V3',

                branches=['car-monit-api-java-V3','car-monit-api-jdk17','car-monit-api-jdk21','car-monit-api-jdk25','master']),

    'backend': dict(repo=r'D:\work\IdeaProjects\car-monit-backend-java-V3',

                    branches=['car-monit-backend-java-V3','car-monit-backend-jdk17','car-monit-backend-jdk21','car-monit-backend-jdk25','master']),

}



# workflow 文件用途说明（按文件名）

WF_PURPOSE = {

    '_java.yml': 'Java 模块可复用工作流：编译/测试 JVM jar，被 master/pr 通过 workflow_call 调用',

    '_cpp.yml': 'C++ 模块可复用工作流：编译/测试 C++ 产物（linux/windows），供总入口调用',

    '_go.yml': 'Go 模块可复用工作流：go build + govulncheck 依赖漏洞门禁',

    '_python.yml': 'Python 模块可复用工作流：源码编译 Python + 单测（规避 openEuler ssl 问题）',

    '_rust.yml': 'Rust 模块可复用工作流：cargo build + test',

    '_image.yml': 'Docker 镜像可复用工作流：构建并推送容器镜像',

    'master.yml': '主分支 push 总入口：编排各语言 job 与 parity 门禁',

    'pr.yml': 'PR 校验入口：对各语言改动做编译/测试与一致性门禁',

    'release.yml': '发布流程：构建各语言产物并上传 GitHub Release（含 SHA256SUMS）',

    'self-hosted-ci.yml': '手动 CI/CD 入口：构建固定云 runner；部署 job 仅 owner + 手动 dispatch 可用',

    'deploy.yml': '部署 workflow：k3d 集群/单机部署入口',

    'cd.yml': '持续部署：构建镜像并部署到目标环境',

    'cd-standalone.yml': '单机部署：打包 standalone 产物并上传 Release',

    'deploy-selfhosted.yml': '自托管部署（已加 owner 守卫，仅手动触发）',

    'selfhost-canary.yml': '自托管 canary 冒烟（已加 owner 守卫）',

    'native-image-cloud.yml': '云 runner 构建 GraalVM/Mandrel native image；release_tag 入参可上传 Release',

    'native-image.yml': '自托管 native 构建（已加 owner 守卫）',

    'parity-verify-cloud.yml': '云上 native vs JVM 全接口 + 资源性能对比（jdk × 平台矩阵）',

    'crosslang-parity-cloud.yml': '跨语言（Go/Python/Rust）与 Java8 基线的全接口 + 资源对比',

}



# 关键 step 的中文注释（按 uses 或 name 关键词）

STEP_HINT = [

    ('actions/checkout', '拉取仓库源码'),

    ('setup-graalvm', '安装 GraalVM/Mandrel 与 native-image 工具链'),

    ('setup-java', '安装 JDK'),

    ('setup-python', '安装 Python'),

    ('download-artifact', '下载上游 workflow 产物'),

    ('upload-artifact', '上传产物供后续 job/Release 使用'),

    ('msvc-dev-cmd', '注入 Windows MSVC 编译环境（cl.exe/link.exe）'),

    ('gh release', '创建/上传 GitHub Release 资产'),

    ('docker/build-push-action', '构建并推送 Docker 镜像'),

    ('mvn ', 'Maven 构建（编译/测试/打包）'),

    ('native:compile', 'GraalVM native-image 编译（AOT 生成本地可执行文件）'),

    ('go build', 'Go 源码编译'),

    ('govulncheck', 'Go 依赖已知漏洞扫描'),

    ('cargo build', 'Rust 源码编译'),

    ('pip install', '安装 Python 依赖'),

    ('pytest', '运行 Python 单测'),

    ('psql', '用 psql 还原 PostgreSQL/openGauss 数据与 schema'),

    ('mysql', '用 mysql 客户端还原 MySQL schema/种子数据'),

    ('--check-stability', '稳定性探测：标记数据非确定性端点'),

    ('parity_probe.py', '探针：启动变体并逐端点采集 status/latency/RSS'),

    ('parity_compare.py', '对比：status/exact/semantic/nondet 判定并出报告'),

]



def wf_header(path, text):

    name = path.rsplit('/',1)[-1]

    purpose = WF_PURPOSE.get(name, 'CI/CD workflow')

    lines = ['# ' + '='*76, f'# 文件：{path}', f'# 用途：{purpose}']

    # triggers

    trig = []

    m = re.search(r'(?m)^on:\s*$', text)

    if m:

        tail = text[m.end():m.end()+900]

        for key,desc in [('workflow_dispatch','手动 dispatch'),('push','push 事件'),('pull_request','PR 事件'),

                         ('workflow_call','被其他 workflow 调用'),('schedule','定时触发'),('release','Release 事件')]:

            if re.search(r'(?m)^\s{2}'+re.escape(key)+r':', tail): trig.append(desc)

    if trig: lines.append('# 触发：' + ' / '.join(trig))

    # jobs

    jobs = re.findall(r'(?m)^  ([A-Za-z0-9_-]+):\s*$', text)

    reserved = ('on','env','permissions','concurrency','defaults','jobs','name','run-name',

                'workflow_dispatch','push','pull_request','pull_request_target','workflow_call',

                'workflow_run','schedule','release','create','tags','branches','paths')

    jobs = [j for j in jobs if j not in reserved]

    if jobs: lines.append('# 主要 job：' + '、'.join(dict.fromkeys(jobs)))

    lines.append('# 说明：本文件仅新增中文注释，不改动任何执行逻辑；runner/权限/守卫以实际配置为准。')

    lines.append('# ' + '='*76)

    return '\n'.join(lines) + '\n'



def annotate_workflow(path, text):

    header = wf_header(path, text)

    out = []

    in_jobs = False   # 仅进入顶层 jobs: 段后才标记 job，避免把 on: 下的触发器当成 job

    for line in text.splitlines():

        stripped = line.strip()

        if re.match(r'^jobs:\s*$', line):

            in_jobs = True

        # job 行（缩进2、非保留键，且必须在 jobs: 段内）

        if in_jobs and re.match(r'^  [A-Za-z0-9_-]+:\s*$', line) and not stripped.startswith('#'):

            key = stripped[:-1]

            if key not in ('on','env','permissions','concurrency','defaults','jobs','name','run-name',

                           'workflow_dispatch','push','pull_request','workflow_call','schedule'):

                out.append(f'  # ── job: {key} ──')

        # step 关键注释（在 "- name:" 或 "- uses:" 行前）

        if re.match(r'^\s+- (name|uses):', line):

            for kw,hint in STEP_HINT:

                if kw in stripped:

                    indent = line[:len(line)-len(line.lstrip())]

                    out.append(f'{indent}# {hint}')

                    break

        out.append(line)

    return header + '\n'.join(out) + ('\n' if text.endswith('\n') else '')



def annotate_script(path, text):

    ext = path.rsplit('.',1)[-1]

    name = path.rsplit('/',1)[-1]

    if ext == 'py':

        comment = '#'

        purpose = {

            'parity_probe.py':'探针：启动 jar/native 变体，逐端点采集 status/bytes/latency/body-sha 与进程树 RSS',

            'parity_compare.py':'对比：两份探针 JSON 按 status/exact/semantic/nondet 判定并输出报告',

        }.get(name, '运维/构建辅助脚本')

    elif ext == 'sh':

        comment = '#'

        purpose = {

            'v3-compare-business.sh':'业务对比：native 与 JVM 的 7 端点字节级/语义级一致性校验',

            'v3-compare-native-jvm.sh':'性能对比：native 与 JVM 的启动时间/RSS/延迟 A/B 测试',

            'v3-native-build-linux.sh':'在 Linux 构建 native image',

            'v3-run-native-linux.sh':'运行 native 二进制并探活',

            'v3-run-jvm-linux.sh':'运行 JVM jar 并探活',

            'v3-setup-mandrel-linux.sh':'安装配置 Mandrel 工具链',

        }.get(name, 'Linux shell 运维/构建脚本')

    else:

        comment = '#'

        purpose = 'PowerShell 运维/构建脚本'

    # 在 shebang 后插入说明块（若无 shebang 则在最前）

    lines = text.splitlines()

    block = [f'{comment} ' + '='*70, f'{comment} 文件：{path}', f'{comment} 用途：{purpose}',

             f'{comment} 说明：仅新增中文注释，不改执行逻辑。', f'{comment} ' + '='*70]

    if lines and lines[0].startswith('#!'):

        newline = [lines[0]] + block + lines[1:]

    else:

        newline = block + lines

    return '\n'.join(newline) + ('\n' if text.endswith('\n') else '')



def git(repo, *a, input=None):

    kw = dict(capture_output=True)

    if input is not None: kw['input'] = input

    return subprocess.run(['git','-C',repo,*a], **kw)



def list_tree(repo, ref, prefix):

    p = git(repo,'ls-tree','-r','--name-only',ref,'--',prefix).stdout.decode('utf-8','replace')

    return [l for l in p.splitlines() if l.strip()]



def blob(repo, ref, path):

    return git(repo,'show',f'{ref}:{path}').stdout



def annotate(path, data):

    bom = data.startswith(b'\xef\xbb\xbf')

    text = data.decode('utf-8-sig','replace')  # 去掉 BOM 再处理，避免 BOM 干扰键名与校验

    if path.endswith(('.yml','.yaml')):

        out = annotate_workflow(path, text)

        # 语义不变校验：注释前后 YAML 解析结果必须完全一致

        try:

            import yaml

            assert yaml.safe_load(text) == yaml.safe_load(out), f'YAML 语义变化: {path}'

        except ImportError:

            pass

    elif path.endswith(('.sh','.py','.ps1')):

        out = annotate_script(path, text)

    else:

        return None

    # 保留原文件的 BOM 状态

    return (b'\xef\xbb\xbf' if bom else b'') + out.encode('utf-8')



for key, cfg in REPOS.items():

    repo = cfg['repo']

    branches = [b for b in cfg['branches'] if ONLY is None or b in ONLY]

    if not branches: continue

    # content hash -> (annotated bytes, [branches])

    groups = collections.OrderedDict()

    for br in branches:

        ref = 'refs/remotes/origin/'+br

        targets = [p for p in list_tree(repo,ref,'.github/workflows') if p.endswith(('.yml','.yaml'))] + \
                  [p for p in list_tree(repo,ref,'scripts') if p.endswith(('.sh','.py','.ps1'))]

        for p in targets:

            data = blob(repo,ref,p)

            h = hashlib.md5(data).hexdigest()

            if h not in groups:

                ann = annotate(p, data)

                if ann is None or ann == data: continue

                groups[h] = dict(path=p, data=ann, branches=[])

            groups[h]['branches'].append(br)

    print(f'###### {key}: {len(groups)} unique files to annotate')

    for h,g in groups.items():

        print(f"  {g['path']} {h[:8]} branches={','.join(g['branches'])}")

    if APPLY:

        for br in branches:

            ref = 'refs/remotes/origin/'+br

            base = git(repo,'rev-parse',ref).stdout.decode().strip()

            idx = os.path.join(tempfile.gettempdir(), f'ann_{os.getpid()}_{abs(hash(br))}.idx')

            env = os.environ.copy(); env['GIT_INDEX_FILE'] = idx

            subprocess.run(['git','-C',repo,'read-tree',base],env=env,capture_output=True,check=True)

            changed = 0

            for h,g in groups.items():

                if br not in g['branches']: continue

                bh = git(repo,'hash-object','-w','--stdin',input=g['data']).stdout.decode().strip()

                old = git(repo,'ls-tree',base,'--',g['path']).stdout.decode().split()

                mode = old[0] if old else '100644'

                subprocess.run(['git','-C',repo,'update-index','--add','--cacheinfo',f'{mode},{bh},{g["path"]}'],

                               env=env,capture_output=True,check=True)

                changed += 1

            tree = subprocess.run(['git','-C',repo,'write-tree'],env=env,capture_output=True,text=True,check=True).stdout.strip()

            os.remove(idx)

            if tree == subprocess.run(['git','-C',repo,'rev-parse',base+'^{tree}'],capture_output=True,text=True).stdout.strip():

                print(f'  {br}: no change'); continue

            c = git(repo,'commit-tree',tree,'-p',base,'-m','docs(ci): 为 CI/CD workflow 与脚本添加中文注释')

            sha = c.stdout.decode().strip()

            if c.returncode: print(f'  {br}: COMMIT ERR {c.stderr.decode()}'); continue

            git(repo,'update-ref',ref,sha)

            print(f'  {br}: committed {sha[:7]} ({changed} files annotated)')

