# backend-java25-crosslang-full-go parity report

| metric | java-master (baseline) | go (candidate) |
| --- | --- | --- |
| startup_ms | None | None |
| peak_rss_MB | None | None |
| avg_latency_ms | 413.34 | 6.05 |

**Endpoints**: 302 | status_match=293 | exact=76 | semantic=176 | nondet=40 | fails=86

| endpoint | status(b/c) | bytes(b/c) | exact | semantic | verdict |
| --- | --- | --- | --- | --- | --- |
| /base/cdc/config | 200/200 | 97513/400 | False | False | DIFF |
| /base/cdc/dead-letters | 200/200 | 43/43 | True | True | OK |
| /base/cdc/retry-messages | 200/200 | 43/43 | True | True | OK |
| /base/cdc/status | 200/200 | 183/183 | False | True | OK |
| /base/config/1 | 200/200 | 33/33 | True | True | OK |
| /base/config/export | 200/200 | 90/90 | False | False | NONDET |
| /base/config/list | 200/200 | 53/53 | False | True | OK |
| /base/configServiceArea/1 | 200/200 | 33/33 | True | True | OK |
| /base/configServiceArea/export | 200/200 | 78/78 | False | False | NONDET |
| /base/configServiceArea/list | 200/200 | 53/53 | False | True | OK |
| /base/configServiceArea/listQuery | 200/200 | 43/45 | False | False | DIFF |
| /base/feeGantry/1 | 200/200 | 150/153 | False | False | DIFF |
| /base/feeGantry/export | 200/200 | 150/158 | False | False | DIFF |
| /base/feeGantry/list | 200/200 | 96/183 | False | False | NONDET |
| /base/feeStationEnter/1 | 200/200 | 77/33 | False | False | DIFF |
| /base/feeStationEnter/list | 200/200 | 97/53 | False | False | DIFF |
| /base/feerecords/1 | 200/200 | 150/154 | False | False | DIFF |
| /base/feerecords/export | 200/200 | 107/6236 | False | False | DIFF |
| /base/feerecords/list | 200/200 | 107/53 | False | False | DIFF |
| /base/feestationexit/1 | 200/200 | 150/158 | False | False | DIFF |
| /base/feestationexit/export | 200/200 | 150/163 | False | False | DIFF |
| /base/feestationexit/list | 200/200 | 97/188 | False | False | DIFF |
| /base/fitting/1 | 200/200 | 150/33 | False | False | DIFF |
| /base/fitting/list | 200/200 | 97/53 | False | False | DIFF |
| /base/fwqjcxx/1 | 200/200 | 33/33 | True | True | OK |
| /base/fwqjcxx/export | 200/200 | 90/90 | False | False | NONDET |
| /base/fwqjcxx/list | 200/200 | 53/53 | False | True | OK |
| /base/gantry/1 | 200/200 | 33/33 | True | True | OK |
| /base/gantry/export | 200/200 | 0/4 | False | True | OK |
| /base/gantry/list | 200/200 | 53/53 | False | True | OK |
| /base/gantry/listAll | 200/200 | 53/53 | False | True | OK |
| /base/gantryIp/1 | 200/200 | 33/33 | True | True | OK |
| /base/gantryIp/list | 200/200 | 53/53 | False | True | OK |
| /base/geometry/1 | 200/200 | 33/33 | True | True | OK |
| /base/geometry/export | 200/200 | 81/81 | False | False | NONDET |
| /base/geometry/getHenDa | 0/200 | 0/33 | False | False | DIFF |
| /base/geometry/list | 200/200 | 53/53 | False | True | OK |
| /base/geometry/syncAllGeometry | 200/200 | 1033/33 | False | False | DIFF |
| /base/geometry/syncAllGeometry1 | 200/200 | 33/33 | True | True | OK |
| /base/location/1 | 200/200 | 33/33 | True | True | OK |
| /base/location/list | 200/200 | 53/53 | False | True | OK |
| /base/org/1 | 200/200 | 33/33 | True | True | OK |
| /base/org/export | 200/200 | 81/81 | False | False | NONDET |
| /base/org/list | 200/200 | 53/53 | False | True | OK |
| /base/provcapture/1 | 200/200 | 77/33 | False | False | DIFF |
| /base/provcapture/list | 200/200 | 97/53 | False | False | DIFF |
| /base/section/1 | 200/200 | 33/33 | True | True | OK |
| /base/section/export | 200/200 | 81/81 | False | False | NONDET |
| /base/section/list | 200/200 | 53/53 | False | True | OK |
| /base/section/listAll | 200/200 | 53/53 | False | True | OK |
| /base/sfsjcxx/1 | 200/200 | 33/33 | True | True | OK |
| /base/sfsjcxx/export | 200/200 | 90/90 | False | False | NONDET |
| /base/sfsjcxx/list | 200/200 | 53/53 | False | True | OK |
| /base/sfzjcxx/1 | 200/200 | 33/33 | True | True | OK |
| /base/sfzjcxx/export | 200/200 | 90/90 | False | False | NONDET |
| /base/sfzjcxx/list | 200/200 | 53/53 | False | True | OK |
| /base/snapshotflow/1 | 200/200 | 150/156 | False | False | DIFF |
| /base/snapshotflow/earliest-time | 200/200 | 150/168 | False | False | DIFF |
| /base/snapshotflow/export | 200/200 | 107/6186 | False | False | DIFF |
| /base/snapshotflow/list | 200/200 | 107/53 | False | False | DIFF |
| /base/stationcapture/1 | 200/200 | 77/33 | False | False | DIFF |
| /base/stationcapture/list | 200/200 | 97/53 | False | False | DIFF |
| /base/toll/1 | 200/200 | 33/33 | True | True | OK |
| /base/toll/export | 200/200 | 90/90 | False | False | NONDET |
| /base/toll/list | 200/200 | 53/53 | False | True | OK |
| /base/toll/listAll | 200/200 | 53/53 | False | True | OK |
| /base/tollStationIp/1 | 200/200 | 33/33 | True | True | OK |
| /base/tollStationIp/list | 200/200 | 53/53 | False | True | OK |
| /base/trailtracks/1 | 200/200 | 33/33 | True | True | OK |
| /base/trailtracks/list | 200/200 | 53/53 | False | True | OK |
| /base/vehicleweight/1 | 200/200 | 77/33 | False | False | DIFF |
| /base/vehicleweight/list | 200/200 | 97/53 | False | False | DIFF |
| /captchaImage | 200/200 | 4028/8052 | False | False | NONDET |
| /common/download | 200/403 | 84/104 | False | False | DIFF |
| /common/download/resource | 200/200 | 0/0 | True | True | OK |
| /downTemplate/1 | 200/200 | 0/0 | True | True | OK |
| /flow/applyinfo/1 | 200/200 | 33/33 | True | True | OK |
| /flow/applyinfo/export | 200/200 | 81/81 | False | False | NONDET |
| /flow/applyinfo/list | 200/200 | 53/53 | False | True | OK |
| /flow/applyinfo/listAll | 200/200 | 53/53 | False | True | OK |
| /flow/currentnode/1 | 200/200 | 33/33 | True | True | OK |
| /flow/currentnode/export | 200/200 | 88/88 | False | False | NONDET |
| /flow/currentnode/getInfoByBillId/1 | 200/200 | 708/708 | False | True | OK |
| /flow/currentnode/list | 200/200 | 53/53 | False | True | OK |
| /flow/flowlist/1 | 200/200 | 33/33 | True | True | OK |
| /flow/flowlist/export | 200/200 | 87/87 | False | False | NONDET |
| /flow/flowlist/list | 200/200 | 53/53 | False | True | OK |
| /flow/flowlist/listnew | 200/200 | 43/43 | True | True | OK |
| /flow/flowname/1 | 200/200 | 33/33 | True | True | OK |
| /flow/flowname/export | 200/200 | 81/81 | False | False | NONDET |
| /flow/flowname/list | 200/200 | 53/53 | False | True | OK |
| /flow/flowname/listQuery | 200/200 | 53/53 | False | True | OK |
| /flow/flowtemplate/1 | 200/200 | 33/33 | True | True | OK |
| /flow/flowtemplate/export | 200/200 | 81/81 | False | False | NONDET |
| /flow/flowtemplate/flowlist | 200/200 | 43/43 | True | True | OK |
| /flow/flowtemplate/list | 200/200 | 53/53 | False | True | OK |
| /flow/messagedispose/1 | 200/200 | 33/33 | True | True | OK |
| /flow/messagedispose/export | 200/200 | 90/90 | False | False | NONDET |
| /flow/messagedispose/list | 200/200 | 53/53 | False | True | OK |
| /flow/messageinfo/1 | 200/200 | 33/33 | True | True | OK |
| /flow/messageinfo/export | 200/200 | 1507/89 | False | False | DIFF |
| /flow/messageinfo/exportShrz | 200/200 | 123/23 | False | False | DIFF |
| /flow/messageinfo/list | 200/200 | 912/89 | False | False | DIFF |
| /flow/messageinfo/listxx | 200/200 | 1350/89 | False | False | DIFF |
| /flow/messageinfo/listyb | 200/200 | 912/89 | False | False | DIFF |
| /flow/messageinfo/listyj | 200/200 | 938/89 | False | False | DIFF |
| /getInfo | 200/200 | 1979/1984 | False | False | DIFF |
| /getRouters | 200/200 | 8606/8606 | False | True | OK |
| /manager/aduitfree/1 | 200/200 | 33/33 | True | True | OK |
| /manager/aduitfree/export | 200/200 | 81/81 | False | False | NONDET |
| /manager/aduitfree/exportIncomeDetailList | 200/200 | 7211/6137 | False | False | DIFF |
| /manager/aduitfree/exportIncomeStatics | 200/200 | 8167/6115 | False | False | DIFF |
| /manager/aduitfree/incomeDetailList | 200/200 | 53/53 | False | True | OK |
| /manager/aduitfree/incomeStatics | 200/200 | 53/53 | False | True | OK |
| /manager/aduitfree/list | 200/200 | 53/53 | False | True | OK |
| /manager/bigScreen/carAudit | 200/200 | 110/110 | False | True | OK |
| /manager/bigScreen/carLocation | 200/200 | 43/43 | True | True | OK |
| /manager/bigScreen/carStatistics | 200/200 | 463/463 | False | True | OK |
| /manager/bigScreen/carVoList | 200/200 | 43/33 | False | False | DIFF |
| /manager/bigScreen/carWarning | 200/200 | 43/43 | True | True | OK |
| /manager/bigScreen/exceptRecordList | 200/200 | 53/53 | False | True | OK |
| /manager/bigScreen/exceptionCar | 200/200 | 43/43 | True | True | OK |
| /manager/bigScreen/export/approvals | 200/404 | 366/113 | False | False | DIFF |
| /manager/bigScreen/export/download/1 | 200/404 | 366/114 | False | False | DIFF |
| /manager/bigScreen/export/status/1 | 200/404 | 366/112 | False | False | DIFF |
| /manager/bigScreen/incomeStatistic | 200/200 | 43/33 | False | False | DIFF |
| /manager/bigScreen/orgList | 200/200 | 102/33 | False | False | DIFF |
| /manager/bigScreen/sectionList | 200/200 | 103/87 | False | False | DIFF |
| /manager/bigScreen/tollGantryFwqList | 200/200 | 102/102 | True | True | OK |
| /manager/bigScreen/topTen | 200/200 | 43/33 | False | False | DIFF |
| /manager/busstest/1 | 200/200 | 33/33 | True | True | OK |
| /manager/busstest/export | 200/200 | 81/81 | False | False | NONDET |
| /manager/busstest/list | 200/200 | 53/53 | False | True | OK |
| /manager/carinfo/1 | 200/200 | 33/33 | True | True | OK |
| /manager/carinfo/export | 200/200 | 7386/6166 | False | False | DIFF |
| /manager/carinfo/list | 200/200 | 53/53 | False | True | OK |
| /manager/carinfo/listAll | 200/200 | 53/53 | False | True | OK |
| /manager/carsuspiciousback/1 | 200/200 | 33/33 | True | True | OK |
| /manager/carsuspiciousback/export | 200/200 | 87/87 | False | False | NONDET |
| /manager/carsuspiciousback/list | 200/200 | 53/53 | False | True | OK |
| /manager/cartrackinfo/1 | 200/200 | 33/33 | True | True | OK |
| /manager/cartrackinfo/carSnapShot | 200/200 | 33/33 | True | True | OK |
| /manager/cartrackinfo/export | 200/200 | 87/87 | False | False | NONDET |
| /manager/cartrackinfo/list | 200/200 | 53/53 | False | True | OK |
| /manager/cartrackinfo/listByCarByTime | 200/200 | 53/53 | False | True | OK |
| /manager/cartrackinfo/listByCarId | 200/200 | 53/53 | False | True | OK |
| /manager/carwarning/1 | 200/200 | 33/33 | True | True | OK |
| /manager/carwarning/export | 200/200 | 7505/6252 | False | False | DIFF |
| /manager/carwarning/list | 200/200 | 53/53 | False | True | OK |
| /manager/confimfree/1 | 200/200 | 33/33 | True | True | OK |
| /manager/confimfree/carStatics | 200/200 | 53/53 | False | True | OK |
| /manager/confimfree/concernedList | 200/200 | 53/53 | False | True | OK |
| /manager/confimfree/except/1 | 200/200 | 51/51 | True | True | OK |
| /manager/confimfree/export | 200/200 | 8294/6201 | False | False | DIFF |
| /manager/confimfree/exportCarStatics | 200/200 | 7585/6283 | False | False | DIFF |
| /manager/confimfree/exportConcernedList | 200/200 | 8369/6191 | False | False | DIFF |
| /manager/confimfree/list | 200/200 | 53/53 | False | True | OK |
| /manager/confimfree/listCarNo | 200/200 | 53/53 | False | True | OK |
| /manager/confimfree/listCount | 200/200 | 33/33 | True | True | OK |
| /manager/exceptrecord/1 | 200/200 | 33/33 | True | True | OK |
| /manager/exceptrecord/exceptRecordCount | 200/200 | 33/33 | True | True | OK |
| /manager/exceptrecord/export | 200/200 | 7685/6450 | False | False | DIFF |
| /manager/exceptrecord/exportOrgId | 200/200 | 7685/6450 | False | False | DIFF |
| /manager/exceptrecord/getConfirmId/1 | 200/200 | 45/45 | True | True | OK |
| /manager/exceptrecord/list | 200/200 | 53/53 | False | True | OK |
| /manager/exceptrecord/listCarNo | 200/200 | 53/53 | False | True | OK |
| /manager/exceptrecord/listCarOrgId | 200/200 | 53/53 | False | True | OK |
| /manager/exceptrecord/listExceptId | 200/200 | 53/53 | False | True | OK |
| /manager/feerecord/1 | 200/200 | 33/33 | True | True | OK |
| /manager/feerecord/export | 200/200 | 81/81 | False | False | NONDET |
| /manager/feerecord/list | 200/200 | 53/53 | False | True | OK |
| /manager/fwqclls/1 | 200/200 | 76/33 | False | False | DIFF |
| /manager/fwqclls/list | 200/200 | 96/53 | False | False | DIFF |
| /manager/gantrycar/1 | 200/200 | 33/33 | True | True | OK |
| /manager/gantrycar/export | 200/200 | 8364/6213 | False | False | DIFF |
| /manager/gantrycar/list | 200/200 | 53/53 | False | True | OK |
| /manager/gantrytrade/1 | 200/200 | 33/33 | True | True | OK |
| /manager/gantrytrade/export | 200/200 | 8472/6264 | False | False | DIFF |
| /manager/gantrytrade/list | 200/200 | 53/53 | False | True | OK |
| /manager/querylog/1 | 200/200 | 33/33 | True | True | OK |
| /manager/querylog/export | 200/200 | 7389/6429 | False | False | DIFF |
| /manager/querylog/list | 200/200 | 53/3100 | False | False | DIFF |
| /manager/routedetail/1 | 200/200 | 33/33 | True | True | OK |
| /manager/routedetail/export | 200/200 | 87/87 | False | False | NONDET |
| /manager/routedetail/list | 200/200 | 53/53 | False | True | OK |
| /manager/routeinfo/1 | 200/200 | 33/33 | True | True | OK |
| /manager/routeinfo/export | 200/200 | 8278/6146 | False | False | DIFF |
| /manager/routeinfo/list | 200/200 | 53/53 | False | True | OK |
| /manager/splitrecord/1 | 200/200 | 33/33 | True | True | OK |
| /manager/splitrecord/export | 200/200 | 8289/6152 | False | False | DIFF |
| /manager/splitrecord/list | 200/200 | 53/53 | False | True | OK |
| /manager/suspicious/1 | 200/200 | 33/33 | True | True | OK |
| /manager/suspicious/export | 200/200 | 7567/6296 | False | False | DIFF |
| /manager/suspicious/exportAbnormalPassage | 200/200 | 113/23 | False | False | DIFF |
| /manager/suspicious/exportHistory | 200/200 | 7567/6305 | False | False | DIFF |
| /manager/suspicious/history/1 | 200/200 | 33/33 | True | True | OK |
| /manager/suspicious/list | 200/200 | 53/53 | False | True | OK |
| /manager/suspicious/listAll | 200/200 | 53/53 | False | True | OK |
| /manager/suspicious/listCarNo | 200/200 | 53/53 | False | True | OK |
| /manager/suspicious/listFileCarNo | 200/200 | 53/53 | False | True | OK |
| /manager/suspicious/listHistory | 200/200 | 53/53 | False | True | OK |
| /manager/suspiciouscheck/1 | 200/200 | 33/33 | True | True | OK |
| /manager/suspiciouscheck/export | 200/200 | 8312/6174 | False | False | NONDET |
| /manager/suspiciouscheck/list | 200/200 | 53/53 | False | True | OK |
| /manager/warningrule/1 | 200/200 | 33/33 | True | True | OK |
| /manager/warningrule/export | 200/200 | 8185/6112 | False | False | DIFF |
| /manager/warningrule/list | 200/200 | 53/53 | False | True | OK |
| /manager/whiteinfo/1 | 200/200 | 33/33 | True | True | OK |
| /manager/whiteinfo/export | 200/200 | 8244/6117 | False | False | DIFF |
| /manager/whiteinfo/list | 200/200 | 53/53 | False | True | OK |
| /monitor/bigscreen/metrics | 200/404 | 446/104 | False | False | DIFF |
| /monitor/bigscreen/switches | 200/404 | 415/105 | False | False | DIFF |
| /monitor/cache/ | 200/200 | 84/6785 | False | False | NONDET |
| /monitor/job/1 | 200/200 | 33/33 | True | True | OK |
| /monitor/job/export | 200/200 | 75/75 | False | False | NONDET |
| /monitor/job/list | 200/200 | 53/53 | False | True | OK |
| /monitor/jobLog/1 | 200/200 | 73/33 | False | False | DIFF |
| /monitor/jobLog/export | 200/200 | 75/75 | False | False | NONDET |
| /monitor/jobLog/list | 200/200 | 53/53 | False | True | OK |
| /monitor/logininfor/export | 200/200 | 75/75 | False | False | NONDET |
| /monitor/logininfor/list | 200/200 | 321/321 | False | False | DIFF |
| /monitor/online/list | 200/200 | 313/317 | False | False | DIFF |
| /monitor/operlog/export | 200/200 | 75/75 | False | False | NONDET |
| /monitor/operlog/list | 200/200 | 5347/4655 | False | False | NONDET |
| /monitor/server/ | 200/200 | 86/1076 | False | False | NONDET |
| /system/config/1 | 200/200 | 378/378 | False | True | OK |
| /system/config/configKey/1 | 200/200 | 21/21 | True | True | OK |
| /system/config/export | 200/200 | 75/75 | False | False | NONDET |
| /system/config/list | 200/200 | 2885/2885 | False | True | OK |
| /system/dept/1 | 200/200 | 33/33 | True | True | OK |
| /system/dept/getCompanyList | 200/200 | 43/43 | True | True | OK |
| /system/dept/getList | 200/200 | 24222/24222 | False | False | DIFF |
| /system/dept/list | 200/200 | 24222/24222 | False | False | DIFF |
| /system/dept/list/exclude/1 | 200/200 | 24222/24222 | False | False | DIFF |
| /system/dept/roleDeptTreeselect/1 | 200/200 | 1840/1840 | False | True | OK |
| /system/dept/treeselect | 200/200 | 1822/1822 | False | True | OK |
| /system/dept/treeselectNew | 200/200 | 43/43 | True | True | OK |
| /system/dict/data/1 | 200/200 | 310/310 | False | True | OK |
| /system/dict/data/export | 200/200 | 75/75 | False | False | NONDET |
| /system/dict/data/list | 200/200 | 2799/2799 | False | True | OK |
| /system/dict/data/type/1 | 200/200 | 43/43 | True | True | OK |
| /system/dict/data/typemore/1 | 200/200 | 43/43 | True | True | OK |
| /system/dict/type/1 | 200/200 | 236/236 | False | True | OK |
| /system/dict/type/export | 200/200 | 75/75 | False | False | NONDET |
| /system/dict/type/list | 200/200 | 1879/1879 | False | True | OK |
| /system/dict/type/optionselect | 200/200 | 9980/9980 | False | True | OK |
| /system/file/1 | 200/200 | 43/43 | True | True | OK |
| /system/file/1/1 | 200/200 | 0/0 | True | True | OK |
| /system/file/getInfoById/1 | 200/200 | 33/33 | True | True | OK |
| /system/file/getNewCa | 200/200 | 44/44 | True | True | OK |
| /system/file/list | 200/200 | 53/53 | False | True | OK |
| /system/file/view/1/1 | 200/403 | 84/109 | False | False | DIFF |
| /system/indexmenu/1 | 200/200 | 33/33 | True | True | OK |
| /system/indexmenu/export | 200/200 | 87/87 | False | False | NONDET |
| /system/indexmenu/list | 200/200 | 3664/3664 | False | True | OK |
| /system/indexmenu/mylist | 200/200 | 861/43 | False | False | DIFF |
| /system/menu/1 | 200/200 | 369/369 | False | True | OK |
| /system/menu/list | 200/200 | 70258/70258 | False | False | DIFF |
| /system/menu/roleMenuTreeselect/1 | 200/200 | 8396/8396 | False | True | OK |
| /system/menu/treeselect | 200/200 | 8378/8378 | False | True | OK |
| /system/notice/1 | 200/200 | 33/33 | True | True | OK |
| /system/notice/list | 200/200 | 53/53 | False | True | OK |
| /system/notice/listquery | 200/200 | 53/53 | False | True | OK |
| /system/notice/view/1 | 200/403 | 84/109 | False | False | DIFF |
| /system/post/1 | 200/200 | 33/33 | True | True | OK |
| /system/post/export | 200/200 | 75/75 | False | False | NONDET |
| /system/post/list | 200/200 | 53/53 | False | True | OK |
| /system/post/optionselect | 200/200 | 43/43 | True | True | OK |
| /system/role/1 | 200/200 | 376/376 | False | True | OK |
| /system/role/export | 200/200 | 75/75 | False | False | NONDET |
| /system/role/list | 200/200 | 1061/1061 | False | True | OK |
| /system/role/optionselect | 200/200 | 1051/1051 | False | True | OK |
| /system/role/selectlist | 200/200 | 1051/1051 | False | True | OK |
| /system/upgradeInfo/1 | 200/200 | 33/33 | True | True | OK |
| /system/upgradeInfo/export | 200/200 | 87/87 | False | False | NONDET |
| /system/upgradeInfo/list | 200/200 | 53/53 | False | True | OK |
| /system/upgradeInfo/newest | 200/200 | 33/33 | True | True | OK |
| /system/user/ | 200/200 | 727/727 | False | True | OK |
| /system/user/currentUser | 200/200 | 747/747 | False | True | OK |
| /system/user/export | 200/200 | 75/75 | False | False | NONDET |
| /system/user/getroleUser/1 | 200/200 | 43/43 | True | True | OK |
| /system/user/importTemplate | 200/200 | 75/75 | False | False | NONDET |
| /system/user/list | 200/200 | 10431/10436 | False | False | DIFF |
| /system/user/list/dept | 200/200 | 2803/2808 | False | False | DIFF |
| /system/user/listAll | 200/200 | 53/53 | False | True | OK |
| /system/user/listMy | 200/200 | 1484/1489 | False | False | DIFF |
| /system/user/listSameUtil | 200/200 | 53/53 | False | True | OK |
| /system/user/listTenantIdAll | 200/200 | 53/53 | False | True | OK |
| /system/user/listutil | 200/200 | 53/53 | False | True | OK |
| /system/user/profile/ | 200/200 | 96/1960 | False | False | DIFF |
| /test/user/1 | 200/200 | 117/117 | False | True | OK |
| /test/user/list | 200/200 | 193/193 | False | True | OK |
| /tool/gen/1 | 200/200 | 116/23 | False | False | DIFF |
| /tool/gen/all/list | 200/200 | 43/43 | True | True | OK |
| /tool/gen/batchGenCode | 200/200 | 83/23 | False | False | DIFF |
| /tool/gen/column/1 | 200/200 | 41/41 | False | True | OK |
| /tool/gen/db/list | 200/200 | 17112/17146 | False | True | OK |
| /tool/gen/download/1 | 200/200 | 113/23 | False | False | DIFF |
| /tool/gen/genCode/1 | 200/200 | 113/23 | False | False | DIFF |
| /tool/gen/list | 200/200 | 53/53 | False | True | OK |
| /tool/gen/preview/1 | 200/200 | 116/23 | False | False | DIFF |
| /tool/gen/synchDb/1 | 200/200 | 113/23 | False | False | DIFF |

## Real differences (DIFF)
- `/base/cdc/config`: status 200/200, bytes 97513/400
- `/base/configServiceArea/listQuery`: status 200/200, bytes 43/45
- `/base/feeGantry/1`: status 200/200, bytes 150/153
- `/base/feeGantry/export`: status 200/200, bytes 150/158
- `/base/feeStationEnter/1`: status 200/200, bytes 77/33
- `/base/feeStationEnter/list`: status 200/200, bytes 97/53
- `/base/feerecords/1`: status 200/200, bytes 150/154
- `/base/feerecords/export`: status 200/200, bytes 107/6236
- `/base/feerecords/list`: status 200/200, bytes 107/53
- `/base/feestationexit/1`: status 200/200, bytes 150/158
- `/base/feestationexit/export`: status 200/200, bytes 150/163
- `/base/feestationexit/list`: status 200/200, bytes 97/188
- `/base/fitting/1`: status 200/200, bytes 150/33
- `/base/fitting/list`: status 200/200, bytes 97/53
- `/base/geometry/getHenDa`: status 0/200, bytes 0/33
- `/base/geometry/syncAllGeometry`: status 200/200, bytes 1033/33
- `/base/provcapture/1`: status 200/200, bytes 77/33
- `/base/provcapture/list`: status 200/200, bytes 97/53
- `/base/snapshotflow/1`: status 200/200, bytes 150/156
- `/base/snapshotflow/earliest-time`: status 200/200, bytes 150/168
- `/base/snapshotflow/export`: status 200/200, bytes 107/6186
- `/base/snapshotflow/list`: status 200/200, bytes 107/53
- `/base/stationcapture/1`: status 200/200, bytes 77/33
- `/base/stationcapture/list`: status 200/200, bytes 97/53
- `/base/vehicleweight/1`: status 200/200, bytes 77/33
- `/base/vehicleweight/list`: status 200/200, bytes 97/53
- `/common/download`: status 200/403, bytes 84/104
- `/flow/messageinfo/export`: status 200/200, bytes 1507/89
- `/flow/messageinfo/exportShrz`: status 200/200, bytes 123/23
- `/flow/messageinfo/list`: status 200/200, bytes 912/89
- `/flow/messageinfo/listxx`: status 200/200, bytes 1350/89
- `/flow/messageinfo/listyb`: status 200/200, bytes 912/89
- `/flow/messageinfo/listyj`: status 200/200, bytes 938/89
- `/getInfo`: status 200/200, bytes 1979/1984
- `/manager/aduitfree/exportIncomeDetailList`: status 200/200, bytes 7211/6137
- `/manager/aduitfree/exportIncomeStatics`: status 200/200, bytes 8167/6115
- `/manager/bigScreen/carVoList`: status 200/200, bytes 43/33
- `/manager/bigScreen/export/approvals`: status 200/404, bytes 366/113
- `/manager/bigScreen/export/download/1`: status 200/404, bytes 366/114
- `/manager/bigScreen/export/status/1`: status 200/404, bytes 366/112
- `/manager/bigScreen/incomeStatistic`: status 200/200, bytes 43/33
- `/manager/bigScreen/orgList`: status 200/200, bytes 102/33
- `/manager/bigScreen/sectionList`: status 200/200, bytes 103/87
- `/manager/bigScreen/topTen`: status 200/200, bytes 43/33
- `/manager/carinfo/export`: status 200/200, bytes 7386/6166
- `/manager/carwarning/export`: status 200/200, bytes 7505/6252
- `/manager/confimfree/export`: status 200/200, bytes 8294/6201
- `/manager/confimfree/exportCarStatics`: status 200/200, bytes 7585/6283
- `/manager/confimfree/exportConcernedList`: status 200/200, bytes 8369/6191
- `/manager/exceptrecord/export`: status 200/200, bytes 7685/6450
- `/manager/exceptrecord/exportOrgId`: status 200/200, bytes 7685/6450
- `/manager/fwqclls/1`: status 200/200, bytes 76/33
- `/manager/fwqclls/list`: status 200/200, bytes 96/53
- `/manager/gantrycar/export`: status 200/200, bytes 8364/6213
- `/manager/gantrytrade/export`: status 200/200, bytes 8472/6264
- `/manager/querylog/export`: status 200/200, bytes 7389/6429
- `/manager/querylog/list`: status 200/200, bytes 53/3100
- `/manager/routeinfo/export`: status 200/200, bytes 8278/6146
- `/manager/splitrecord/export`: status 200/200, bytes 8289/6152
- `/manager/suspicious/export`: status 200/200, bytes 7567/6296
- `/manager/suspicious/exportAbnormalPassage`: status 200/200, bytes 113/23
- `/manager/suspicious/exportHistory`: status 200/200, bytes 7567/6305
- `/manager/warningrule/export`: status 200/200, bytes 8185/6112
- `/manager/whiteinfo/export`: status 200/200, bytes 8244/6117
- `/monitor/bigscreen/metrics`: status 200/404, bytes 446/104
- `/monitor/bigscreen/switches`: status 200/404, bytes 415/105
- `/monitor/jobLog/1`: status 200/200, bytes 73/33
- `/monitor/logininfor/list`: status 200/200, bytes 321/321
- `/monitor/online/list`: status 200/200, bytes 313/317
- `/system/dept/getList`: status 200/200, bytes 24222/24222
- `/system/dept/list`: status 200/200, bytes 24222/24222
- `/system/dept/list/exclude/1`: status 200/200, bytes 24222/24222
- `/system/file/view/1/1`: status 200/403, bytes 84/109
- `/system/indexmenu/mylist`: status 200/200, bytes 861/43
- `/system/menu/list`: status 200/200, bytes 70258/70258
- `/system/notice/view/1`: status 200/403, bytes 84/109
- `/system/user/list`: status 200/200, bytes 10431/10436
- `/system/user/list/dept`: status 200/200, bytes 2803/2808
- `/system/user/listMy`: status 200/200, bytes 1484/1489
- `/system/user/profile/`: status 200/200, bytes 96/1960
- `/tool/gen/1`: status 200/200, bytes 116/23
- `/tool/gen/batchGenCode`: status 200/200, bytes 83/23
- `/tool/gen/download/1`: status 200/200, bytes 113/23
- `/tool/gen/genCode/1`: status 200/200, bytes 113/23
- `/tool/gen/preview/1`: status 200/200, bytes 116/23
- `/tool/gen/synchDb/1`: status 200/200, bytes 113/23