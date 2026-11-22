<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

# api-jdk25-mysql parity report

| metric | jar (baseline) | jar (candidate) |
| --- | --- | --- |
| startup_ms | 8720 | 7816 |
| peak_rss_MB | 501.8 | 540.8 |
| avg_latency_ms | 9.77 | 9.14 |

**Endpoints**: 79 | status_match=79 | exact=20 | semantic=20 | nondet=59 | fails=0

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
| /base/feeGantry/1 | 500/500 | 112/112 | False | True | NONDET |
| /base/feeGantry/list | 500/500 | 115/115 | False | True | NONDET |
| /base/feeStationEnter/1 | 500/500 | 118/118 | False | True | NONDET |
| /base/feeStationEnter/list | 500/500 | 121/121 | False | True | NONDET |
| /base/feerecords/1 | 500/500 | 113/113 | False | True | NONDET |
| /base/feerecords/list | 500/500 | 116/116 | False | True | NONDET |
| /base/feerecords/listToExport | 500/500 | 124/124 | False | True | NONDET |
| /base/feestationexit/1 | 500/500 | 117/117 | False | True | NONDET |
| /base/feestationexit/list | 500/500 | 120/120 | False | True | NONDET |
| /base/fwqjcxx/1 | 500/500 | 110/110 | False | True | NONDET |
| /base/fwqjcxx/list | 500/500 | 113/113 | False | True | NONDET |
| /base/fwqjcxx/listAll | 500/500 | 116/116 | False | True | NONDET |
| /base/gantry/1 | 500/500 | 109/109 | False | True | NONDET |
| /base/gantry/list | 500/500 | 112/112 | False | True | NONDET |
| /base/gantry/listAll | 500/500 | 115/115 | False | True | NONDET |
| /base/gantryIp/1 | 500/500 | 111/111 | False | True | NONDET |
| /base/gantryIp/list | 500/500 | 114/114 | False | True | NONDET |
| /base/org/1 | 500/500 | 106/106 | False | True | NONDET |
| /base/org/list | 500/500 | 109/109 | False | True | NONDET |
| /base/org/listAll | 500/500 | 112/112 | False | True | NONDET |
| /base/provcapture/1 | 500/500 | 114/114 | False | True | NONDET |
| /base/provcapture/list | 500/500 | 117/117 | False | True | NONDET |
| /base/section/1 | 500/500 | 110/110 | False | True | NONDET |
| /base/section/list | 500/500 | 113/113 | False | True | NONDET |
| /base/section/listAll | 500/500 | 116/116 | False | True | NONDET |
| /base/sfsjcxx/1 | 500/500 | 110/110 | False | True | NONDET |
| /base/sfsjcxx/list | 500/500 | 113/113 | False | True | NONDET |
| /base/sfsjcxx/listAll | 500/500 | 116/116 | False | True | NONDET |
| /base/sfzjcxx/1 | 500/500 | 110/110 | False | True | NONDET |
| /base/sfzjcxx/list | 500/500 | 113/113 | False | True | NONDET |
| /base/sfzjcxx/listAll | 500/500 | 116/116 | False | True | NONDET |
| /base/snapshotflow/1 | 500/500 | 115/115 | False | True | NONDET |
| /base/snapshotflow/list | 500/500 | 118/118 | False | True | NONDET |
| /base/snapshotflow/listToExport | 500/500 | 126/126 | False | True | NONDET |
| /base/stationcapture/1 | 500/500 | 117/117 | False | True | NONDET |
| /base/stationcapture/list | 500/500 | 120/120 | False | True | NONDET |
| /base/sysutil/carTrackQueryByCarNo | 200/200 | 53/53 | True | True | OK |
| /base/sysutil/carTrackQueryByTime | 200/200 | 53/53 | True | True | OK |
| /base/sysutil/getByTrailBo | 200/200 | 724/724 | True | True | OK |
| /base/sysutil/saveRedis | 200/200 | 33/33 | True | True | OK |
| /base/sysutilTest/separateSnapshotFlowTimeList | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncBaseInfo | 500/500 | 125/125 | False | True | NONDET |
| /base/sysutilTest/syncCurrentTrack | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncHistroyTrack | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncOdsSzdnGantry | 500/500 | 130/130 | False | True | NONDET |
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
| /base/toll/1 | 500/500 | 107/107 | False | True | NONDET |
| /base/toll/list | 500/500 | 110/110 | False | True | NONDET |
| /base/toll/listAll | 500/500 | 113/113 | False | True | NONDET |
| /base/tollStationIp/1 | 500/500 | 116/116 | False | True | NONDET |
| /base/tollStationIp/list | 500/500 | 119/119 | False | True | NONDET |
| /base/trailtracks/1 | 500/500 | 114/114 | False | True | NONDET |
| /base/trailtracks/list | 500/500 | 117/117 | False | True | NONDET |
| /base/vehicleweight/1 | 500/500 | 116/116 | False | True | NONDET |
| /base/vehicleweight/list | 500/500 | 119/119 | False | True | NONDET |
| /base/vehicleweight/map | 500/500 | 118/118 | False | True | NONDET |
| /manager/fwqclls/1 | 500/500 | 113/113 | False | True | NONDET |
| /manager/fwqclls/list | 500/500 | 116/116 | False | True | NONDET |
| /progressive/feerecords/list | 500/500 | 123/123 | False | True | NONDET |
| /progressive/scale-level | 200/200 | 166/166 | True | True | OK |
| /progressive/snapshotflow/list | 500/500 | 125/125 | False | True | NONDET |
| /progressive/trailfitting/list | 500/500 | 125/125 | False | True | NONDET |