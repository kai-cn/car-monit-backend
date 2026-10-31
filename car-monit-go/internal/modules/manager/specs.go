// JAVA 对照: ruoyi-system/src/main/resources/mapper/manager/*.xml 的 selectXxxList
// 类/职责: manager 各标准表的声明式规格（列、关联、条件、排序）
// 对应 Go 文件: internal/modules/manager/specs.go
//
// DIFF: XML 的 <if> 顺序被照抄成 conditions 顺序；like / null_only 语义见 query.go。
package manager

import (
	"github.com/gin-gonic/gin"
)

var (
	// car_fee_record
	feeRecordSpec = &tableSpec{
		table:     carFeeRecordTable,
		selectSQL: carFeeRecordSelectColumns,
		orderBy:   "t.create_time desc,t.id",
		columns:   carFeeRecordColumns,
		prototype: &carFeeRecord{},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("carId", "t.car_id"), eqCond("carNo", "t.car_no"),
			eqCond("carType", "t.car_type"), eqCond("carVehicle", "t.car_vehicle"),
			eqCond("inStationId", "t.in_station_id"), eqCond("inStation", "t.in_station"),
			nullCond("inTime", "t.in_time"), eqCond("outStationId", "t.out_station_id"),
			eqCond("outStation", "t.out_station"), nullCond("outTime", "t.out_time"),
			eqCond("chargeType", "t.charge_type"), nullCond("amount", "t.amount"),
			eqCond("exceptId", "t.except_id"), eqCond("backCol1", "t.back_col1"),
			eqCond("backCol2", "t.back_col2"), eqCond("status", "t.status"),
			nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
			nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
			dateGe("applyTime1", "create_time"), dateLtNextDay("applyTime2", "create_time"),
		},
	}

	// car_route_detail
	routeDetailSpec = &tableSpec{
		table:     carRouteDetailTable,
		selectSQL: carRouteDetailSelectColumns,
		orderBy:   "t.create_time desc,t.id",
		columns:   carRouteDetailColumns,
		prototype: &carRouteDetail{},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("routeId", "t.route_id"), eqCond("carId", "t.car_id"),
			eqCond("carNo", "t.car_no"), eqCond("dataSource", "t.data_source"),
			likeCond("dataSourceName", "t.data_source_name"), nullCond("lastPassTime", "t.last_pass_time"),
			eqCond("lastPassPicture", "t.last_pass_picture"), eqCond("lastPassType", "t.last_pass_type"),
			eqCond("lastPassAddress", "t.last_pass_address"), eqCond("lastPassLongitude", "t.last_pass_longitude"),
			eqCond("lastPassLatitude", "t.last_pass_latitude"), eqCond("lastPassCardirection", "t.last_pass_cardirection"),
			eqCond("roadSectionId", "t.road_section_id"), likeCond("roadSectionName", "t.road_section_name"),
			nullCond("nextPassTime", "t.next_pass_time"), eqCond("nextPassType", "t.next_pass_type"),
			eqCond("nextPassAddress", "t.next_pass_address"), eqCond("nextPassLongitude", "t.next_pass_longitude"),
			eqCond("nextPassLatitude", "t.next_pass_latitude"), eqCond("orgId", "t.org_id"),
			likeCond("orgName", "t.org_name"), eqCond("backCol1", "t.back_col1"),
			eqCond("backCol2", "t.back_col2"), eqCond("status", "t.status"),
			nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
			nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
			dateGe("applyTime1", "create_time"), dateLtNextDay("applyTime2", "create_time"),
		},
	}

	// car_route_info
	routeInfoSpec = &tableSpec{
		table:     carRouteInfoTable,
		selectSQL: carRouteInfoSelectColumns,
		orderBy:   "t.create_time desc,t.id",
		columns:   carRouteInfoColumns,
		prototype: &carRouteInfo{},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("carId", "t.car_id"), eqCond("carNo", "t.car_no"),
			eqCond("carType", "t.car_type"), eqCond("carVehicle", "t.car_vehicle"),
			nullCond("carNum", "t.car_num"), eqCond("startAddress", "t.start_address"),
			eqCond("startLongitude", "t.start_longitude"), eqCond("startLatitude", "t.start_latitude"),
			eqCond("endAddress", "t.end_address"), eqCond("endLongitude", "t.end_longitude"),
			eqCond("endLatitude", "t.end_latitude"), eqCond("routeDetail", "t.route_detail"),
			eqCond("backCol1", "t.back_col1"), eqCond("backCol2", "t.back_col2"),
			eqCond("status", "t.status"), nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
			nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
			dateGe("applyTime1", "create_time"), dateLtNextDay("applyTime2", "create_time"),
		},
	}

	// car_split_record
	splitRecordSpec = &tableSpec{
		table:     carSplitRecordTable,
		selectSQL: carSplitRecordSelectColumns,
		orderBy:   "t.create_time desc,t.id",
		columns:   carSplitRecordColumns,
		prototype: &carSplitRecord{},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("carId", "t.car_id"), eqCond("carNo", "t.car_no"),
			eqCond("carType", "t.car_type"), eqCond("carVehicle", "t.car_vehicle"),
			eqCond("passType", "t.pass_type"), eqCond("inStationId", "t.in_station_id"),
			eqCond("inStation", "t.in_station"), nullCond("inTime", "t.in_time"),
			eqCond("outStationId", "t.out_station_id"), eqCond("outStation", "t.out_station"),
			nullCond("outTime", "t.out_time"), nullCond("amount", "t.amount"),
			eqCond("backCol1", "t.back_col1"), eqCond("backCol2", "t.back_col2"),
			eqCond("status", "t.status"), nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
			nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
			dateGe("applyTime1", "create_time"), dateLtNextDay("applyTime2", "create_time"),
		},
	}

	// car_white_info
	whiteInfoSpec = &tableSpec{
		table:        carWhiteInfoTable,
		selectSQL:    carWhiteInfoSelectColumns,
		fromSQL:      "car_white_info t left join sys_user su on su.user_id = t.create_by left join sys_dept sd on t.eps_id = sd.dept_id",
		selectSuffix: ",concat(sd.dept_name, ' ', su.nick_name) AS create_info",
		orderBy:      "t.create_time desc,t.id",
		columns:      carWhiteInfoColumns,
		prototype:    &carWhiteInfo{},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("plateColor", "t.plate_color"), eqCond("carNo", "t.car_no"),
			likeCond("carNoQuery", "t.car_no"), eqCond("carType", "t.car_type"),
			eqCond("carVehicle", "t.car_vehicle"), nullCond("carNum", "t.car_num"),
			eqCond("fileIds", "t.file_ids"), eqCond("backCol1", "t.back_col1"),
			eqCond("backCol2", "t.back_col2"), eqCond("status", "t.status"),
			nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
			nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
		},
	}

	// car_query_log
	queryLogSpec = &tableSpec{
		table:     carQueryLogTable,
		selectSQL: carQueryLogSelectColumns,
		orderBy:   "t.create_time desc,t.id",
		columns:   carQueryLogColumns,
		prototype: &carQueryLog{},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("userId", "t.user_id"),
			likeCond("userName", "t.user_name"), eqCond("userIp", "t.user_ip"),
			eqCond("modelType", "t.model_type"), eqCond("menuPoint", "t.menu_point"),
			nullCond("createBy", "t.create_by"),
			dateTimeGe("applyTime1", "create_time"), dateTimeLe("applyTime2", "create_time"),
		},
	}

	// car_suspicious_check
	suspiciousCheckSpec = &tableSpec{
		table:     carSuspiciousCheckTable,
		selectSQL: carSuspiciousCheckSelectColumns,
		orderBy:   "t.create_time,t.id",
		columns:   carSuspiciousCheckColumns,
		prototype: &carSuspiciousCheck{},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("carId", "t.car_id"), eqCond("carNo", "t.car_no"),
			eqCond("suspicousFlag", "t.suspicous_flag"), eqCond("attachments", "t.attachments"),
			eqCond("escapedType", "t.escaped_type"), eqCond("backCol1", "t.back_col1"),
			nullCond("chargeAmount", "t.charge_amount"), nullCond("totalAmount", "t.total_amount"),
			eqCond("backCol2", "t.back_col2"), nullCond("difAmount", "t.dif_amount"),
			eqCond("status", "t.status"), nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
			nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
			dateGe("applyTime1", "create_time"), dateLtNextDay("applyTime2", "create_time"),
		},
	}

	// car_warning_rule
	warningRuleSpec = &tableSpec{
		table:     carWarningRuleTable,
		selectSQL: carWarningRuleSelectColumns,
		orderBy:   "t.create_time desc,t.id",
		columns:   carWarningRuleColumns,
		prototype: &carWarningRule{},
		conditions: []cond{
			eqCond("id", "t.id"), likeCond("ruleName", "t.rule_name"),
			eqCond("noticeRangeId", "t.notice_range_id"), likeCond("noticeRangeAnme", "t.notice_range_anme"),
			eqCond("notice", "t.notice"), eqCond("noticeType", "t.notice_type"),
			eqCond("noticeUserId", "t.notice_user_id"), likeCond("noticeUserName", "t.notice_user_name"),
			eqCond("orgId", "t.org_id"), likeCond("orgName", "t.org_name"),
			eqCond("backCol1", "t.back_col1"), eqCond("backCol2", "t.back_col2"),
			eqCond("status", "t.status"), nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
			nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
			dateGe("applyTime1", "create_time"), dateLtNextDay("applyTime2", "create_time"),
		},
	}

	// gantry_car
	gantryCarSpec = &tableSpec{
		table:     gantryCarTable,
		selectSQL: gantryCarSelectColumns,
		orderBy:   "t.create_time desc,t.id",
		columns:   gantryCarColumns,
		prototype: &gantryCar{},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("carNo", "t.car_no"), eqCond("carType", "t.car_type"),
			eqCond("carVehicle", "t.car_vehicle"), nullCond("carNum", "t.car_num"),
			eqCond("inStationId", "t.in_station_id"), eqCond("inStation", "t.in_station"),
			nullCond("inTime", "t.in_time"), eqCond("gantryStationId", "t.gantry_station_id"),
			eqCond("gantrytStation", "t.gantryt_station"), nullCond("gantryTime", "t.gantry_time"),
			eqCond("fileIds", "t.file_ids"), eqCond("backCol1", "t.back_col1"),
			eqCond("backCol2", "t.back_col2"), eqCond("status", "t.status"),
			nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
			nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
			dateGe("applyTime1", "create_time"), dateLtNextDay("applyTime2", "create_time"),
		},
	}

	// gantry_trade_info
	gantryTradeSpec = &tableSpec{
		table:     gantryTradeInfoTable,
		selectSQL: gantryTradeInfoSelectColumns,
		orderBy:   "t.create_time desc,t.id",
		columns:   gantryTradeInfoColumns,
		prototype: &gantryTradeInfo{},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("carNo", "t.car_no"), eqCond("carType", "t.car_type"),
			eqCond("carVehicle", "t.car_vehicle"), nullCond("carNum", "t.car_num"),
			eqCond("inStationId", "t.in_station_id"), eqCond("inStation", "t.in_station"),
			nullCond("inTime", "t.in_time"), eqCond("outStationId", "t.out_station_id"),
			eqCond("outStation", "t.out_station"), nullCond("outTime", "t.out_time"),
			eqCond("chargeType", "t.charge_type"), nullCond("amount", "t.amount"),
			eqCond("backCol1", "t.back_col1"), eqCond("backCol2", "t.back_col2"),
			eqCond("status", "t.status"), nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
			nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
			dateGe("applyTime1", "create_time"), dateLtNextDay("applyTime2", "create_time"),
		},
	}

	// buss_test
	bussTestSpec = &tableSpec{
		table:     bussTestTable,
		selectSQL: bussTestSelectColumns,
		orderBy:   "t.create_time desc,t.id",
		columns:   bussTestColumns,
		prototype: &bussTest{},
		conditions: []cond{
			eqCond("id", "t.id"), likeCond("billName", "t.bill_name"), eqCond("billType", "t.bill_type"),
			nullCond("amount", "t.amount"), nullCond("deptId", "t.dept_id"), nullCond("userId", "t.user_id"),
			nullCond("applyTime", "t.apply_time"), nullCond("applyTime2", "t.apply_time2"),
			eqCond("fileIds", "t.file_ids"), eqCond("flowKey", "t.flow_key"),
			eqCond("flowRuid", "t.flow_ruid"), eqCond("flowApplyOid", "t.flow_apply_oid"),
			eqCond("flowStatus", "t.flow_status"), nullCond("shTime", "t.sh_time"),
			eqCond("backCol1", "t.back_col1"), eqCond("backCol2", "t.back_col2"),
			eqCond("status", "t.status"), nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
			nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
		},
	}

	// car_suspicious_back —— 备份表，实体与排序都跟随 CarSuspiciousBackMapper.xml
	// JAVA 对照: mapper/manager/CarSuspiciousBackMapper.xml:109（order by t.create_time desc,t.id）
	suspiciousBackSpec = &tableSpec{
		table:     carSuspiciousBackTable,
		selectSQL: carSuspiciousBackSelectColumns,
		orderBy:   "t.create_time desc,t.id",
		columns:   carSuspiciousBackColumns,
		prototype: &carSuspiciousBack{},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("plateColor", "t.plate_color"), eqCond("carNo", "t.car_no"),
			eqCond("carType", "t.car_type"), eqCond("carVehicle", "t.car_vehicle"),
			nullCond("carNum", "t.car_num"), eqCond("passType", "t.pass_type"),
			eqCond("inStationId", "t.in_station_id"), eqCond("inStation", "t.in_station"),
			nullCond("inTime", "t.in_time"), eqCond("outStationId", "t.out_station_id"),
			eqCond("outStation", "t.out_station"), nullCond("outTime", "t.out_time"),
			eqCond("gantryStationId", "t.gantry_station_id"), eqCond("gantrytStation", "t.gantryt_station"),
			nullCond("gantryTime", "t.gantry_time"), eqCond("fileIds", "t.file_ids"),
			eqCond("outGantryStationId", "t.out_gantry_station_id"), eqCond("outGantrytStation", "t.out_gantryt_station"),
			nullCond("outGantryTime", "t.out_gantry_time"), eqCond("outFileIds", "t.out_file_ids"),
			eqCond("escapedType", "t.escaped_type"), likeCond("escapedTypeName", "t.escaped_type_name"),
			nullCond("escapedNum", "t.escaped_num"), eqCond("isExcept", "t.is_except"),
			eqCond("exceptRemark", "t.except_remark"), eqCond("exceptFileIds", "t.except_file_ids"),
			eqCond("checkStatus", "t.check_status"), eqCond("orgId", "t.org_id"),
			likeCond("orgName", "t.org_name"), eqCond("isWhite", "t.is_white"),
			eqCond("whiteRemark", "t.white_remark"), eqCond("whiteFileIds", "t.white_file_ids"),
			eqCond("roadCode", "t.road_code"), likeCond("roadName", "t.road_name"),
			eqCond("sectionCode", "t.section_code"), likeCond("sectionName", "t.section_name"),
			eqCond("trackId", "t.track_id"), eqCond("trackJosn", "t.track_josn"),
			eqCond("trackNames", "t.track_names"), eqCond("backCol1", "t.back_col1"),
			eqCond("backCol2", "t.back_col2"), eqCond("status", "t.status"),
			nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
			nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
		},
	}

	// 可疑车辆历史列表 —— Java 用的是 CarSuspicious 实体 + selectCarSuspiciousVo，
	// 只是表换成 car_suspicious_back、排序 t.id（CarSuspiciousMapper.xml:195）。
	suspiciousHistSpec = &tableSpec{
		table:      carSuspiciousBackTable,
		selectSQL:  carSuspiciousSelectColumns,
		orderBy:    "t.id",
		columns:    carSuspiciousColumns,
		prototype:  &carSuspicious{},
		conditions: suspiciousSpec.conditions,
	}

	// car_track_info
	trackInfoSpec = &tableSpec{
		table:        carTrackInfoTable,
		selectSQL:    carTrackInfoSelectColumns,
		detailSuffix: ",t.track_josn",
		orderBy:      "t.create_time,t.id",
		columns:      carTrackInfoColumns,
		prototype:    &carTrackInfo{},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("carId", "t.car_id"), eqCond("carNo", "t.car_no"),
			eqCond("longitude", "t.longitude"), eqCond("latitude", "t.latitude"),
			eqCond("deviceType", "t.device_type"), eqCond("deviceNo", "t.device_no"),
			eqCond("laneNo", "t.lane_no"), nullCond("snapTime", "t.snap_time"),
			nullCond("receiveTime", "t.receive_time"), eqCond("snapPic", "t.snap_pic"),
			eqCond("roadSectionId", "t.road_section_id"), likeCond("roadSectionName", "t.road_section_name"),
			eqCond("backCol1", "t.back_col1"), eqCond("backCol2", "t.back_col2"),
			eqCond("status", "t.status"), nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
			nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
			dateTimeGe("applyTime1", "create_time"), dateTimeLe("applyTime2", "create_time"),
		},
	}

	// car_aduit_free
	aduitFreeSpec = &tableSpec{
		table:        carAduitFreeTable,
		selectSQL:    carAduitFreeSelectColumns,
		fromSQL:      "car_aduit_free t left join sys_dept d on d.dept_id = t.org_id and d.del_flag = '0'",
		selectSuffix: ",d.dept_name AS org_name",
		detailSuffix: ",d.dept_name AS org_name",
		orderBy:      "t.create_time,t.id",
		columns:      carAduitFreeColumns,
		prototype:    &carAduitFree{},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("confirmId", "t.confirm_id"), eqCond("carId", "t.car_id"),
			likeCond("carNo", "t.car_no"), eqCond("carType", "t.car_type"),
			eqCond("carVehicle", "t.car_vehicle"), eqCond("orgId", "t.org_id"),
			tmplCond("orgName", "d.dept_name LIKE CONCAT('%', ?, '%')"),
			eqCond("userIds", "t.user_ids"), eqCond("userNames", "t.user_names"),
			nullCond("amount", "t.amount"), eqCond("backCol1", "t.back_col1"),
			eqCond("backCol2", "t.back_col2"), eqCond("status", "t.status"),
			nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
			nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
		},
	}

	// car_confim_free
	confimFreeSpec = &tableSpec{
		table:     carConfimFreeTable,
		selectSQL: carConfimFreeSelectColumns,
		fromSQL:   "car_confim_free t left join sys_dept sd on sd.dept_id = t.org_id",
		orderBy:   "t.create_time desc,t.id",
		columns:   carConfimFreeColumns,
		prototype: &carConfimFree{},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("carId", "t.car_id"), eqCond("carNo", "t.car_no"),
			eqCond("carType", "t.car_type"), eqCond("carVehicle", "t.car_vehicle"),
			likeCond("linkName", "t.link_name"), eqCond("linkPhone", "t.link_phone"),
			eqCond("orgId", "t.org_id"),
			tmplCond("orgName", "sd.dept_name LIKE CONCAT('%', ?, '%')"),
			eqCond("userIds", "t.user_ids"), eqCond("userNames", "t.user_names"),
			nullCond("amount", "t.amount"), eqCond("escapedTypes", "t.escaped_types"),
			eqCond("backCol1", "t.back_col1"), eqCond("backCol2", "t.back_col2"),
			eqCond("status", "t.status"), nullCond("sort", "t.sort"), nullCond("epsId", "t.eps_id"),
			nullCond("tenantId", "t.tenant_id"), nullCond("createBy", "t.create_by"),
			inSetCond("exceptIds"), likeCond("carNoQuery", "t.car_no"),
			dateTimeGe("applyTime1", "create_time"), dateTimeLe("applyTime2", "create_time"),
			dateGe("applyTime3", "create_time"), dateLtNextDay("applyTime4", "create_time"),
		},
	}
)

// init 在包初始化后挂上依赖 spec 自身的缓存刷新钩子（避免 var 初始化环）。
func init() {
	whiteInfoSpec.afterChange = func(h *handler, c *gin.Context) { _ = h.refreshWhiteList(c) }
	warningRuleSpec.afterChange = func(h *handler, c *gin.Context) { _ = h.cacheWarningRule(c) }
	// JAVA 对照: CarExceptRecord.supplementaryStatus = "0"（字段初始化值，select 未取该列）
	exceptRecordSpec.afterScan = normalizeExceptRecords
	exceptRecordSpecNew.afterScan = normalizeExceptRecords
}
