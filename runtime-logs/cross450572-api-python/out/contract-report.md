# api-java25-crosslang-full-python parity report

| metric | java-master (baseline) | python (candidate) |
| --- | --- | --- |
| startup_ms | None | None |
| peak_rss_MB | None | None |
| avg_latency_ms | 22.35 | 19.71 |

**Endpoints**: 79 | status_match=30 | exact=15 | semantic=20 | nondet=10 | fails=49

| endpoint | status(b/c) | bytes(b/c) | exact | semantic | verdict |
| --- | --- | --- | --- | --- | --- |
| /api/v1/large/carTrackQueryByCarNo | 400/400 | 119/137 | False | False | NONDET |
| /api/v1/large/export/status/1 | 200/200 | 39/39 | True | True | OK |
| /api/v1/large/fee | 400/400 | 102/120 | False | False | NONDET |
| /api/v1/large/snapshot | 400/400 | 107/125 | False | False | NONDET |
| /api/v1/large/stats/group | 400/400 | 110/128 | False | False | NONDET |
| /api/v1/large/trail | 400/400 | 104/122 | False | False | NONDET |
| /api/v1/unified/1/list | 400/400 | 107/125 | False | False | NONDET |
| /api/v1/unified/export/status/1 | 200/200 | 39/39 | True | True | OK |
| /base/feeGantry/1 | 200/500 | 0/130 | False | False | DIFF |
| /base/feeGantry/list | 200/500 | 17445/133 | False | False | DIFF |
| /base/feeStationEnter/1 | 200/500 | 33/136 | False | False | DIFF |
| /base/feeStationEnter/list | 200/500 | 8049/139 | False | False | DIFF |
| /base/feerecords/1 | 200/500 | 0/131 | False | False | DIFF |
| /base/feerecords/list | 200/500 | 53/134 | False | False | DIFF |
| /base/feerecords/listToExport | 200/500 | 2/142 | False | False | DIFF |
| /base/feestationexit/1 | 200/500 | 33/135 | False | False | DIFF |
| /base/feestationexit/list | 200/500 | 13774/138 | False | False | DIFF |
| /base/fwqjcxx/1 | 500/500 | 110/128 | False | False | NONDET |
| /base/fwqjcxx/list | 200/500 | 6427/131 | False | False | DIFF |
| /base/fwqjcxx/listAll | 200/500 | 95184/134 | False | False | DIFF |
| /base/gantry/1 | 200/500 | 645/127 | False | False | DIFF |
| /base/gantry/list | 200/500 | 6023/130 | False | False | DIFF |
| /base/gantry/listAll | 200/500 | 89589/133 | False | False | DIFF |
| /base/gantryIp/1 | 200/500 | 226/129 | False | False | DIFF |
| /base/gantryIp/list | 200/500 | 1939/132 | False | False | DIFF |
| /base/org/1 | 200/500 | 33/124 | False | False | DIFF |
| /base/org/list | 200/500 | 4053/127 | False | False | DIFF |
| /base/org/listAll | 200/500 | 58412/130 | False | False | DIFF |
| /base/provcapture/1 | 200/500 | 33/132 | False | False | DIFF |
| /base/provcapture/list | 200/500 | 53/135 | False | False | DIFF |
| /base/section/1 | 200/500 | 332/128 | False | False | DIFF |
| /base/section/list | 200/500 | 2953/131 | False | False | DIFF |
| /base/section/listAll | 200/500 | 24990/134 | False | False | DIFF |
| /base/sfsjcxx/1 | 200/500 | 33/128 | False | False | DIFF |
| /base/sfsjcxx/list | 200/500 | 4755/131 | False | False | DIFF |
| /base/sfsjcxx/listAll | 200/500 | 11086/134 | False | False | DIFF |
| /base/sfzjcxx/1 | 200/500 | 33/128 | False | False | DIFF |
| /base/sfzjcxx/list | 200/500 | 4583/131 | False | False | DIFF |
| /base/sfzjcxx/listAll | 200/500 | 67281/134 | False | False | DIFF |
| /base/snapshotflow/1 | 200/500 | 0/133 | False | False | DIFF |
| /base/snapshotflow/list | 200/500 | 53/136 | False | False | DIFF |
| /base/snapshotflow/listToExport | 200/500 | 2/144 | False | False | DIFF |
| /base/stationcapture/1 | 200/500 | 33/135 | False | False | DIFF |
| /base/stationcapture/list | 200/500 | 53/138 | False | False | DIFF |
| /base/sysutil/carTrackQueryByCarNo | 200/200 | 53/53 | False | True | OK |
| /base/sysutil/carTrackQueryByTime | 200/200 | 53/53 | False | True | OK |
| /base/sysutil/getByTrailBo | 200/200 | 724/724 | False | True | OK |
| /base/sysutil/saveRedis | 200/200 | 33/33 | False | True | OK |
| /base/sysutilTest/separateSnapshotFlowTimeList | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncBaseInfo | 200/500 | 0/143 | False | False | DIFF |
| /base/sysutilTest/syncCurrentTrack | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncHistroyTrack | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncOdsSzdnGantry | 200/500 | 0/148 | False | False | DIFF |
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
| /base/toll/1 | 200/500 | 1123/125 | False | False | DIFF |
| /base/toll/list | 200/500 | 10116/128 | False | False | DIFF |
| /base/toll/listAll | 200/500 | 146759/131 | False | False | DIFF |
| /base/tollStationIp/1 | 200/500 | 33/134 | False | False | DIFF |
| /base/tollStationIp/list | 200/500 | 1560/137 | False | False | DIFF |
| /base/trailtracks/1 | 200/500 | 33/132 | False | False | DIFF |
| /base/trailtracks/list | 200/500 | 44378/135 | False | False | DIFF |
| /base/vehicleweight/1 | 500/500 | 116/134 | False | False | NONDET |
| /base/vehicleweight/list | 200/500 | 53/137 | False | False | DIFF |
| /base/vehicleweight/map | 500/500 | 118/136 | False | False | NONDET |
| /manager/fwqclls/1 | 200/500 | 391/131 | False | False | DIFF |
| /manager/fwqclls/list | 200/500 | 1105/134 | False | False | DIFF |
| /progressive/feerecords/list | 200/500 | 483566/141 | False | False | DIFF |
| /progressive/scale-level | 200/200 | 166/166 | False | True | OK |
| /progressive/snapshotflow/list | 200/500 | 179032/143 | False | False | DIFF |
| /progressive/trailfitting/list | 500/500 | 125/143 | False | False | NONDET |

## Real differences (DIFF)
- `/base/feeGantry/1`: status 200/500, bytes 0/130
- `/base/feeGantry/list`: status 200/500, bytes 17445/133
- `/base/feeStationEnter/1`: status 200/500, bytes 33/136
- `/base/feeStationEnter/list`: status 200/500, bytes 8049/139
- `/base/feerecords/1`: status 200/500, bytes 0/131
- `/base/feerecords/list`: status 200/500, bytes 53/134
- `/base/feerecords/listToExport`: status 200/500, bytes 2/142
- `/base/feestationexit/1`: status 200/500, bytes 33/135
- `/base/feestationexit/list`: status 200/500, bytes 13774/138
- `/base/fwqjcxx/list`: status 200/500, bytes 6427/131
- `/base/fwqjcxx/listAll`: status 200/500, bytes 95184/134
- `/base/gantry/1`: status 200/500, bytes 645/127
- `/base/gantry/list`: status 200/500, bytes 6023/130
- `/base/gantry/listAll`: status 200/500, bytes 89589/133
- `/base/gantryIp/1`: status 200/500, bytes 226/129
- `/base/gantryIp/list`: status 200/500, bytes 1939/132
- `/base/org/1`: status 200/500, bytes 33/124
- `/base/org/list`: status 200/500, bytes 4053/127
- `/base/org/listAll`: status 200/500, bytes 58412/130
- `/base/provcapture/1`: status 200/500, bytes 33/132
- `/base/provcapture/list`: status 200/500, bytes 53/135
- `/base/section/1`: status 200/500, bytes 332/128
- `/base/section/list`: status 200/500, bytes 2953/131
- `/base/section/listAll`: status 200/500, bytes 24990/134
- `/base/sfsjcxx/1`: status 200/500, bytes 33/128
- `/base/sfsjcxx/list`: status 200/500, bytes 4755/131
- `/base/sfsjcxx/listAll`: status 200/500, bytes 11086/134
- `/base/sfzjcxx/1`: status 200/500, bytes 33/128
- `/base/sfzjcxx/list`: status 200/500, bytes 4583/131
- `/base/sfzjcxx/listAll`: status 200/500, bytes 67281/134
- `/base/snapshotflow/1`: status 200/500, bytes 0/133
- `/base/snapshotflow/list`: status 200/500, bytes 53/136
- `/base/snapshotflow/listToExport`: status 200/500, bytes 2/144
- `/base/stationcapture/1`: status 200/500, bytes 33/135
- `/base/stationcapture/list`: status 200/500, bytes 53/138
- `/base/sysutilTest/syncBaseInfo`: status 200/500, bytes 0/143
- `/base/sysutilTest/syncOdsSzdnGantry`: status 200/500, bytes 0/148
- `/base/toll/1`: status 200/500, bytes 1123/125
- `/base/toll/list`: status 200/500, bytes 10116/128
- `/base/toll/listAll`: status 200/500, bytes 146759/131
- `/base/tollStationIp/1`: status 200/500, bytes 33/134
- `/base/tollStationIp/list`: status 200/500, bytes 1560/137
- `/base/trailtracks/1`: status 200/500, bytes 33/132
- `/base/trailtracks/list`: status 200/500, bytes 44378/135
- `/base/vehicleweight/list`: status 200/500, bytes 53/137
- `/manager/fwqclls/1`: status 200/500, bytes 391/131
- `/manager/fwqclls/list`: status 200/500, bytes 1105/134
- `/progressive/feerecords/list`: status 200/500, bytes 483566/141
- `/progressive/snapshotflow/list`: status 200/500, bytes 179032/143