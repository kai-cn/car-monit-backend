# api-java25-crosslang-full-python parity report

| metric | java-master (baseline) | python (candidate) |
| --- | --- | --- |
| startup_ms | None | None |
| peak_rss_MB | None | None |
| avg_latency_ms | 17.43 | 24.95 |

**Endpoints**: 79 | status_match=77 | exact=19 | semantic=52 | nondet=10 | fails=17

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
| /base/feeGantry/1 | 200/200 | 0/4 | False | True | OK |
| /base/feeGantry/list | 200/200 | 17445/17495 | False | False | NONDET |
| /base/feeStationEnter/1 | 200/200 | 33/33 | False | True | OK |
| /base/feeStationEnter/list | 200/200 | 8049/8049 | False | True | OK |
| /base/feerecords/1 | 200/200 | 0/4 | False | True | OK |
| /base/feerecords/list | 200/200 | 53/53 | False | True | OK |
| /base/feerecords/listToExport | 200/200 | 2/2 | True | True | OK |
| /base/feestationexit/1 | 200/200 | 33/33 | False | True | OK |
| /base/feestationexit/list | 200/200 | 13774/13774 | False | False | DIFF |
| /base/fwqjcxx/1 | 500/500 | 110/128 | False | False | NONDET |
| /base/fwqjcxx/list | 200/200 | 6427/6427 | False | True | OK |
| /base/fwqjcxx/listAll | 200/200 | 95184/95184 | False | False | DIFF |
| /base/gantry/1 | 200/200 | 645/645 | False | True | OK |
| /base/gantry/list | 200/200 | 6023/6023 | False | True | OK |
| /base/gantry/listAll | 200/200 | 89589/89589 | False | False | DIFF |
| /base/gantryIp/1 | 200/200 | 226/226 | False | True | OK |
| /base/gantryIp/list | 200/200 | 1939/1939 | False | True | OK |
| /base/org/1 | 200/200 | 33/33 | False | True | OK |
| /base/org/list | 200/200 | 4053/4053 | False | False | DIFF |
| /base/org/listAll | 200/200 | 58412/58412 | False | False | DIFF |
| /base/provcapture/1 | 200/200 | 33/33 | False | True | OK |
| /base/provcapture/list | 200/200 | 53/53 | False | True | OK |
| /base/section/1 | 200/200 | 332/332 | False | False | DIFF |
| /base/section/list | 200/200 | 2953/2953 | False | False | DIFF |
| /base/section/listAll | 200/200 | 24990/24990 | False | False | DIFF |
| /base/sfsjcxx/1 | 200/200 | 33/33 | False | True | OK |
| /base/sfsjcxx/list | 200/200 | 4755/4755 | False | True | OK |
| /base/sfsjcxx/listAll | 200/200 | 11086/11086 | False | True | OK |
| /base/sfzjcxx/1 | 200/200 | 33/33 | False | True | OK |
| /base/sfzjcxx/list | 200/200 | 4583/4583 | False | True | OK |
| /base/sfzjcxx/listAll | 200/200 | 67281/67281 | False | False | DIFF |
| /base/snapshotflow/1 | 200/200 | 0/4 | False | True | OK |
| /base/snapshotflow/list | 200/200 | 53/53 | False | True | OK |
| /base/snapshotflow/listToExport | 200/200 | 2/2 | True | True | OK |
| /base/stationcapture/1 | 200/200 | 33/33 | False | True | OK |
| /base/stationcapture/list | 200/200 | 53/53 | False | True | OK |
| /base/sysutil/carTrackQueryByCarNo | 200/200 | 53/53 | False | True | OK |
| /base/sysutil/carTrackQueryByTime | 200/200 | 53/53 | False | True | OK |
| /base/sysutil/getByTrailBo | 200/200 | 724/724 | False | True | OK |
| /base/sysutil/saveRedis | 200/200 | 33/33 | False | True | OK |
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
| /base/toll/1 | 200/200 | 1123/1123 | False | False | DIFF |
| /base/toll/list | 200/200 | 10116/10116 | False | False | DIFF |
| /base/toll/listAll | 200/200 | 146759/146759 | False | False | DIFF |
| /base/tollStationIp/1 | 200/200 | 33/33 | False | True | OK |
| /base/tollStationIp/list | 200/200 | 1560/1560 | False | True | OK |
| /base/trailtracks/1 | 200/200 | 33/33 | False | True | OK |
| /base/trailtracks/list | 200/200 | 44378/44378 | False | False | DIFF |
| /base/vehicleweight/1 | 500/500 | 116/134 | False | False | NONDET |
| /base/vehicleweight/list | 200/500 | 53/137 | False | False | DIFF |
| /base/vehicleweight/map | 500/500 | 118/136 | False | False | NONDET |
| /manager/fwqclls/1 | 200/200 | 391/391 | False | True | OK |
| /manager/fwqclls/list | 200/200 | 1105/1105 | False | True | OK |
| /progressive/feerecords/list | 200/200 | 483566/466616 | False | False | DIFF |
| /progressive/scale-level | 200/200 | 166/166 | False | True | OK |
| /progressive/snapshotflow/list | 200/200 | 179032/179782 | False | False | DIFF |
| /progressive/trailfitting/list | 500/200 | 125/741150 | False | False | DIFF |

## Real differences (DIFF)
- `/base/feestationexit/list`: status 200/200, bytes 13774/13774
- `/base/fwqjcxx/listAll`: status 200/200, bytes 95184/95184
- `/base/gantry/listAll`: status 200/200, bytes 89589/89589
- `/base/org/list`: status 200/200, bytes 4053/4053
- `/base/org/listAll`: status 200/200, bytes 58412/58412
- `/base/section/1`: status 200/200, bytes 332/332
- `/base/section/list`: status 200/200, bytes 2953/2953
- `/base/section/listAll`: status 200/200, bytes 24990/24990
- `/base/sfzjcxx/listAll`: status 200/200, bytes 67281/67281
- `/base/toll/1`: status 200/200, bytes 1123/1123
- `/base/toll/list`: status 200/200, bytes 10116/10116
- `/base/toll/listAll`: status 200/200, bytes 146759/146759
- `/base/trailtracks/list`: status 200/200, bytes 44378/44378
- `/base/vehicleweight/list`: status 200/500, bytes 53/137
- `/progressive/feerecords/list`: status 200/200, bytes 483566/466616
- `/progressive/snapshotflow/list`: status 200/200, bytes 179032/179782
- `/progressive/trailfitting/list`: status 500/200, bytes 125/741150