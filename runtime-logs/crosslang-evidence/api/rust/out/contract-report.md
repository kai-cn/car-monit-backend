# api-java-master-crosslang-full-rust parity report

| metric | java-master (baseline) | rust (candidate) |
| --- | --- | --- |
| startup_ms | None | None |
| peak_rss_MB | None | None |
| avg_latency_ms | 27.58 | 2.98 |

**Endpoints**: 79 | status_match=72 | exact=51 | semantic=52 | nondet=4 | fails=23

| endpoint | status(b/c) | bytes(b/c) | exact | semantic | verdict |
| --- | --- | --- | --- | --- | --- |
| /api/v1/large/carTrackQueryByCarNo | 400/400 | 277/137 | False | False | NONDET |
| /api/v1/large/export/status/1 | 200/200 | 39/39 | True | True | OK |
| /api/v1/large/fee | 400/400 | 277/120 | False | False | DIFF |
| /api/v1/large/snapshot | 400/400 | 277/125 | False | False | DIFF |
| /api/v1/large/stats/group | 400/400 | 277/128 | False | False | DIFF |
| /api/v1/large/trail | 400/400 | 277/122 | False | False | DIFF |
| /api/v1/unified/1/list | 400/200 | 277/81 | False | False | DIFF |
| /api/v1/unified/export/status/1 | 200/200 | 39/39 | True | True | OK |
| /base/feeGantry/1 | 200/200 | 0/0 | True | True | OK |
| /base/feeGantry/list | 200/200 | 17495/17495 | False | False | NONDET |
| /base/feeStationEnter/1 | 200/200 | 33/33 | True | True | OK |
| /base/feeStationEnter/list | 200/200 | 8049/8029 | False | True | OK |
| /base/feerecords/1 | 200/500 | 0/131 | False | False | DIFF |
| /base/feerecords/list | 200/500 | 53/134 | False | False | DIFF |
| /base/feerecords/listToExport | 200/500 | 2/142 | False | False | DIFF |
| /base/feestationexit/1 | 200/200 | 33/33 | True | True | OK |
| /base/feestationexit/list | 200/200 | 13774/13744 | False | False | DIFF |
| /base/fwqjcxx/1 | 500/500 | 287/128 | False | False | NONDET |
| /base/fwqjcxx/list | 200/200 | 6427/6427 | True | True | OK |
| /base/fwqjcxx/listAll | 200/200 | 95184/95184 | True | True | OK |
| /base/gantry/1 | 200/200 | 645/645 | True | True | OK |
| /base/gantry/list | 200/200 | 6023/6023 | True | True | OK |
| /base/gantry/listAll | 200/200 | 89589/89589 | True | True | OK |
| /base/gantryIp/1 | 200/200 | 226/226 | True | True | OK |
| /base/gantryIp/list | 200/200 | 1939/1939 | True | True | OK |
| /base/org/1 | 200/200 | 33/33 | True | True | OK |
| /base/org/list | 200/200 | 4053/4053 | False | False | DIFF |
| /base/org/listAll | 200/200 | 58412/58412 | False | False | DIFF |
| /base/provcapture/1 | 200/200 | 33/33 | True | True | OK |
| /base/provcapture/list | 200/200 | 53/53 | True | True | OK |
| /base/section/1 | 200/200 | 332/332 | False | False | DIFF |
| /base/section/list | 200/200 | 2953/2953 | False | False | DIFF |
| /base/section/listAll | 200/200 | 24990/24990 | False | False | DIFF |
| /base/sfsjcxx/1 | 200/200 | 33/33 | True | True | OK |
| /base/sfsjcxx/list | 200/200 | 4755/4755 | True | True | OK |
| /base/sfsjcxx/listAll | 200/200 | 11086/11086 | True | True | OK |
| /base/sfzjcxx/1 | 200/200 | 33/33 | True | True | OK |
| /base/sfzjcxx/list | 200/200 | 4583/4583 | True | True | OK |
| /base/sfzjcxx/listAll | 200/200 | 67281/67281 | True | True | OK |
| /base/snapshotflow/1 | 200/200 | 0/0 | True | True | OK |
| /base/snapshotflow/list | 200/200 | 53/53 | True | True | OK |
| /base/snapshotflow/listToExport | 200/200 | 2/2 | True | True | OK |
| /base/stationcapture/1 | 200/200 | 33/33 | True | True | OK |
| /base/stationcapture/list | 200/200 | 53/53 | True | True | OK |
| /base/sysutil/carTrackQueryByCarNo | 200/200 | 53/53 | True | True | OK |
| /base/sysutil/carTrackQueryByTime | 200/200 | 53/53 | True | True | OK |
| /base/sysutil/getByTrailBo | 200/200 | 724/724 | True | True | OK |
| /base/sysutil/saveRedis | 200/200 | 33/33 | True | True | OK |
| /base/sysutilTest/separateSnapshotFlowTimeList | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncBaseInfo | 200/200 | 0/0 | True | True | OK |
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
| /base/toll/1 | 200/200 | 1123/1123 | False | False | DIFF |
| /base/toll/list | 200/200 | 10116/10116 | False | False | DIFF |
| /base/toll/listAll | 200/200 | 146759/146759 | False | False | DIFF |
| /base/tollStationIp/1 | 200/200 | 33/33 | True | True | OK |
| /base/tollStationIp/list | 200/200 | 1560/1560 | True | True | OK |
| /base/trailtracks/1 | 200/200 | 33/33 | True | True | OK |
| /base/trailtracks/list | 200/200 | 44378/44378 | False | False | DIFF |
| /base/vehicleweight/1 | 500/500 | 287/134 | False | False | NONDET |
| /base/vehicleweight/list | 200/200 | 53/53 | True | True | OK |
| /base/vehicleweight/map | 500/200 | 287/43 | False | False | DIFF |
| /manager/fwqclls/1 | 200/200 | 391/391 | True | True | OK |
| /manager/fwqclls/list | 200/200 | 1105/1105 | True | True | OK |
| /progressive/feerecords/list | 200/500 | 483566/141 | False | False | DIFF |
| /progressive/scale-level | 200/200 | 166/166 | True | True | OK |
| /progressive/snapshotflow/list | 200/200 | 179782/179782 | False | False | DIFF |
| /progressive/trailfitting/list | 500/500 | 287/143 | False | False | DIFF |

## Real differences (DIFF)
- `/api/v1/large/fee`: status 400/400, bytes 277/120
- `/api/v1/large/snapshot`: status 400/400, bytes 277/125
- `/api/v1/large/stats/group`: status 400/400, bytes 277/128
- `/api/v1/large/trail`: status 400/400, bytes 277/122
- `/api/v1/unified/1/list`: status 400/200, bytes 277/81
- `/base/feerecords/1`: status 200/500, bytes 0/131
- `/base/feerecords/list`: status 200/500, bytes 53/134
- `/base/feerecords/listToExport`: status 200/500, bytes 2/142
- `/base/feestationexit/list`: status 200/200, bytes 13774/13744
- `/base/org/list`: status 200/200, bytes 4053/4053
- `/base/org/listAll`: status 200/200, bytes 58412/58412
- `/base/section/1`: status 200/200, bytes 332/332
- `/base/section/list`: status 200/200, bytes 2953/2953
- `/base/section/listAll`: status 200/200, bytes 24990/24990
- `/base/sysutilTest/syncOdsSzdnGantry`: status 200/500, bytes 0/148
- `/base/toll/1`: status 200/200, bytes 1123/1123
- `/base/toll/list`: status 200/200, bytes 10116/10116
- `/base/toll/listAll`: status 200/200, bytes 146759/146759
- `/base/trailtracks/list`: status 200/200, bytes 44378/44378
- `/base/vehicleweight/map`: status 500/200, bytes 287/43
- `/progressive/feerecords/list`: status 200/500, bytes 483566/141
- `/progressive/snapshotflow/list`: status 200/200, bytes 179782/179782
- `/progressive/trailfitting/list`: status 500/500, bytes 287/143