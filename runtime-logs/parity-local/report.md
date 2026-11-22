<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

# api-local-jdk25 parity report

| metric | jar (baseline) | native (candidate) |
| --- | --- | --- |
| startup_ms | 17126 | 2708 |
| peak_rss_MB | 519.0 | 298.5 |
| avg_latency_ms | 41.16 | 33.25 |

**Endpoints**: 79 | status_match=78 | exact=69 | semantic=69 | nondet=9 | fails=1

| endpoint | status(b/c) | bytes(b/c) | exact | semantic | verdict |
| --- | --- | --- | --- | --- | --- |
| /api/v1/large/carTrackQueryByCarNo | 400/400 | 119/119 | False | True | NONDET |
| /api/v1/large/export/status/1 | 200/200 | 39/39 | True | True | OK |
| /api/v1/large/fee | 400/400 | 102/102 | False | True | NONDET |
| /api/v1/large/snapshot | 400/400 | 107/107 | False | True | NONDET |
| /api/v1/large/stats/group | 400/400 | 110/110 | False | True | NONDET |
| /api/v1/large/trail | 400/400 | 104/104 | False | True | NONDET |
| /api/v1/unified/1/list | 400/400 | 107/107 | False | True | NONDET |
| /api/v1/unified/export/status/1 | 200/200 | 39/39 | True | True | OK |
| /base/feeGantry/1 | 200/200 | 0/0 | True | True | OK |
| /base/feeGantry/list | 200/200 | 17445/17445 | False | False | NONDET |
| /base/feeStationEnter/1 | 200/200 | 33/33 | True | True | OK |
| /base/feeStationEnter/list | 200/200 | 8049/8049 | True | True | OK |
| /base/feerecords/1 | 200/200 | 0/0 | True | True | OK |
| /base/feerecords/list | 200/200 | 33423/33423 | True | True | OK |
| /base/feerecords/listToExport | 200/200 | 33369/33369 | True | True | OK |
| /base/feestationexit/1 | 200/200 | 33/33 | True | True | OK |
| /base/feestationexit/list | 200/200 | 13774/13774 | True | True | OK |
| /base/fwqjcxx/1 | 200/200 | 691/691 | True | True | OK |
| /base/fwqjcxx/list | 200/200 | 6427/6427 | True | True | OK |
| /base/fwqjcxx/listAll | 200/200 | 137969/137969 | True | True | OK |
| /base/gantry/1 | 200/200 | 645/645 | True | True | OK |
| /base/gantry/list | 200/200 | 6024/6024 | True | True | OK |
| /base/gantry/listAll | 200/200 | 900175/900175 | True | True | OK |
| /base/gantryIp/1 | 200/200 | 226/226 | True | True | OK |
| /base/gantryIp/list | 200/200 | 1940/1940 | True | True | OK |
| /base/org/1 | 200/200 | 33/33 | True | True | OK |
| /base/org/list | 200/200 | 4053/4053 | True | True | OK |
| /base/org/listAll | 200/200 | 189438/189438 | True | True | OK |
| /base/provcapture/1 | 200/200 | 33/33 | True | True | OK |
| /base/provcapture/list | 200/200 | 22914/22914 | True | True | OK |
| /base/section/1 | 200/200 | 332/332 | True | True | OK |
| /base/section/list | 200/200 | 2953/2953 | True | True | OK |
| /base/section/listAll | 200/200 | 24990/24990 | True | True | OK |
| /base/sfsjcxx/1 | 200/200 | 33/33 | True | True | OK |
| /base/sfsjcxx/list | 200/200 | 4755/4755 | True | True | OK |
| /base/sfsjcxx/listAll | 200/200 | 11086/11086 | True | True | OK |
| /base/sfzjcxx/1 | 200/200 | 33/33 | True | True | OK |
| /base/sfzjcxx/list | 200/200 | 4583/4583 | True | True | OK |
| /base/sfzjcxx/listAll | 200/200 | 143736/143736 | True | True | OK |
| /base/snapshotflow/1 | 200/200 | 0/0 | True | True | OK |
| /base/snapshotflow/list | 200/200 | 55/55 | True | True | OK |
| /base/snapshotflow/listToExport | 200/200 | 2/2 | True | True | OK |
| /base/stationcapture/1 | 200/200 | 33/33 | True | True | OK |
| /base/stationcapture/list | 200/200 | 9713/9713 | True | True | OK |
| /base/sysutil/carTrackQueryByCarNo | 200/200 | 53/53 | True | True | OK |
| /base/sysutil/carTrackQueryByTime | 200/200 | 53/53 | True | True | OK |
| /base/sysutil/getByTrailBo | 200/200 | 724/724 | True | True | OK |
| /base/sysutil/saveRedis | 200/500 | 33/118 | False | False | DIFF |
| /base/sysutilTest/separateSnapshotFlowTimeList | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncBaseInfo | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncCurrentTrack | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncHistroyTrack | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncOdsSzdnGantry | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncSuspiciousCar1 | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncSuspiciousCar10 | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncSuspiciousCar2 | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncSuspiciousCar3 | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncSuspiciousCar4 | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncSuspiciousCar5 | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncSuspiciousCar6 | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncSuspiciousCar7 | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncSuspiciousCar8 | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncSuspiciousCar9 | 200/200 | 0/0 | True | True | OK |
| /base/toll/1 | 200/200 | 1123/1123 | True | True | OK |
| /base/toll/list | 200/200 | 10116/10116 | True | True | OK |
| /base/toll/listAll | 200/200 | 307969/307969 | True | True | OK |
| /base/tollStationIp/1 | 200/200 | 33/33 | True | True | OK |
| /base/tollStationIp/list | 200/200 | 1560/1560 | True | True | OK |
| /base/trailtracks/1 | 200/200 | 33/33 | True | True | OK |
| /base/trailtracks/list | 200/200 | 44379/44379 | True | True | OK |
| /base/vehicleweight/1 | 500/500 | 116/116 | False | True | NONDET |
| /base/vehicleweight/list | 200/200 | 11815/11815 | True | True | OK |
| /base/vehicleweight/map | 200/200 | 2362/2362 | True | True | OK |
| /manager/fwqclls/1 | 200/200 | 391/391 | True | True | OK |
| /manager/fwqclls/list | 200/200 | 1105/1105 | True | True | OK |
| /progressive/feerecords/list | 200/200 | 3298553/3298553 | True | True | OK |
| /progressive/scale-level | 200/200 | 166/166 | True | True | OK |
| /progressive/snapshotflow/list | 200/200 | 1073744/1073744 | True | True | OK |
| /progressive/trailfitting/list | 500/500 | 125/125 | False | True | NONDET |

## Real differences (DIFF)
- `/base/sysutil/saveRedis`: status 200/500, bytes 33/118