#!/usr/bin/env python3
"""
@description 历史脚本 add_native_release.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python add_native_release.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""Add release-upload capability to native-image-cloud.yml across all branches.

- adds `release_tag` workflow_dispatch input (empty = skip upload)
- adds a `publish` job (needs build) that downloads all native-* artifacts and
  uploads them to the given GitHub Release via gh CLI.
"""
import sys, os, subprocess, re
sys.path.insert(0, r'D:\work\runtime-logs')
ns = {}
exec(open(r'D:\work\runtime-logs\harden_workflows.py', encoding='utf-8').read().split('def main()')[0], ns)
REPOS = ns['REPOS']; git = ns['git']; branches = ns['branches']; show = ns['show']

INPUT_BLOCK = '''      release_tag:
        description: 'GitHub Release tag (留空=仅产出 artifact，不上传 Release)'
        type: string
        default: ''
'''

PUBLISH_JOB = '''
  publish:
    name: upload native to GitHub Release
    needs: [build]
    if: inputs.release_tag != ''
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Download all native artifacts
        uses: actions/download-artifact@v4
        with:
          pattern: native-*
          merge-multiple: false
          path: release-dist

      - name: Remove non-binary helper files and verify size
        shell: bash
        run: |
          set -euo pipefail
          cd release-dist
          find . -type f -printf '%p %s bytes\\n' | sort
          # 每个 native-* artifact 目录应含一个 >10MB 的二进制；小的 .sha256/manifest 保留供校验。
          bad=0
          for d in native-*; do
            [ -d "$d" ] || continue
            big=$(find "$d" -maxdepth 1 -type f -size +10M | head -n1)
            if [ -z "$big" ]; then echo "::error::$d 无 >10MB native 二进制（疑似误选 shim）"; bad=1; fi
          done
          [ "$bad" -eq 0 ] || exit 1

      - name: Flatten and checksum
        shell: bash
        run: |
          set -euo pipefail
          mkdir -p dist
          find release-dist -type f -exec cp -f {} dist/ \\;
          cd dist && sha256sum * > SHA256SUMS && ls -lh

      - name: gh release upload
        env:
          GH_TOKEN: ${{ github.token }}
          GH_REPO: ${{ github.repository }}
          RELEASE_TAG: ${{ inputs.release_tag }}
        shell: bash
        run: |
          gh release view "$RELEASE_TAG" >/dev/null 2>&1 || \\
            gh release create "$RELEASE_TAG" --generate-notes --title "$RELEASE_TAG"
          gh release upload "$RELEASE_TAG" dist/* --clobber
'''


def transform(text):
    changed = False
    if 'release_tag:' not in text:
        # insert after `inputs:` line at top (first occurrence under workflow_dispatch)
        m = re.search(r'(?m)^  workflow_dispatch:\n    inputs:\n', text)
        if not m:
            return text, False
        text = text[:m.end()] + INPUT_BLOCK + text[m.end():]
        changed = True
    if 'name: upload native to GitHub Release' not in text:
        text = text.rstrip('\n') + '\n' + PUBLISH_JOB
        changed = True
    return text, changed


apply = '--apply' in sys.argv
for rn, repo in REPOS.items():
    print('====', rn)
    for br in branches(repo):
        f = '.github/workflows/native-image-cloud.yml'
        c = show(repo, br, f)
        if c is None:
            continue
        new, ch = transform(c)
        if not ch:
            continue
        short = br.replace('refs/remotes/origin/', '')
        print('  ', short, 'changed')
        if apply:
            import yaml
            yaml.safe_load(new)
            base = git(repo, 'rev-parse', br).stdout.strip()
            h = git(repo, 'hash-object', '-w', '--stdin', input=new).stdout.strip()
            ti = os.path.join(os.environ.get('TEMP','/tmp'), f'rel_{os.getpid()}_{abs(hash(br))}.idx')
            e = os.environ.copy(); e['GIT_INDEX_FILE'] = ti
            subprocess.run(['git','-C',repo,'read-tree',base], env=e, capture_output=True, check=True)
            mode = git(repo,'ls-tree',base,'--',f).stdout.split()[0]
            subprocess.run(['git','-C',repo,'update-index','--add','--cacheinfo',f'{mode},{h},{f}'], env=e, capture_output=True, check=True)
            tree = subprocess.run(['git','-C',repo,'write-tree'], env=e, capture_output=True, text=True, check=True).stdout.strip()
            os.remove(ti)
            cm = git(repo,'commit-tree',tree,'-p',base,'-m','ci(native): add release_tag input and gh release upload job')
            if cm.returncode:
                print('    COMMIT ERR', cm.stderr); continue
            sha = cm.stdout.strip()
            git(repo,'update-ref',br,sha)
            print('    COMMITTED', sha[:7])
