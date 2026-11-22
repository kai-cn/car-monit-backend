# api-java-master-crosslang-full-cpp parity report

| metric | java-master (baseline) | cpp (candidate) |
| --- | --- | --- |
| startup_ms | None | None |
| peak_rss_MB | None | None |
| avg_latency_ms | 27.58 | 194.57 |

**Endpoints**: 79 | status_match=31 | exact=21 | semantic=21 | nondet=8 | fails=50

| endpoint | status(b/c) | bytes(b/c) | exact | semantic | verdict |
| --- | --- | --- | --- | --- | --- |
| /api/v1/large/carTrackQueryByCarNo | 400/400 | 277/219 | False | False | NONDET |
| /api/v1/large/export/status/1 | 200/200 | 39/39 | True | True | OK |
| /api/v1/large/fee | 400/400 | 277/206 | False | False | DIFF |
| /api/v1/large/snapshot | 400/400 | 277/211 | False | False | NONDET |
| /api/v1/large/stats/group | 400/400 | 277/214 | False | False | NONDET |
| /api/v1/large/trail | 400/400 | 277/208 | False | False | NONDET |
| /api/v1/unified/1/list | 400/400 | 277/211 | False | False | NONDET |
| /api/v1/unified/export/status/1 | 200/200 | 39/39 | True | True | OK |
| /base/feeGantry/1 | 200/200 | 0/0 | True | True | OK |
| /base/feeGantry/list | 200/500 | 17495/207 | False | False | DIFF |
| /base/feeStationEnter/1 | 200/500 | 33/210 | False | False | DIFF |
| /base/feeStationEnter/list | 200/500 | 8049/213 | False | False | DIFF |
| /base/feerecords/1 | 200/500 | 0/205 | False | False | DIFF |
| /base/feerecords/list | 200/500 | 53/208 | False | False | DIFF |
| /base/feerecords/listToExport | 200/500 | 2/216 | False | False | DIFF |
| /base/feestationexit/1 | 200/500 | 33/209 | False | False | DIFF |
| /base/feestationexit/list | 200/500 | 13774/212 | False | False | DIFF |
| /base/fwqjcxx/1 | 500/500 | 287/202 | False | False | NONDET |
| /base/fwqjcxx/list | 200/500 | 6427/171 | False | False | DIFF |
| /base/fwqjcxx/listAll | 200/500 | 95184/208 | False | False | DIFF |
| /base/gantry/1 | 200/500 | 645/201 | False | False | DIFF |
| /base/gantry/list | 200/500 | 6023/204 | False | False | DIFF |
| /base/gantry/listAll | 200/500 | 89589/207 | False | False | DIFF |
| /base/gantryIp/1 | 200/500 | 226/203 | False | False | DIFF |
| /base/gantryIp/list | 200/500 | 1939/206 | False | False | DIFF |
| /base/org/1 | 200/500 | 33/198 | False | False | DIFF |
| /base/org/list | 200/500 | 4053/201 | False | False | DIFF |
| /base/org/listAll | 200/500 | 58412/204 | False | False | DIFF |
| /base/provcapture/1 | 200/500 | 33/206 | False | False | DIFF |
| /base/provcapture/list | 200/500 | 53/209 | False | False | DIFF |
| /base/section/1 | 200/500 | 332/202 | False | False | DIFF |
| /base/section/list | 200/500 | 2953/205 | False | False | DIFF |
| /base/section/listAll | 200/500 | 24990/208 | False | False | DIFF |
| /base/sfsjcxx/1 | 200/500 | 33/202 | False | False | DIFF |
| /base/sfsjcxx/list | 200/500 | 4755/205 | False | False | DIFF |
| /base/sfsjcxx/listAll | 200/500 | 11086/208 | False | False | DIFF |
| /base/sfzjcxx/1 | 200/500 | 33/202 | False | False | DIFF |
| /base/sfzjcxx/list | 200/500 | 4583/205 | False | False | DIFF |
| /base/sfzjcxx/listAll | 200/500 | 67281/208 | False | False | DIFF |
| /base/snapshotflow/1 | 200/500 | 0/207 | False | False | DIFF |
| /base/snapshotflow/list | 200/500 | 53/210 | False | False | DIFF |
| /base/snapshotflow/listToExport | 200/500 | 2/218 | False | False | DIFF |
| /base/stationcapture/1 | 200/500 | 33/209 | False | False | DIFF |
| /base/stationcapture/list | 200/500 | 53/212 | False | False | DIFF |
| /base/sysutil/carTrackQueryByCarNo | 200/200 | 53/53 | True | True | OK |
| /base/sysutil/carTrackQueryByTime | 200/200 | 53/53 | True | True | OK |
| /base/sysutil/getByTrailBo | 200/200 | 724/724 | True | True | OK |
| /base/sysutil/saveRedis | 200/200 | 33/33 | True | True | OK |
| /base/sysutilTest/separateSnapshotFlowTimeList | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncBaseInfo | 200/500 | 0/217 | False | False | DIFF |
| /base/sysutilTest/syncCurrentTrack | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncHistroyTrack | 200/200 | 0/0 | True | True | OK |
| /base/sysutilTest/syncOdsSzdnGantry | 200/500 | 0/222 | False | False | DIFF |
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
| /base/toll/1 | 200/500 | 1123/199 | False | False | DIFF |
| /base/toll/list | 200/500 | 10116/202 | False | False | DIFF |
| /base/toll/listAll | 200/500 | 146759/205 | False | False | DIFF |
| /base/tollStationIp/1 | 200/500 | 33/208 | False | False | DIFF |
| /base/tollStationIp/list | 200/500 | 1560/211 | False | False | DIFF |
| /base/trailtracks/1 | 200/500 | 33/206 | False | False | DIFF |
| /base/trailtracks/list | 200/500 | 44378/209 | False | False | DIFF |
| /base/vehicleweight/1 | 500/500 | 287/208 | False | False | NONDET |
| /base/vehicleweight/list | 200/500 | 53/211 | False | False | DIFF |
| /base/vehicleweight/map | 500/200 | 287/2 | False | False | DIFF |
| /manager/fwqclls/1 | 200/200 | 391/33 | False | False | DIFF |
| /manager/fwqclls/list | 200/500 | 1105/208 | False | False | DIFF |
| /progressive/feerecords/list | 200/500 | 483566/215 | False | False | DIFF |
| /progressive/scale-level | 200/200 | 166/166 | True | True | OK |
| /progressive/snapshotflow/list | 200/500 | 179782/217 | False | False | DIFF |
| /progressive/trailfitting/list | 500/500 | 287/217 | False | False | NONDET |

## Real differences (DIFF)
- `/api/v1/large/fee`: status 400/400, bytes 277/206
- `/base/feeGantry/list`: status 200/500, bytes 17495/207
- `/base/feeStationEnter/1`: status 200/500, bytes 33/210
- `/base/feeStationEnter/list`: status 200/500, bytes 8049/213
- `/base/feerecords/1`: status 200/500, bytes 0/205
- `/base/feerecords/list`: status 200/500, bytes 53/208
- `/base/feerecords/listToExport`: status 200/500, bytes 2/216
- `/base/feestationexit/1`: status 200/500, bytes 33/209
- `/base/feestationexit/list`: status 200/500, bytes 13774/212
- `/base/fwqjcxx/list`: status 200/500, bytes 6427/171
- `/base/fwqjcxx/listAll`: status 200/500, bytes 95184/208
- `/base/gantry/1`: status 200/500, bytes 645/201
- `/base/gantry/list`: status 200/500, bytes 6023/204
- `/base/gantry/listAll`: status 200/500, bytes 89589/207
- `/base/gantryIp/1`: status 200/500, bytes 226/203
- `/base/gantryIp/list`: status 200/500, bytes 1939/206
- `/base/org/1`: status 200/500, bytes 33/198
- `/base/org/list`: status 200/500, bytes 4053/201
- `/base/org/listAll`: status 200/500, bytes 58412/204
- `/base/provcapture/1`: status 200/500, bytes 33/206
- `/base/provcapture/list`: status 200/500, bytes 53/209
- `/base/section/1`: status 200/500, bytes 332/202
- `/base/section/list`: status 200/500, bytes 2953/205
- `/base/section/listAll`: status 200/500, bytes 24990/208
- `/base/sfsjcxx/1`: status 200/500, bytes 33/202
- `/base/sfsjcxx/list`: status 200/500, bytes 4755/205
- `/base/sfsjcxx/listAll`: status 200/500, bytes 11086/208
- `/base/sfzjcxx/1`: status 200/500, bytes 33/202
- `/base/sfzjcxx/list`: status 200/500, bytes 4583/205
- `/base/sfzjcxx/listAll`: status 200/500, bytes 67281/208
- `/base/snapshotflow/1`: status 200/500, bytes 0/207
- `/base/snapshotflow/list`: status 200/500, bytes 53/210
- `/base/snapshotflow/listToExport`: status 200/500, bytes 2/218
- `/base/stationcapture/1`: status 200/500, bytes 33/209
- `/base/stationcapture/list`: status 200/500, bytes 53/212
- `/base/sysutilTest/syncBaseInfo`: status 200/500, bytes 0/217
- `/base/sysutilTest/syncOdsSzdnGantry`: status 200/500, bytes 0/222
- `/base/toll/1`: status 200/500, bytes 1123/199
- `/base/toll/list`: status 200/500, bytes 10116/202
- `/base/toll/listAll`: status 200/500, bytes 146759/205
- `/base/tollStationIp/1`: status 200/500, bytes 33/208
- `/base/tollStationIp/list`: status 200/500, bytes 1560/211
- `/base/trailtracks/1`: status 200/500, bytes 33/206
- `/base/trailtracks/list`: status 200/500, bytes 44378/209
- `/base/vehicleweight/list`: status 200/500, bytes 53/211
- `/base/vehicleweight/map`: status 500/200, bytes 287/2
- `/manager/fwqclls/1`: status 200/200, bytes 391/33
- `/manager/fwqclls/list`: status 200/500, bytes 1105/208
- `/progressive/feerecords/list`: status 200/500, bytes 483566/215
- `/progressive/snapshotflow/list`: status 200/500, bytes 179782/217