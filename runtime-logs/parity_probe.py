#!/usr/bin/env python3

#
# @description 历史脚本 parity_probe.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage python parity_probe.py [args]；具体参数以脚本 argparse 或源码说明为准。
# @dependencies Java 运行时；Python 3 标准库及脚本原有第三方依赖
#
from __future__ import annotations

import argparse, hashlib, json, os, signal, socket, subprocess, sys, threading, time

from pathlib import Path



IS_WIN = os.name == 'nt'



if IS_WIN:

    import ctypes

    from ctypes import wintypes



    class PMC(ctypes.Structure):

        _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD),

                    ('PeakWorkingSetSize', ctypes.c_size_t), ('WorkingSetSize', ctypes.c_size_t),

                    ('QuotaPeakPagedPoolUsage', ctypes.c_size_t), ('QuotaPagedPoolUsage', ctypes.c_size_t),

                    ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t), ('QuotaNonPagedPoolUsage', ctypes.c_size_t),

                    ('PagefileUsage', ctypes.c_size_t), ('PeakPagefileUsage', ctypes.c_size_t)]





def _tree_rss_linux(root_pid):

    """Sum RSS over the whole process tree rooted at root_pid (shell + java child)."""

    try:

        pids = {}

        for d in os.listdir('/proc'):

            if not d.isdigit():

                continue

            pid = int(d)

            try:

                with open('/proc/%d/stat' % pid) as f:

                    stat = f.read()

                ppid = int(stat.rsplit(')', 1)[1].split()[1])

                pids[pid] = ppid

            except Exception:

                continue

        # collect descendants of root_pid

        want = {root_pid}

        changed = True

        while changed:

            changed = False

            for pid, ppid in pids.items():

                if ppid in want and pid not in want:

                    want.add(pid); changed = True

        total = 0.0

        for pid in want:

            try:

                with open('/proc/%d/status' % pid) as f:

                    for line in f:

                        if line.startswith('VmRSS:'):

                            total += int(line.split()[1]) / 1024.0

                            break

            except Exception:

                pass

        return total if total > 0 else None

    except Exception:

        return None





def rss_mb(pid):

    """Return (current_rss_mb, peak_rss_mb).



    On Linux, `shell=True` makes `pid` the /bin/sh wrapper; the JVM/native process is a

    descendant, so we sum the whole process tree. Peak is approximated by the sampler's

    running max, so we return (tree_rss, tree_rss) and let the caller track the maximum.

    """

    if IS_WIN:

        try:

            h = ctypes.windll.kernel32.OpenProcess(0x0400 | 0x0010, False, pid)

            if not h:

                return None, None

            pmc = PMC()

            pmc.cb = ctypes.sizeof(pmc)

            ok = ctypes.windll.psapi.GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb)

            ctypes.windll.kernel32.CloseHandle(h)

            if not ok:

                return None, None

            return pmc.WorkingSetSize / 1048576.0, pmc.PeakWorkingSetSize / 1048576.0

        except Exception:

            return None, None

    cur = _tree_rss_linux(pid)

    return cur, cur





def port_open(port, timeout=1.0):

    try:

        with socket.create_connection(('127.0.0.1', port), timeout=timeout):

            return True

    except OSError:

        return False





def http_get(port, path, timeout=15):

    import urllib.request, urllib.error

    url = 'http://127.0.0.1:%d%s' % (port, path)

    t0 = time.time()

    try:

        with urllib.request.urlopen(url, timeout=timeout) as r:

            body = r.read()

            code = r.status

    except urllib.error.HTTPError as e:

        body = e.read()

        code = e.code

    except Exception as e:

        return 0, b'', round((time.time() - t0) * 1000, 2), str(e)[:150]

    return code, body, round((time.time() - t0) * 1000, 2), None





def main():

    ap = argparse.ArgumentParser()

    ap.add_argument('--variant', required=True)

    ap.add_argument('--cmd', required=True)

    ap.add_argument('--port', type=int, required=True)

    ap.add_argument('--endpoints', required=True)

    ap.add_argument('--out', required=True)

    ap.add_argument('--label', default='parity')

    ap.add_argument('--ready-timeout', type=int, default=300)

    ap.add_argument('--mode', choices=['full', 'reachability'], default='full')

    ap.add_argument('--repeat', type=int, default=1)

    ap.add_argument('--check-stability', action='store_true',

                    help='call each endpoint twice; mark unstable (non-deterministic) endpoints')

    a = ap.parse_args()



    endpoints = [l.strip() for l in Path(a.endpoints).read_text(encoding='utf-8').splitlines() if l.strip()]

    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or '.', exist_ok=True)

    out = {'label': a.label, 'variant': a.variant, 'mode': a.mode, 'port': a.port,

           'endpoint_count': len(endpoints), 'startup_ms': None, 'startup_peak_rss_mb': None,

           'steady_rss_mb': None, 'endpoints': [], 'error': None}



    t0 = time.time()

    if IS_WIN:

        proc = subprocess.Popen(a.cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    else:

        proc = subprocess.Popen(a.cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,

                                start_new_session=True)

    logf = open(a.out + '.app.log', 'wb')

    peak = [0.0]

    stop = threading.Event()



    def sampler():

        while not stop.is_set():

            cur, pk = rss_mb(proc.pid)

            v = pk or cur

            if v and v > peak[0]:

                peak[0] = v

            time.sleep(0.5)



    def pump():

        try:

            for chunk in iter(lambda: proc.stdout.read(4096), b''):

                logf.write(chunk); logf.flush()

        except Exception:

            pass



    threading.Thread(target=sampler, daemon=True).start()

    threading.Thread(target=pump, daemon=True).start()



    ready = False

    while time.time() - t0 < a.ready_timeout:

        if proc.poll() is not None:

            out['error'] = 'process exited early rc=%s' % proc.returncode

            break

        if port_open(a.port):

            ready = True

            break

        time.sleep(0.3)



    out['startup_ms'] = int((time.time() - t0) * 1000)

    out['startup_peak_rss_mb'] = round(peak[0], 1)



    if ready:

        rows = []

        for ep in endpoints:

            code, body, ms, err = http_get(a.port, ep)

            sha1 = hashlib.sha256(body).hexdigest()[:16] if body else ''

            # stability probe: call once more, compare sha -> detect non-deterministic endpoints

            stable = True

            sha2 = sha1

            if a.check_stability:

                code2, body2, _ms2, _e2 = http_get(a.port, ep)

                sha2 = hashlib.sha256(body2).hexdigest()[:16] if body2 else ''

                stable = (code == code2 and sha1 == sha2)

            rows.append({'endpoint': ep, 'status': code, 'bytes': len(body), 'latency_ms': ms,

                         'sha256': sha1, 'sha256_2nd': sha2, 'stable': stable,

                         'body': body.decode('utf-8', 'replace')[:6000] if a.mode == 'full' and body else '',

                         'error': err})

        out['endpoints'] = rows

        out['steady_rss_mb'] = round(peak[0], 1)

    elif not out['error']:

        out['error'] = 'not ready within %ss' % a.ready_timeout



    stop.set()

    try:

        if IS_WIN:

            subprocess.run(['taskkill', '/F', '/T', '/PID', str(proc.pid)], capture_output=True)

        else:

            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)

    except Exception:

        try:

            proc.terminate()

        except Exception:

            pass

    try:

        proc.wait(timeout=15)

    except Exception:

        try:

            proc.kill()

        except Exception:

            pass

    try:

        logf.close()

    except Exception:

        pass



    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print('PROBE_DONE variant=%s ready=%s startup_ms=%s peak_rss=%sMB ep=%d err=%s' % (

        a.variant, ready, out['startup_ms'], out['startup_peak_rss_mb'], len(out['endpoints']), out['error']))





if __name__ == '__main__':

    main()

