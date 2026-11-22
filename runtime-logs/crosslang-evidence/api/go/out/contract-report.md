# api-java25-crosslang-full-go parity report

| metric | java25-boot4 (baseline) | go (candidate) |
| --- | --- | --- |
| startup_ms | None | None |
| peak_rss_MB | None | None |
| avg_latency_ms | 16.99 | 2.86 |

**Endpoints**: 79 | status_match=62 | exact=6 | semantic=36 | nondet=6 | baseline_skip=0 | fails=37

| endpoint | status(b/c) | bytes(b/c) | exact | semantic | verdict |
| --- | --- | --- | --- | --- | --- |
| /api/v1/large/carTrackQueryByCarNo | 400/400 | 119/137 | False | False | NONDET |
| /api/v1/large/export/status/1 | 200/200 | 39/39 | True | True | OK |
| /api/v1/large/fee | 400/400 | 102/120 | False | False | NONDET |
| /api/v1/large/snapshot | 400/400 | 107/125 | False | False | NONDET |
| /api/v1/large/stats/group | 400/400 | 110/128 | False | False | NONDET |
| /api/v1/large/trail | 400/400 | 104/122 | False | False | NONDET |
| /api/v1/unified/1/list | 400/200 | 107/81 | False | False | DIFF |
| /api/v1/unified/export/status/1 | 200/200 | 39/39 | True | True | OK |
| /base/feeGantry/1 | 200/200 | 0/0 | True | True | OK |
| /base/feeGantry/list | 200/200 | 17445/17495 | False | False | NONDET |
| /base/feeStationEnter/1 | 200/200 | 33/33 | False | True | OK |
| /base/feeStationEnter/list | 200/200 | 8049/7989 | False | True | OK |
| /base/feerecords/1 | 200/200 | 0/0 | True | True | OK |
| /base/feerecords/list | 200/200 | 53/37629 | False | False | DIFF |
| /base/feerecords/listToExport | 200/200 | 2/37576 | False | False | DIFF |
| /base/feestationexit/1 | 200/200 | 33/33 | False | True | OK |
| /base/feestationexit/list | 200/200 | 13774/13724 | False | False | DIFF |
| /base/fwqjcxx/1 | 500/200 | 110/691 | False | False | DIFF |
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
| /base/snapshotflow/1 | 200/200 | 0/0 | True | True | OK |
| /base/snapshotflow/list | 200/200 | 53/53 | False | True | OK |
| /base/snapshotflow/listToExport | 200/200 | 2/2 | True | True | OK |
| /base/stationcapture/1 | 200/200 | 33/33 | False | True | OK |
| /base/stationcapture/list | 200/200 | 53/53 | False | True | OK |
| /base/sysutil/carTrackQueryByCarNo | 200/200 | 53/53 | False | True | OK |
| /base/sysutil/carTrackQueryByTime | 200/200 | 53/53 | False | True | OK |
| /base/sysutil/getByTrailBo | 200/200 | 724/724 | False | True | OK |
| /base/sysutil/saveRedis | 200/200 | 33/33 | False | True | OK |
| /base/sysutilTest/separateSnapshotFlowTimeList | 200/501 | 0/591 | False | False | DIFF |
| /base/sysutilTest/syncBaseInfo | 200/200 | 0/48 | False | False | DIFF |
| /base/sysutilTest/syncCurrentTrack | 200/200 | 0/64 | False | False | DIFF |
| /base/sysutilTest/syncHistroyTrack | 200/200 | 0/65 | False | False | DIFF |
| /base/sysutilTest/syncOdsSzdnGantry | 200/501 | 0/526 | False | False | DIFF |
| /base/sysutilTest/syncSuspiciousCar1 | 200/501 | 0/705 | False | False | DIFF |
| /base/sysutilTest/syncSuspiciousCar10 | 200/501 | 0/706 | False | False | DIFF |
| /base/sysutilTest/syncSuspiciousCar2 | 200/501 | 0/705 | False | False | DIFF |
| /base/sysutilTest/syncSuspiciousCar3 | 200/501 | 0/705 | False | False | DIFF |
| /base/sysutilTest/syncSuspiciousCar4 | 200/501 | 0/705 | False | False | DIFF |
| /base/sysutilTest/syncSuspiciousCar5 | 200/501 | 0/705 | False | False | DIFF |
| /base/sysutilTest/syncSuspiciousCar6 | 200/501 | 0/705 | False | False | DIFF |
| /base/sysutilTest/syncSuspiciousCar7 | 200/501 | 0/705 | False | False | DIFF |
| /base/sysutilTest/syncSuspiciousCar8 | 200/501 | 0/705 | False | False | DIFF |
| /base/sysutilTest/syncSuspiciousCar9 | 200/501 | 0/705 | False | False | DIFF |
| /base/toll/1 | 200/200 | 1123/1123 | False | False | DIFF |
| /base/toll/list | 200/200 | 10116/10116 | False | False | DIFF |
| /base/toll/listAll | 200/200 | 146759/146759 | False | False | DIFF |
| /base/tollStationIp/1 | 200/200 | 33/33 | False | True | OK |
| /base/tollStationIp/list | 200/200 | 1560/1560 | False | True | OK |
| /base/trailtracks/1 | 200/200 | 33/33 | False | True | OK |
| /base/trailtracks/list | 200/200 | 44378/44378 | False | False | DIFF |
| /base/vehicleweight/1 | 500/200 | 116/33 | False | False | DIFF |
| /base/vehicleweight/list | 200/200 | 53/53 | False | True | OK |
| /base/vehicleweight/map | 500/200 | 118/43 | False | False | DIFF |
| /manager/fwqclls/1 | 200/200 | 391/391 | False | True | OK |
| /manager/fwqclls/list | 200/200 | 1105/1105 | False | True | OK |
| /progressive/feerecords/list | 200/200 | 483566/558569 | False | False | DIFF |
| /progressive/scale-level | 200/200 | 166/166 | False | True | OK |
| /progressive/snapshotflow/list | 200/200 | 179032/179782 | False | False | DIFF |
| /progressive/trailfitting/list | 500/200 | 125/741150 | False | False | DIFF |

## Real differences (DIFF)
- `/api/v1/unified/1/list`: status 400/200, bytes 107/81
    - baseline body: `{"timestamp":"2026-11-22T06:33:21.221Z","status":400,"error":"Bad Request","path":"/api/v1/unified/1/list"}`
    - candidate body: `{"code":400,"message":"未知数据源: 1, 合法取值: snapshot / fee / trail"}`
- `/base/feerecords/list`: status 200/200, bytes 53/37629
    - baseline body: `{"total":0,"code":200,"msg":"查询成功","rows":[]}`
    - candidate body: `{"total":150,"rows":[{"bigId":"1029052209","algorithmidentifier":"1","antennaid":"3","axlecount":2,"balanceafter":4291227038,"balancebefore":4291227038,"cardfeesumafter":2297,"cardfeesumbefore":1343,"computerorder":"1","consumetime":267,"cpucardid":"1901230000119937","cpucardtype":"2","cpuenddate":"`
- `/base/feerecords/listToExport`: status 200/200, bytes 2/37576
    - baseline body: `[]`
    - candidate body: `[{"bigId":"1029052209","algorithmidentifier":"1","antennaid":"3","axlecount":2,"balanceafter":4291227038,"balancebefore":4291227038,"cardfeesumafter":2297,"cardfeesumbefore":1343,"computerorder":"1","consumetime":267,"cpucardid":"1901230000119937","cpucardtype":"2","cpuenddate":"20291222","cpuissuei`
- `/base/feestationexit/list`: status 200/200, bytes 13774/13724
    - baseline body: `{"total":150,"code":200,"msg":"查询成功","rows":[{"actualfeeclass":"0","axlecount":2,"bigId":"11150377","cid":null,"cidList":null,"discountfee":0,"electricalpercentage":0,"enaxlecount":null,"entime":"1970-01-01 08:00:00","entolllanehex":"0","entolllaneid":"-1","entollstationid":"-1","entollstationname":`
    - candidate body: `{"total":150,"rows":[{"bigId":"11150377","actualfeeclass":"0","axlecount":2,"discountfee":0,"electricalpercentage":0,"enaxlecount":null,"entime":"1970-01-01 00:00:00","entolllanehex":"0","entolllaneid":"-1","entollstationid":"-1","entollstationname":"-1","envehicleclass":0,"envehicleid":"默A00000_9",`
- `/base/fwqjcxx/1`: status 500/200, bytes 110/691
    - baseline body: `{"timestamp":"2026-11-22T06:33:19.802Z","status":500,"error":"Internal Server Error","path":"/base/fwqjcxx/1"}`
    - candidate body: `{"code":200,"data":{"agentPk":"1","yxtzj":"45L4479928780847000","fwqbm":"G0321361123W0010","fwqmc":"三清山西服务区","wd":"28.78460594859297","fxmc":null,"fxdm":"1","jd":"117.99355545361145","sslxbh":"G0321","sslxmc":null,"ssldbh":"200R503210756000","ssldmc":"德上","sczhkgs":"1204.55005","sczhszgs":null,"ssgl`
- `/base/fwqjcxx/listAll`: status 200/200, bytes 95184/95184
    - baseline body: `[{"agentPk":"1","allColPk":null,"cdzs":"2","cws":"118","fwqbm":"G0321361123W0010","fwqmc":"三清山西服务区","fxdm":"1","fxmc":null,"jd":"117.99355545361145","loadTime":null,"lyxt":"三清山西服务区","mj":null,"sczhkgs":"1204.55005","sczhszgs":null,"sfcyfw":"1","sfszlkk":"1","sftgcsfw":"1","sftgcshfw":null,"sftgjyfw"`
    - candidate body: `[{"agentPk":"1","yxtzj":"45L4479928780847000","fwqbm":"G0321361123W0010","fwqmc":"三清山西服务区","wd":"28.78460594859297","fxmc":null,"fxdm":"1","jd":"117.99355545361145","sslxbh":"G0321","sslxmc":null,"ssldbh":"200R503210756000","ssldmc":"德上","sczhkgs":"1204.55005","sczhszgs":null,"ssglzxbm":"030000009",`
- `/base/gantry/listAll`: status 200/200, bytes 89589/89589
    - baseline body: `[{"belongGroup":"1","boundaryGantryType":null,"cityCode":"360730","direction":"1","districtName":"江西省赣州市宁都县","gantryCode":"G003536012000720010","gantryCodeMerge":"G003536012000720010","gantryName":"瑞金北互通-宁都东互通门架1","gantryNameAlias":"瑞金北互通-宁都东互通门架1","gantryType":"0","hexCode":"39110A","id":"18","isDa`
    - candidate body: `[{"id":"18","gantryCode":"G003536012000720010","gantryName":"瑞金北互通-宁都东互通门架1","roadCode":"G35","sectionCode":"200R500350729001","tollCode":"G35360730F0020","orgCode":"030000007","hexCode":"39110A","direction":"1","pileNo":"ZK1396+010","lon":"116.13113948740477","lat":"26.22047484041828","isVirtual":"`
- `/base/org/list`: status 200/200, bytes 4053/4053
    - baseline body: `{"total":150,"code":200,"msg":"查询成功","rows":[{"bigId":"24945","gradeLevel":1,"loadTime":"2025-08-29","orgAddress":null,"orgCategory":"03","orgCode":"000000936","orgIsAuthorized":"0","orgIsDeleted":"0","orgIsManager":"0","orgIsVirtual":"1","orgIsYhAutarky":"0","orgLevelCode":"00000011005300050001","o`
    - candidate body: `{"total":150,"rows":[{"bigId":"24945","orgCode":"000000936","orgName":"中心机关","orgShortName":"中心机关","orgParentId":"030000009","orgLevelCode":"00000011005300050001","orgIsVirtual":"1","orgMaintenance":"1","orgSequence":1,"orgIsManager":"0","orgIsDeleted":"0","orgCategory":"03","orgIsAuthorized":"0","o`
- `/base/org/listAll`: status 200/200, bytes 58412/58412
    - baseline body: `[{"bigId":"24945","gradeLevel":1,"loadTime":"2025-08-29","orgAddress":null,"orgCategory":"03","orgCode":"000000936","orgIsAuthorized":"0","orgIsDeleted":"0","orgIsManager":"0","orgIsVirtual":"1","orgIsYhAutarky":"0","orgLevelCode":"00000011005300050001","orgMaintenance":"1","orgName":"中心机关","orgPare`
    - candidate body: `[{"bigId":"24945","orgCode":"000000936","orgName":"中心机关","orgShortName":"中心机关","orgParentId":"030000009","orgLevelCode":"00000011005300050001","orgIsVirtual":"1","orgMaintenance":"1","orgSequence":1,"orgIsManager":"0","orgIsDeleted":"0","orgCategory":"03","orgIsAuthorized":"0","orgAddress":null,"org`
- `/base/section/1`: status 200/200, bytes 332/332
    - baseline body: `{"msg":"操作成功","code":200,"data":{"endPileNo":2915,"id":"1","mileage":41,"openDate":"2003-06-01","orgCategory":"03","orgCode":"020000253","orgLevelCode":"0000001100530012","orgName":"吉安西管理中心","roadCode":"G45","roadName":"大广高速","sectionCode":"200R500450642000","sectionName":"昌泰","startPileNo":2873}}`
    - candidate body: `{"code":200,"data":{"id":"1","roadCode":"G45","roadName":"大广高速","sectionCode":"200R500450642000","sectionName":"昌泰","startPileNo":2873,"endPileNo":2915,"orgCode":"020000253","orgName":"吉安西管理中心","orgLevelCode":"0000001100530012","orgCategory":"03","mileage":41,"openDate":"2003-05-31"},"msg":"操作成功"}`
- `/base/section/list`: status 200/200, bytes 2953/2953
    - baseline body: `{"total":85,"code":200,"msg":"查询成功","rows":[{"endPileNo":397,"id":"18","mileage":0,"openDate":"2005-11-01","orgCategory":"03","orgCode":"020110017","orgLevelCode":"0000001100530011","orgName":"南昌东管理中心","roadCode":"G6021","roadName":"杭长高速","sectionCode":"200R560210671000","sectionName":"乐温","startPil`
    - candidate body: `{"total":85,"rows":[{"id":"18","roadCode":"G6021","roadName":"杭长高速","sectionCode":"200R560210671000","sectionName":"乐温","startPileNo":379,"endPileNo":397,"orgCode":"020110017","orgName":"南昌东管理中心","orgLevelCode":"0000001100530011","orgCategory":"03","mileage":0,"openDate":"2005-10-31"},{"id":"27","ro`
- `/base/section/listAll`: status 200/200, bytes 24990/24990
    - baseline body: `[{"endPileNo":397,"id":"18","mileage":0,"openDate":"2005-11-01","orgCategory":"03","orgCode":"020110017","orgLevelCode":"0000001100530011","orgName":"南昌东管理中心","roadCode":"G6021","roadName":"杭长高速","sectionCode":"200R560210671000","sectionName":"乐温","startPileNo":379},{"endPileNo":446,"id":"27","milea`
    - candidate body: `[{"id":"18","roadCode":"G6021","roadName":"杭长高速","sectionCode":"200R560210671000","sectionName":"乐温","startPileNo":379,"endPileNo":397,"orgCode":"020110017","orgName":"南昌东管理中心","orgLevelCode":"0000001100530011","orgCategory":"03","mileage":0,"openDate":"2005-10-31"},{"id":"27","roadCode":"G76","road`
- `/base/sfzjcxx/listAll`: status 200/200, bytes 67281/67281
    - baseline body: `[{"agentPk":"363bc7b76e508c55dcb259cf6a3f007e","allColPk":"c1d6f80963f0f971268c957bed9dcc81","jd":"116.29458816","loadTime":"2025-08-29 06:11:00","lyxt":"机电运维管理系统","sczhK":"K24+600","sczhN":"24.600","sfzdm":"G56360429F0010","sfzmc":"均桥收费站","ssglzxbm":"030000254","ssglzxmc":null,"ssldbh":"200R0022360`
    - candidate body: `[{"agentPk":"363bc7b76e508c55dcb259cf6a3f007e","yxtzj":"1495673117678645249","sfzdm":"G56360429F0010","sfzmc":"均桥收费站","jd":"116.29458816","wd":"29.66365882","sslxbh":"S22","sslxmc":"都九高速公路","ssldbh":"200R00223600000611000","ssldmc":"都九高速九景段","sczhK":"K24+600","sczhN":"24.600","ssglzxbm":"030000254",`
- `/base/sysutilTest/separateSnapshotFlowTimeList`: status 200/501, bytes 0/591
    - baseline body: ``
    - candidate body: `{"code":501,"data":null,"javaRef":"SysTestController.java:359-364","msg":"SysTestController/separateSnapshotFlowTimeList 不提供（Java 侧同样无法执行）：产出 car_uspicious:*，其唯一消费方 syncSuspiciousCarDB() 无任何调用方，且会向外部 HTTP 接口推送数据；输入 js_car_snapshot:* 又只由上面那条中断的链路写入","porting":"blocked","reason":"产出 car_uspicious:*，其唯`
- `/base/sysutilTest/syncBaseInfo`: status 200/200, bytes 0/48
    - baseline body: ``
    - candidate body: `{"code":200,"msg":"基础字典缓存已重建"}`
- `/base/sysutilTest/syncCurrentTrack`: status 200/200, bytes 0/64
    - baseline body: ``
    - candidate body: `{"code":200,"msg":"实时轨迹已同步到 car_curent_trail:*"}`
- `/base/sysutilTest/syncHistroyTrack`: status 200/200, bytes 0/65
    - baseline body: ``
    - candidate body: `{"code":200,"msg":"历史轨迹已合并到 car_history_trail:*"}`
- `/base/sysutilTest/syncOdsSzdnGantry`: status 200/501, bytes 0/526
    - baseline body: ``
    - candidate body: `{"code":501,"data":null,"javaRef":"SysTestController.java:327-354","msg":"SysTestController/syncOdsSzdnGantry 不提供（Java 侧同样无法执行）：依赖 OdsLwzxsfsjFeeRecords01Mapper.selectGantryNum（只有声明、无 SQL），且入参时间串为 \"2025-11-01 00-00-00\"，过不了 to_timestamp 的格式解析","porting":"blocked","reason":"依赖 OdsLwzxsfsjFeeRecords0`
- `/base/sysutilTest/syncSuspiciousCar1`: status 200/501, bytes 0/705
    - baseline body: ``
    - candidate body: `{"code":501,"data":null,"javaRef":"SysTestController.java:175-185","msg":"SysTestController/syncSuspiciousCar1 不提供（Java 侧同样无法执行）：依赖 SysUtilServiceImpl.syncSuspiciousCarQutaz，该方法需要 OdsLwzxsfsjFeeRecords01Mapper.selectOdsLwzxsfsjFeeRecords01ListNew —— 该语句在全部 Mapper XML 中缺失，Java 侧调用时抛 Invalid bound sta`
- `/base/sysutilTest/syncSuspiciousCar10`: status 200/501, bytes 0/706
    - baseline body: ``
    - candidate body: `{"code":501,"data":null,"javaRef":"SysTestController.java:311-321","msg":"SysTestController/syncSuspiciousCar10 不提供（Java 侧同样无法执行）：依赖 SysUtilServiceImpl.syncSuspiciousCarQutaz，该方法需要 OdsLwzxsfsjFeeRecords01Mapper.selectOdsLwzxsfsjFeeRecords01ListNew —— 该语句在全部 Mapper XML 中缺失，Java 侧调用时抛 Invalid bound st`
- `/base/sysutilTest/syncSuspiciousCar2`: status 200/501, bytes 0/705
    - baseline body: ``
    - candidate body: `{"code":501,"data":null,"javaRef":"SysTestController.java:190-200","msg":"SysTestController/syncSuspiciousCar2 不提供（Java 侧同样无法执行）：依赖 SysUtilServiceImpl.syncSuspiciousCarQutaz，该方法需要 OdsLwzxsfsjFeeRecords01Mapper.selectOdsLwzxsfsjFeeRecords01ListNew —— 该语句在全部 Mapper XML 中缺失，Java 侧调用时抛 Invalid bound sta`
- `/base/sysutilTest/syncSuspiciousCar3`: status 200/501, bytes 0/705
    - baseline body: ``
    - candidate body: `{"code":501,"data":null,"javaRef":"SysTestController.java:205-215","msg":"SysTestController/syncSuspiciousCar3 不提供（Java 侧同样无法执行）：依赖 SysUtilServiceImpl.syncSuspiciousCarQutaz，该方法需要 OdsLwzxsfsjFeeRecords01Mapper.selectOdsLwzxsfsjFeeRecords01ListNew —— 该语句在全部 Mapper XML 中缺失，Java 侧调用时抛 Invalid bound sta`
- `/base/sysutilTest/syncSuspiciousCar4`: status 200/501, bytes 0/705
    - baseline body: ``
    - candidate body: `{"code":501,"data":null,"javaRef":"SysTestController.java:220-230","msg":"SysTestController/syncSuspiciousCar4 不提供（Java 侧同样无法执行）：依赖 SysUtilServiceImpl.syncSuspiciousCarQutaz，该方法需要 OdsLwzxsfsjFeeRecords01Mapper.selectOdsLwzxsfsjFeeRecords01ListNew —— 该语句在全部 Mapper XML 中缺失，Java 侧调用时抛 Invalid bound sta`
- `/base/sysutilTest/syncSuspiciousCar5`: status 200/501, bytes 0/705
    - baseline body: ``
    - candidate body: `{"code":501,"data":null,"javaRef":"SysTestController.java:235-245","msg":"SysTestController/syncSuspiciousCar5 不提供（Java 侧同样无法执行）：依赖 SysUtilServiceImpl.syncSuspiciousCarQutaz，该方法需要 OdsLwzxsfsjFeeRecords01Mapper.selectOdsLwzxsfsjFeeRecords01ListNew —— 该语句在全部 Mapper XML 中缺失，Java 侧调用时抛 Invalid bound sta`
- `/base/sysutilTest/syncSuspiciousCar6`: status 200/501, bytes 0/705
    - baseline body: ``
    - candidate body: `{"code":501,"data":null,"javaRef":"SysTestController.java:250-260","msg":"SysTestController/syncSuspiciousCar6 不提供（Java 侧同样无法执行）：依赖 SysUtilServiceImpl.syncSuspiciousCarQutaz，该方法需要 OdsLwzxsfsjFeeRecords01Mapper.selectOdsLwzxsfsjFeeRecords01ListNew —— 该语句在全部 Mapper XML 中缺失，Java 侧调用时抛 Invalid bound sta`
- `/base/sysutilTest/syncSuspiciousCar7`: status 200/501, bytes 0/705
    - baseline body: ``
    - candidate body: `{"code":501,"data":null,"javaRef":"SysTestController.java:265-275","msg":"SysTestController/syncSuspiciousCar7 不提供（Java 侧同样无法执行）：依赖 SysUtilServiceImpl.syncSuspiciousCarQutaz，该方法需要 OdsLwzxsfsjFeeRecords01Mapper.selectOdsLwzxsfsjFeeRecords01ListNew —— 该语句在全部 Mapper XML 中缺失，Java 侧调用时抛 Invalid bound sta`
- `/base/sysutilTest/syncSuspiciousCar8`: status 200/501, bytes 0/705
    - baseline body: ``
    - candidate body: `{"code":501,"data":null,"javaRef":"SysTestController.java:280-290","msg":"SysTestController/syncSuspiciousCar8 不提供（Java 侧同样无法执行）：依赖 SysUtilServiceImpl.syncSuspiciousCarQutaz，该方法需要 OdsLwzxsfsjFeeRecords01Mapper.selectOdsLwzxsfsjFeeRecords01ListNew —— 该语句在全部 Mapper XML 中缺失，Java 侧调用时抛 Invalid bound sta`
- `/base/sysutilTest/syncSuspiciousCar9`: status 200/501, bytes 0/705
    - baseline body: ``
    - candidate body: `{"code":501,"data":null,"javaRef":"SysTestController.java:296-306","msg":"SysTestController/syncSuspiciousCar9 不提供（Java 侧同样无法执行）：依赖 SysUtilServiceImpl.syncSuspiciousCarQutaz，该方法需要 OdsLwzxsfsjFeeRecords01Mapper.selectOdsLwzxsfsjFeeRecords01ListNew —— 该语句在全部 Mapper XML 中缺失，Java 侧调用时抛 Invalid bound sta`
- `/base/toll/1`: status 200/200, bytes 1123/1123
    - baseline body: `{"msg":"操作成功","code":200,"data":{"dynamicMonitorResource":null,"hexCode":null,"id":"1","idCard":"44L4464527980850000","inMonitorResource":"78f3570a76524ab5842a094953ebc254","isAccess":"1","laneMonitorResource":"8b8be1b74188409f912923d79d6dec4b,dda58d58b8e14276868530539ed012b8,6fdb8f5217104d858dbdf8e`
    - candidate body: `{"code":200,"data":{"id":"1","roadCode":"S43","idCard":"44L4464527980850000","tollCode":"S43361002F0020","tollName":"抚州东收费站","pileNo":"11.725899696350098","orgName":"抚州管理中心","hexCode":null,"stateCode":"S0043360010020","orgCode":"030000006","longitude":"116.46153232837898","latitude":"27.978258476644`
- `/base/toll/list`: status 200/200, bytes 10116/10116
    - baseline body: `{"total":150,"code":200,"msg":"查询成功","rows":[{"dynamicMonitorResource":null,"hexCode":null,"id":"1","idCard":"44L4464527980850000","inMonitorResource":"78f3570a76524ab5842a094953ebc254","isAccess":"1","laneMonitorResource":"8b8be1b74188409f912923d79d6dec4b,dda58d58b8e14276868530539ed012b8,6fdb8f5217`
    - candidate body: `{"total":150,"rows":[{"id":"1","roadCode":"S43","idCard":"44L4464527980850000","tollCode":"S43361002F0020","tollName":"抚州东收费站","pileNo":"11.725899696350098","orgName":"抚州管理中心","hexCode":null,"stateCode":"S0043360010020","orgCode":"030000006","longitude":"116.46153232837898","latitude":"27.9782584766`
- `/base/toll/listAll`: status 200/200, bytes 146759/146759
    - baseline body: `[{"dynamicMonitorResource":null,"hexCode":null,"id":"1","idCard":"44L4464527980850000","inMonitorResource":"78f3570a76524ab5842a094953ebc254","isAccess":"1","laneMonitorResource":"8b8be1b74188409f912923d79d6dec4b,dda58d58b8e14276868530539ed012b8,6fdb8f5217104d858dbdf8ef753979cb,7f85421df0d94d61a89df`
    - candidate body: `[{"id":"1","roadCode":"S43","idCard":"44L4464527980850000","tollCode":"S43361002F0020","tollName":"抚州东收费站","pileNo":"11.725899696350098","orgName":"抚州管理中心","hexCode":null,"stateCode":"S0043360010020","orgCode":"030000006","longitude":"116.46153232837898","latitude":"27.978258476644598","openDate":"1`
- `/base/trailtracks/list`: status 200/200, bytes 44378/44378
    - baseline body: `{"total":150,"code":200,"msg":"查询成功","rows":[{"applyTime1":null,"applyTime2":null,"carNo":null,"carNum":null,"carType":null,"carVehicle":null,"enaxlecount":null,"endLat":null,"endLatDec":null,"endLon":null,"endLonDec":null,"enterLocationcode":null,"enterTime":"2025-09-10 12:39:49","entolllaneid":nul`
    - candidate body: `{"total":150,"rows":[{"uuid":"e0e22490-fb40-4795-947b-68565d864aa7","type":0,"pointCount":45,"plateKey":"***","enterTime":"2025-09-10 04:39:49","exitTime":"2025-09-11 02:19:01","trailPoints":"[{\"pointUuid\":\"cd58f6fa-a108-45ff-8d5b-4588201795f6\",\"stateType\":\"StationCapture\",\"captureTime\`
- `/base/vehicleweight/1`: status 500/200, bytes 116/33
    - baseline body: `{"timestamp":"2026-11-22T06:33:20.396Z","status":500,"error":"Internal Server Error","path":"/base/vehicleweight/1"}`
    - candidate body: `{"code":200,"msg":"操作成功"}`
- `/base/vehicleweight/map`: status 500/200, bytes 118/43
    - baseline body: `{"timestamp":"2026-11-22T06:33:20.404Z","status":500,"error":"Internal Server Error","path":"/base/vehicleweight/map"}`
    - candidate body: `{"code":200,"data":{},"msg":"操作成功"}`
- `/progressive/feerecords/list`: status 200/200, bytes 483566/558569
    - baseline body: `{"total":150,"code":200,"msg":"策略: phase1-gaussdb-gin","rows":[{"algorithmidentifier":null,"antennaid":null,"axlecount":2,"balanceafter":null,"balancebefore":null,"bigId":"1872248497","cardfeesumafter":null,"cardfeesumbefore":null,"cid":"b29c91ae837c457db627596144a34f41","cidList":null,"code":null,"`
    - candidate body: `{"total":150,"rows":[{"bigId":"1029052209","algorithmidentifier":"1","antennaid":"3","axlecount":2,"balanceafter":4291227038,"balancebefore":4291227038,"cardfeesumafter":2297,"cardfeesumbefore":1343,"computerorder":"1","consumetime":267,"cpucardid":"1901230000119937","cpucardtype":"2","cpuenddate":"`
- `/progressive/snapshotflow/list`: status 200/200, bytes 179032/179782
    - baseline body: `{"total":150,"code":200,"msg":"策略: phase1-gaussdb-gin","rows":[{"applyTime1":null,"applyTime2":null,"bigId":null,"cameratype":null,"carbrand":null,"carcolor":"红色","carcolorcode":4,"cardirection":null,"cartype":"货车","cartypecode":16,"code":null,"codeList":null,"datasource":null,"datauuid":"736f1bc2-9`
    - candidate body: `{"total":150,"rows":[{"bigId":null,"datasource":null,"cameratype":null,"deviceid":null,"gantrycode":null,"gantryname":"黄金埠互通-万年互通门架1","roadcode":null,"roadname":"济广高速公路","sectioncode":null,"sectionname":"景鹰","tollcode":null,"tollname":null,"orgcode":null,"orgname":null,"direction":1,"hexcode":null,"`
- `/progressive/trailfitting/list`: status 500/200, bytes 125/741150
    - baseline body: `{"timestamp":"2026-11-22T06:33:20.660Z","status":500,"error":"Internal Server Error","path":"/progressive/trailfitting/list"}`
    - candidate body: `{"total":150,"rows":[{"cid":"0cd1353dc8894cad89e7b7df599ce7aa","enaxlecount":2,"entime":"2025-10-01","entolllaneid":"G15173605800301010030","entollstationid":"G1517360580030","entollstationname":"江西宁都北站","envehicleclass":0,"envehicleid":"***","envehicletype":11,"enweight":3600,"extime":"2025-10-`