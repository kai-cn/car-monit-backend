// JAVA 对照: ruoyi-system/src/main/resources/mapper/base/*.xml 的 selectXxxList / selectXxxVo
// 类/职责: base 各表的声明式规格（投影、条件、排序、主键、删除方式）
// 对应 Go 文件: internal/modules/base/specs.go
//
// DIFF: XML 的 <if> 顺序被照抄成 conditions 顺序；数值/日期字段的判据是「只判 null」，
// 用 numCond 表达；等值/模糊用 eqCond / likeCond。
package base

var (
	// ods_szdn_section —— order by t.road_code,t.section_code
	sectionSpec = &tableSpec{
		table: "ods_szdn_section",
		selectSQL: `t.id, t.road_code, t.road_name, t.section_code, t.section_name,
			t.start_pile_no, t.end_pile_no, t.org_code, t.org_name, t.org_level_code,
			t.org_category, t.mileage, t.open_date`,
		orderBy:   "t.road_code,t.section_code",
		pk:        "id",
		prototype: &odsSzdnSection{},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("roadCode", "t.road_code"),
			likeCond("roadName", "t.road_name"), eqCond("sectionCode", "t.section_code"),
			likeCond("sectionName", "t.section_name"), numCond("startPileNo", "t.start_pile_no"),
			numCond("endPileNo", "t.end_pile_no"), eqCond("orgCode", "t.org_code"),
			likeCond("orgName", "t.org_name"), eqCond("orgLevelCode", "t.org_level_code"),
			eqCond("orgCategory", "t.org_category"), numCond("mileage", "t.mileage"),
			numCond("openDate", "t.open_date"),
		},
	}

	// ods_szdn_toll —— order by t.toll_name；sectionName 条件映射到 section_code like
	tollSpec = &tableSpec{
		table: "ods_szdn_toll",
		selectSQL: `t.id, t.road_code, t.id_card, t.toll_code, t.toll_name, t.pile_no,
			t.org_name, t.hex_code, t.state_code, t.org_code, t.longitude, t.latitude,
			t.open_date, t.toll_alias_name, t.in_monitor_resource, t.lane_monitor_resource,
			t.square_monitor_resource, t.dynamic_monitor_resource, t.toll_code_merge,
			t.state_code_merge, t.toll_name_merge, t.section_code, t.toll_org_code, t.is_access`,
		orderBy:   "t.toll_name",
		pk:        "id",
		prototype: &odsSzdnToll{},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("roadCode", "t.road_code"), eqCond("idCard", "t.id_card"),
			eqCond("tollCode", "t.toll_code"), likeCond("tollName", "t.toll_name"),
			eqCond("pileNo", "t.pile_no"), likeCond("orgName", "t.org_name"),
			eqCond("hexCode", "t.hex_code"), eqCond("stateCode", "t.state_code"),
			eqCond("orgCode", "t.org_code"), eqCond("longitude", "t.longitude"),
			eqCond("latitude", "t.latitude"), numCond("openDate", "t.open_date"),
			likeCond("tollAliasName", "t.toll_alias_name"),
			eqCond("inMonitorResource", "t.in_monitor_resource"),
			eqCond("laneMonitorResource", "t.lane_monitor_resource"),
			eqCond("squareMonitorResource", "t.square_monitor_resource"),
			eqCond("dynamicMonitorResource", "t.dynamic_monitor_resource"),
			eqCond("tollCodeMerge", "t.toll_code_merge"),
			eqCond("stateCodeMerge", "t.state_code_merge"),
			likeCond("tollNameMerge", "t.toll_name_merge"),
			eqCond("sectionCode", "t.section_code"), eqCond("tollOrgCode", "t.toll_org_code"),
			eqCond("isAccess", "t.is_access"), likeCond("sectionName", "t.section_code"),
		},
	}

	// ods_szdn_gantry —— order by t.gantry_name
	gantrySpec = &tableSpec{
		table: "ods_szdn_gantry",
		selectSQL: `t.id, t.gantry_code, t.gantry_name, t.road_code, t.section_code,
			t.toll_code, t.org_code, t.hex_code, t.direction, t.pile_no, t.lon, t.lat,
			t.remark, t.is_virtual, t.mileage, t.boundary_gantry_type, t.gantry_type,
			t.city_code, t.district_name, t.belong_group, t.gantry_code_merge,
			t.gantry_name_alias`,
		orderBy:   "t.gantry_name",
		pk:        "id",
		prototype: &odsSzdnGantry{},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("gantryCode", "t.gantry_code"),
			likeCond("gantryName", "t.gantry_name"), eqCond("roadCode", "t.road_code"),
			eqCond("sectionCode", "t.section_code"), eqCond("tollCode", "t.toll_code"),
			eqCond("orgCode", "t.org_code"), eqCond("hexCode", "t.hex_code"),
			eqCond("direction", "t.direction"), likeCond("pileNo", "t.pile_no"),
			eqCond("lon", "t.lon"), eqCond("lat", "t.lat"),
			eqCond("isVirtual", "t.is_virtual"), eqCond("mileage", "t.mileage"),
			eqCond("boundaryGantryType", "t.boundary_gantry_type"),
			eqCond("gantryType", "t.gantry_type"), eqCond("cityCode", "t.city_code"),
			likeCond("districtName", "t.district_name"), eqCond("belongGroup", "t.belong_group"),
			eqCond("gantryCodeMerge", "t.gantry_code_merge"),
			eqCond("gantryNameAlias", "t.gantry_name_alias"),
			likeCond("sectionName", "t.section_code"),
		},
	}

	// ods_yhgl_v_base_org —— order by t.big_id，投影带 parentId 相关子查询
	orgSpec = &tableSpec{
		table: "ods_yhgl_v_base_org",
		selectSQL: `t.big_id, t.org_code, t.org_name, t.org_short_name, t.org_parent_id,
			t.org_level_code, t.org_is_virtual, t.org_maintenance, t.org_sequence,
			t.org_is_manager, t.org_is_deleted, t.org_category, t.org_is_authorized,
			t.org_address, t.org_is_yh_autarky, t.load_time, t.grade_level,
			(select t1.big_id from ods_yhgl_v_base_org t1 where t1.org_code = t.org_parent_id) parentId`,
		orderBy:   "t.big_id",
		pk:        "big_id",
		prototype: &odsYhglVBaseOrg{},
		// parentId 是相关子查询列（Java @TableField(exist = false)），不参与写入。
		readOnly: map[string]bool{"parentId": true},
		conditions: []cond{
			eqCond("bigId", "t.big_id"), eqCond("orgCode", "t.org_code"),
			likeCond("orgName", "t.org_name"), likeCond("orgShortName", "t.org_short_name"),
			eqCond("orgParentId", "t.org_parent_id"), eqCond("orgLevelCode", "t.org_level_code"),
			eqCond("orgIsVirtual", "t.org_is_virtual"), eqCond("orgMaintenance", "t.org_maintenance"),
			numCond("orgSequence", "t.org_sequence"), eqCond("orgIsManager", "t.org_is_manager"),
			eqCond("orgIsDeleted", "t.org_is_deleted"), numCond("orgCategory", "t.org_category"),
			eqCond("orgIsAuthorized", "t.org_is_authorized"), eqCond("orgAddress", "t.org_address"),
			eqCond("orgIsYhAutarky", "t.org_is_yh_autarky"),
			numCond("loadTime", "t.load_time"), numCond("gradeLevel", "t.grade_level"),
		},
	}

	// geometry —— order by lxbh,t.qdzh；主键 Integer，新增/修改按 id 是否为 null 判定
	geometrySpec = &tableSpec{
		table:     "geometry",
		selectSQL: "t.id, t.lxbh, t.lxfx, t.qdzh, t.zdzh, t.paths",
		orderBy:   "lxbh,t.qdzh",
		pk:        "id",
		pkKind:    pkInteger,
		prototype: &geometry{},
		conditions: []cond{
			zeroSkipCond("id", "t.id"), eqCond("lxbh", "t.lxbh"), eqCond("lxfx", "t.lxfx"),
			numCond("qdzh", "t.qdzh"), numCond("zdzh", "t.zdzh"), eqCond("paths", "t.paths"),
		},
	}

	// zdata_location_dict —— 无 order by（PageHelper 追加客户端排序）
	locationSpec = &tableSpec{
		table: "zdata_location_dict",
		selectSQL: `t.id, t.type, t.name, t.raw_code, t.standard_code, t.roadcode,
			t.roadname, t.sectioncode, t.sectionname, t.tollcode, t.tollname, t.orgcode,
			t.orgname, t.created_at, t.updated_at`,
		pk:        "id",
		prototype: &zdataLocationDict{},
		conditions: []cond{
			zeroSkipCond("id", "t.id"), eqCond("type", "t.type"), likeCond("name", "t.name"),
			eqCond("rawCode", "t.raw_code"), eqCond("standardCode", "t.standard_code"),
			eqCond("roadcode", "t.roadcode"), likeCond("roadname", "t.roadname"),
			eqCond("sectioncode", "t.sectioncode"), likeCond("sectionname", "t.sectionname"),
			eqCond("tollcode", "t.tollcode"), likeCond("tollname", "t.tollname"),
			eqCond("orgcode", "t.orgcode"), likeCond("orgname", "t.orgname"),
			numCond("createdAt", "t.created_at"), numCond("updatedAt", "t.updated_at"),
		},
	}

	// zdata_trail_fitting —— 唯一带 "WHERE t.del_flag = '0'" 前缀的列表语句
	fittingSpec = &tableSpec{
		// DIFF: Java 的 ZdataTrailFittingMapper 在 <if test="id != null"> 里引用了实体不存在的 id 属性，
		// MyBatis 抛 ReflectionException（该接口在 Java 侧恒 500）；Go 侧正常返回列表。
		table: "zdata_trail_fitting",
		selectSQL: `t.cid, t.enaxlecount, t.entime, t.entolllaneid, t.entollstationid,
			t.entollstationname, t.envehicleclass, t.envehicleid, t.envehicletype, t.enweight,
			t.extime, t.extolllaneid, t.extollstationid, t.extollstationname, t.exvehicleclass,
			t.exvehicleid, t.exvehicletype, t.exweight, t.trailpoints`,
		// DIFF: Java XML 写的是 "WHERE t.del_flag = '0'"，但目标库 zdata_trail_fitting
		// 没有 del_flag 列（Java 侧 500）；Python 参考实现按模板用 "where 1 = 1"，
		// 这里与参考实现一致，保证列表可用。
		wherePrefix: "WHERE 1=1",
		pk:          "cid",
		detailPK:    "cid",
		prototype:   &zdataTrailFitting{},
		conditions: []cond{
			// JAVA 对照: XML 里确实写了 t.id = #{id}，而实体没有 id 字段（照抄）。
			eqCond("id", "t.id"), numCond("enaxlecount", "t.enaxlecount"),
			numCond("entime", "t.entime"), eqCond("entolllaneid", "t.entolllaneid"),
			eqCond("entollstationid", "t.entollstationid"),
			likeCond("entollstationname", "t.entollstationname"),
			numCond("envehicleclass", "t.envehicleclass"), eqCond("envehicleid", "t.envehicleid"),
			numCond("envehicletype", "t.envehicletype"), numCond("enweight", "t.enweight"),
			numCond("extime", "t.extime"), eqCond("extolllaneid", "t.extolllaneid"),
			eqCond("extollstationid", "t.extollstationid"),
			likeCond("extollstationname", "t.extollstationname"),
			numCond("exvehicleclass", "t.exvehicleclass"), eqCond("exvehicleid", "t.exvehicleid"),
			numCond("exvehicletype", "t.exvehicletype"), numCond("exweight", "t.exweight"),
			eqCond("trailpoints", "t.trailpoints"),
		},
	}

	// zdata_trail_tracks —— order by t.enter_time desc
	trailTracksSpec = &tableSpec{
		table: "zdata_trail_tracks",
		selectSQL: `t.uuid, t.type, t.point_count, t.plate_key, t.enter_time, t.exit_time,
			t.trail_points, t.create_time, t.enter_locationcode, t.exit_locationcode,
			t.track_josn, t.enaxlecount, t.entolllaneid, t.entollstationid, t.entollstationname,
			t.envehicleclass, t.envehicleid, t.envehicletype, t.enweight, t.extolllaneid,
			t.extollstationid, t.extollstationname, t.exvehicleclass, t.exvehicleid,
			t.exvehicletype, t.exweight, t.start_lon, t.strat_lat, t.end_lon, t.end_lat`,
		orderBy:   "t.enter_time desc",
		pk:        "uuid",
		prototype: &zdataTrailTracks{},
		conditions: []cond{
			eqCond("uuid", "t.uuid"), numCond("type", "t.type"), numCond("pointCount", "t.point_count"),
			eqCond("plateKey", "t.plate_key"), numCond("enterTime", "t.enter_time"),
			numCond("exitTime", "t.exit_time"), eqCond("trailPoints", "t.trail_points"),
			tmplCond("carNo", "t.plate_key = {p}"),
			dateGe("applyTime1", "enter_time"), dateLtNextDay("applyTime2", "enter_time"),
		},
	}

	// ods_cxzt_fwqclls —— 无 order by
	fwqCllsSpec = &tableSpec{
		table: "ods_cxzt_fwqclls",
		selectSQL: `t.big_id, t.datauuid, t.targetpicurl, t.vehiclebrand, t.platepicurl,
			t.rollvehiclestype, t.plateno, t.directionname, t.platetype, t.dangmark,
			t.crosstime, t.axles, t.devicename, t.ipaddress, t.servicename, t.vehicletype,
			t.load_time, t.grade_level`,
		pk:        "big_id",
		prototype: &odsCxztFwqclls{},
		conditions: []cond{
			numCond("bigId", "t.big_id"), eqCond("datauuid", "t.datauuid"),
			eqCond("targetpicurl", "t.targetpicurl"), eqCond("vehiclebrand", "t.vehiclebrand"),
			eqCond("platepicurl", "t.platepicurl"), eqCond("rollvehiclestype", "t.rollvehiclestype"),
			eqCond("plateno", "t.plateno"), likeCond("directionname", "t.directionname"),
			eqCond("platetype", "t.platetype"), eqCond("dangmark", "t.dangmark"),
			numCond("crosstime", "t.crosstime"), eqCond("axles", "t.axles"),
			likeCond("devicename", "t.devicename"), eqCond("ipaddress", "t.ipaddress"),
			likeCond("servicename", "t.servicename"), eqCond("vehicletype", "t.vehicletype"),
			eqCond("loadTime", "t.load_time"), eqCond("gradeLevel", "t.grade_level"),
		},
	}

	// ods_szdn_gantry_ip —— order by t.id
	gantryIPSpec = &tableSpec{
		table:     "ods_szdn_gantry_ip",
		selectSQL: "t.id, t.gantry_code, t.gantry_name, t.org_code, t.ip, t.brand, t.type",
		orderBy:   "t.id",
		pk:        "id",
		prototype: &odsSzdnGantryIp{},
		conditions: []cond{
			zeroSkipCond("id", "t.id"), eqCond("gantryCode", "t.gantry_code"),
			likeCond("gantryName", "t.gantry_name"), eqCond("orgCode", "t.org_code"),
			eqCond("ip", "t.ip"), eqCond("brand", "t.brand"), eqCond("type", "t.type"),
		},
	}

	// ods_szdn_toll_station_ip
	// DIFF: Java XML 写的是 order by t.big_id，但该表实际主键列是 id（resultMap 也把 id 映射成 id）。
	// 照抄会让接口稳定 500（Unknown column），这里改为 t.id，排序语义等价且可用。
	tollStationIPSpec = &tableSpec{
		table:     "ods_szdn_toll_station_ip",
		selectSQL: "t.id, t.toll_code, t.toll_name, t.org_code, t.ip, t.brand",
		orderBy:   "t.id",
		pk:        "id",
		prototype: &odsSzdnTollStationIp{},
		conditions: []cond{
			eqCond("tollCode", "t.toll_code"), likeCond("tollName", "t.toll_name"),
			eqCond("orgCode", "t.org_code"), eqCond("ip", "t.ip"), eqCond("brand", "t.brand"),
		},
	}

	// ods_szdn_province_border_vehicle_weight_newstructure —— 无 order by；详情按 dataSource
	vehicleWeightSpec = &tableSpec{
		table: "ods_szdn_province_border_vehicle_weight_newstructure",
		selectSQL: `t.dataSource, t.dataType, t.plateNo, t.siteId, t.location, t.driveNo,
			t.plateColor, t.plateColorCode, t.plateType, t.plateTypeCode, t.vehicleColor,
			t.vehicleColorCode, t.vehicleType, t.vehicleTypeCode, t.vehicleSpeed, t.isOverweight,
			t.axleNum, t.overWeight, t.vehicleWeight, t.limitWeight, t.checkTimeUnix, t.checkTime,
			t.axleModel, t.loadRate, t.axleArray, t.weighingImagesArry, t.load_time,
			t.grade_level, t.datauuid, t.reserve1, t.reserve2, t.reserve3`,
		pk:        "datauuid",
		detailPK:  "dataSource",
		prototype: &odsSzdnProvinceBorderVehicleWeightNewstructure{},
		conditions: []cond{
			eqCond("dataSource", "t.dataSource"), eqCond("dataType", "t.dataType"),
			eqCond("plateNo", "t.plateNo"), eqCond("siteId", "t.siteId"),
			eqCond("location", "t.location"), numCond("driveNo", "t.driveNo"),
			eqCond("plateColor", "t.plateColor"), eqCond("plateColorCode", "t.plateColorCode"),
			eqCond("plateType", "t.plateType"), eqCond("plateTypeCode", "t.plateTypeCode"),
			eqCond("vehicleColor", "t.vehicleColor"), eqCond("vehicleColorCode", "t.vehicleColorCode"),
			eqCond("vehicleType", "t.vehicleType"), eqCond("vehicleTypeCode", "t.vehicleTypeCode"),
			numCond("vehicleSpeed", "t.vehicleSpeed"), numCond("isOverweight", "t.isOverweight"),
			numCond("axleNum", "t.axleNum"), numCond("overWeight", "t.overWeight"),
			numCond("vehicleWeight", "t.vehicleWeight"), numCond("limitWeight", "t.limitWeight"),
			numCond("checkTimeUnix", "t.checkTimeUnix"), numCond("checkTime", "t.checkTime"),
			numCond("axleModel", "t.axleModel"), numCond("loadRate", "t.loadRate"),
			eqCond("axleArray", "t.axleArray"), eqCond("weighingImagesArry", "t.weighingImagesArry"),
			numCond("loadTime", "t.load_time"), numCond("gradeLevel", "t.grade_level"),
			eqCond("datauuid", "t.datauuid"), eqCond("reserve1", "t.reserve1"),
			eqCond("reserve2", "t.reserve2"), eqCond("reserve3", "t.reserve3"),
		},
	}

	// base_config_service_area —— 无 order by、物理删除。
	// DIFF: XML 用 <where>（无条件时不输出 WHERE），这里统一 "WHERE 1=1"，结果集相同。
	serviceAreaSpec = &tableSpec{
		table:          "base_config_service_area",
		selectSQL:      "t.fwqbm, t.fwqmc, t.lon, t.lat, t.road_code, t.section_code, t.pile_no",
		wherePrefix:    "WHERE 1=1",
		pk:             "fwqbm",
		physicalDelete: true,
		prototype:      &baseConfigServiceArea{},
		// DIFF: Java 的实体继承 BasePlusEntity（id/eps_id/del_flag/create_by/...），
		// 但目标库的 base_config_service_area 只有 7 个业务列 —— 这里不做审计列填充、
		// 不生成雪花 id，写入时排除这些字段（Java 的 insert 会因 Unknown column 失败）。
		audit: false,
		readOnly: map[string]bool{
			"id": true, "epsId": true, "delFlag": true, "createBy": true, "createTime": true,
			"updateBy": true, "updateTime": true, "sort": true, "tenantId": true,
		},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("fwqbm", "t.fwqbm"), eqCond("fwqmc", "t.fwqmc"),
			eqCond("lon", "t.lon"), eqCond("lat", "t.lat"), eqCond("roadCode", "t.road_code"),
			eqCond("sectionCode", "t.section_code"), eqCond("pileNo", "t.pile_no"),
			numCond("createBy", "t.create_by"),
		},
	}

	// car_warning_config —— join base_config_service_area；无 order by；物理删除。
	// DIFF: XML 用 <where>，这里统一 "WHERE 1=1"，结果集相同。
	carWarningConfigSpec = &tableSpec{
		table: "car_warning_config",
		selectSQL: `t.id, t.gantry_code_in, t.gantry_name_in, t.gantry_code_out,
			t.gantry_name_out, t.time_span, t.remark, t.fwqbm, t1.fwqmc, t1.lon, t1.lat,
			t1.road_code, t1.section_code, t1.pile_no`,
		fromSQL:        "car_warning_config t join base_config_service_area t1 on t.fwqbm = t1.fwqbm",
		wherePrefix:    "WHERE 1=1",
		pk:             "id",
		assignUUID:     true,
		physicalDelete: true,
		prototype:      &carWarningConfig{},
		readOnly: map[string]bool{
			"fwqmc": true, "lon": true, "lat": true, "roadCode": true,
			"sectionCode": true, "pileNo": true,
		},
		conditions: []cond{
			eqCond("id", "t.id"), eqCond("gantryCodeIn", "t.gantry_code_in"),
			likeCond("gantryNameIn", "t.gantry_name_in"),
			eqCond("gantryCodeOut", "t.gantry_code_out"),
			likeCond("gantryNameOut", "t.gantry_name_out"), numCond("timeSpan", "t.time_span"),
			eqCond("fwqbm", "t.fwqbm"),
			tmplCond("fwqmc", "t1.fwqmc LIKE CONCAT('%', {p}, '%')"),
			// JAVA 对照: 这 5 条指向 t.lon / t.lat / t.road_code / t.section_code / t.pile_no，
			// 但这 5 列在 t1 上 —— 一旦传参 MySQL 报 Unknown column（Java 侧 500，照抄）。
			eqCond("lon", "t.lon"), eqCond("lat", "t.lat"),
			eqCond("roadCode", "t.road_code"), eqCond("sectionCode", "t.section_code"),
			eqCond("pileNo", "t.pile_no"),
		},
	}

	// ods_lwzxsfsj_fee_station_enter_01 —— order by t.big_id
	feeStationEnterSpec = &tableSpec{
		table: "ods_lwzxsfsj_fee_station_enter_01",
		selectSQL: `t.big_id, t.cardid, t.electricalpercentage, t.enaxlecount, t.entime,
			t.entolllanehex, t.entolllaneid, t.entollstationid, t.enweight, t.identifyvehicleid,
			t.lanetype, t.mediatype, t.operid, t.operationmedia, t.params, t.passid,
			t.receivetime, t.shift, t.signstatus, t.specialtype, t.tac, t.terminalno,
			t.terminaltransno, t.transfee, t.transtype, t.vcount, t.vehicleclass, t.vehicleid,
			t.vehiclesign, t.vehiclesignid, t.vehicletype, t.load_time, t.grade_level, t.cid`,
		orderBy:   "t.big_id",
		pk:        "big_id",
		prototype: &odsLwzxsfsjFeeStationEnter01{},
		conditions: []cond{
			numCond("bigId", "t.big_id"), eqCond("cardid", "t.cardid"),
			numCond("electricalpercentage", "t.electricalpercentage"),
			numCond("enaxlecount", "t.enaxlecount"), numCond("entime", "t.entime"),
			eqCond("entolllanehex", "t.entolllanehex"), eqCond("entolllaneid", "t.entolllaneid"),
			eqCond("entollstationid", "t.entollstationid"), numCond("enweight", "t.enweight"),
			eqCond("identifyvehicleid", "t.identifyvehicleid"), eqCond("lanetype", "t.lanetype"),
			eqCond("mediatype", "t.mediatype"), eqCond("operid", "t.operid"),
			eqCond("operationmedia", "t.operationmedia"), eqCond("params", "t.params"),
			eqCond("passid", "t.passid"), numCond("receivetime", "t.receivetime"),
			eqCond("shift", "t.shift"), eqCond("signstatus", "t.signstatus"),
			eqCond("specialtype", "t.specialtype"), eqCond("tac", "t.tac"),
			eqCond("terminalno", "t.terminalno"), eqCond("terminaltransno", "t.terminaltransno"),
			numCond("transfee", "t.transfee"), eqCond("transtype", "t.transtype"),
			numCond("vcount", "t.vcount"), eqCond("vehicleclass", "t.vehicleclass"),
			eqCond("vehicleid", "t.vehicleid"), eqCond("vehiclesign", "t.vehiclesign"),
			eqCond("vehiclesignid", "t.vehiclesignid"), eqCond("vehicletype", "t.vehicletype"),
			numCond("loadTime", "t.load_time"), eqCond("gradeLevel", "t.grade_level"),
		},
	}

	// ods_rt_szdn_snapshot_flow_provcapture_addcode —— order by t.big_id
	provCaptureSpec = &tableSpec{
		table: "ods_rt_szdn_snapshot_flow_provcapture_addcode",
		selectSQL: `t.big_id, t.deviceip, t.tailcapturetimeunix, t.tailcapturetime,
			t.extendattribute, t.smallsideimagewidth, t.axletype, t.smallsideimageheight,
			t.platecolorcode, t.platecolor, t.cover, t.averageauthoritative, t.headlanecode,
			t.specialvehicle, t.carlength, t.resulttype, t.carhight, t.carmodelscode,
			t.carmodels, t.laneposition, t.firstauthoritative, t.tailplateimageheight,
			t.axlecount, t.plateimagewidth, t.specialclass, t.tailplatenumber, t.tailimage,
			t.sidecapturetimeunix, t.sidecapturetime, t.sidelanecode, t.wheelbase, t.attached,
			t.wheelcount, t.guid, t.sideimagewidth, t.plateimageheight, t.datasource,
			t.carclass, t.gantryid, t.smallsideimage, t.headimageheight, t.sidescenetypecode,
			t.sidescenetype, t.tailimagewidth, t.envstate, t.headscenetypecode, t.headscenetype,
			t.sidedrivingdirectioncode, t.sidedrivingdirection, t.sideimageheight, t.speed,
			t.tailplateimage, t.headdrivingdirectioncode, t.headdrivingdirection, t.cartype,
			t.plateimage, t.changelane, t.sideimage, t.tailplateposition, t.headimagewidth,
			t.headimage, t.carweight, t.tailimageheight, t.devicecode, t.platenumber,
			t.tailplatecolorcode, t.tailplatecolor, t.uploadtimeunix, t.uploadtime,
			t.impostoraxlecount, t.taillanecode, t.siteid, t.headcapturetimeunix,
			t.headcapturetime, t.plateposition, t.tailplateimagewidth, t.loadtime, t.gradelevel,
			t.datauuid, t.reserve1, t.reserve2, t.reserve3`,
		orderBy:   "t.big_id",
		pk:        "big_id",
		prototype: &odsRtSzdnSnapshotFlowProvcaptureAddcode{},
		conditions: []cond{
			numCond("bigId", "t.big_id"), eqCond("deviceip", "t.deviceip"),
			numCond("tailcapturetimeunix", "t.tailcapturetimeunix"),
			numCond("tailcapturetime", "t.tailcapturetime"),
			eqCond("extendattribute", "t.extendattribute"),
			numCond("smallsideimagewidth", "t.smallsideimagewidth"),
			eqCond("axletype", "t.axletype"),
			numCond("smallsideimageheight", "t.smallsideimageheight"),
			numCond("platecolorcode", "t.platecolorcode"), eqCond("platecolor", "t.platecolor"),
			eqCond("cover", "t.cover"), numCond("averageauthoritative", "t.averageauthoritative"),
			numCond("headlanecode", "t.headlanecode"), numCond("specialvehicle", "t.specialvehicle"),
			numCond("carlength", "t.carlength"), eqCond("resulttype", "t.resulttype"),
			numCond("carhight", "t.carhight"), numCond("carmodelscode", "t.carmodelscode"),
			eqCond("carmodels", "t.carmodels"), eqCond("laneposition", "t.laneposition"),
			numCond("firstauthoritative", "t.firstauthoritative"),
			numCond("tailplateimageheight", "t.tailplateimageheight"),
			numCond("axlecount", "t.axlecount"), numCond("plateimagewidth", "t.plateimagewidth"),
			eqCond("specialclass", "t.specialclass"), eqCond("tailplatenumber", "t.tailplatenumber"),
			eqCond("tailimage", "t.tailimage"), numCond("sidecapturetimeunix", "t.sidecapturetimeunix"),
			numCond("sidecapturetime", "t.sidecapturetime"), numCond("sidelanecode", "t.sidelanecode"),
			numCond("wheelbase", "t.wheelbase"), eqCond("attached", "t.attached"),
			numCond("wheelcount", "t.wheelcount"), eqCond("guid", "t.guid"),
			numCond("sideimagewidth", "t.sideimagewidth"), numCond("plateimageheight", "t.plateimageheight"),
			eqCond("datasource", "t.datasource"), eqCond("carclass", "t.carclass"),
			eqCond("gantryid", "t.gantryid"), eqCond("smallsideimage", "t.smallsideimage"),
			numCond("headimageheight", "t.headimageheight"),
			numCond("sidescenetypecode", "t.sidescenetypecode"),
			eqCond("sidescenetype", "t.sidescenetype"), numCond("tailimagewidth", "t.tailimagewidth"),
			eqCond("envstate", "t.envstate"), numCond("headscenetypecode", "t.headscenetypecode"),
			eqCond("headscenetype", "t.headscenetype"),
			numCond("sidedrivingdirectioncode", "t.sidedrivingdirectioncode"),
			eqCond("sidedrivingdirection", "t.sidedrivingdirection"),
			numCond("sideimageheight", "t.sideimageheight"), eqCond("speed", "t.speed"),
			eqCond("tailplateimage", "t.tailplateimage"),
			numCond("headdrivingdirectioncode", "t.headdrivingdirectioncode"),
			eqCond("headdrivingdirection", "t.headdrivingdirection"),
			eqCond("cartype", "t.cartype"), eqCond("plateimage", "t.plateimage"),
			eqCond("changelane", "t.changelane"), eqCond("sideimage", "t.sideimage"),
			eqCond("tailplateposition", "t.tailplateposition"),
			numCond("headimagewidth", "t.headimagewidth"), eqCond("headimage", "t.headimage"),
			numCond("carweight", "t.carweight"), numCond("tailimageheight", "t.tailimageheight"),
			eqCond("devicecode", "t.devicecode"), eqCond("platenumber", "t.platenumber"),
			numCond("tailplatecolorcode", "t.tailplatecolorcode"),
			eqCond("tailplatecolor", "t.tailplatecolor"),
			numCond("uploadtimeunix", "t.uploadtimeunix"), numCond("uploadtime", "t.uploadtime"),
			numCond("impostoraxlecount", "t.impostoraxlecount"),
			numCond("taillanecode", "t.taillanecode"), numCond("siteid", "t.siteid"),
			numCond("headcapturetimeunix", "t.headcapturetimeunix"),
			numCond("headcapturetime", "t.headcapturetime"),
			eqCond("plateposition", "t.plateposition"),
			numCond("tailplateimagewidth", "t.tailplateimagewidth"),
			numCond("loadtime", "t.loadtime"), numCond("gradelevel", "t.gradelevel"),
			eqCond("datauuid", "t.datauuid"), eqCond("reserve1", "t.reserve1"),
			eqCond("reserve2", "t.reserve2"), eqCond("reserve3", "t.reserve3"),
		},
	}

	// ods_rt_szdn_snapshot_flow_stationcapture_addcode —— order by t.big_id
	stationCaptureSpec = &tableSpec{
		table: "ods_rt_szdn_snapshot_flow_stationcapture_addcode",
		selectSQL: `t.big_id, t.datasource, t.cameratype, t.deviceid, t.deviceip, t.tollcode,
			t.tollname, t.orgcode, t.siteid, t.laneid, t.snapshottimeunix, t.snapshottime,
			t.receivedtimeunix, t.receivedtime, t.platenumber, t.platecolorcode, t.platecolor,
			t.platetypecode, t.platetype, t.plateconfidence, t.carbrand, t.carcolorcode,
			t.carcolor, t.cartypecode, t.cartype, t.cardirectioncode, t.cardirection,
			t.snappicturepath, t.loadtime, t.gradelevel, t.datauuid, t.maindirection,
			t.maindirectionname, t.reserve3`,
		orderBy:   "t.big_id",
		pk:        "big_id",
		prototype: &odsRtSzdnSnapshotFlowStationcaptureAddcode{},
		conditions: []cond{
			numCond("bigId", "t.big_id"), eqCond("datasource", "t.datasource"),
			eqCond("cameratype", "t.cameratype"), eqCond("deviceid", "t.deviceid"),
			eqCond("deviceip", "t.deviceip"), eqCond("tollcode", "t.tollcode"),
			likeCond("tollname", "t.tollname"), numCond("orgcode", "t.orgcode"),
			numCond("siteid", "t.siteid"), numCond("laneid", "t.laneid"),
			numCond("snapshottimeunix", "t.snapshottimeunix"),
			numCond("snapshottime", "t.snapshottime"),
			numCond("receivedtimeunix", "t.receivedtimeunix"),
			numCond("receivedtime", "t.receivedtime"), eqCond("platenumber", "t.platenumber"),
			numCond("platecolorcode", "t.platecolorcode"), eqCond("platecolor", "t.platecolor"),
			numCond("platetypecode", "t.platetypecode"), eqCond("platetype", "t.platetype"),
			numCond("plateconfidence", "t.plateconfidence"), eqCond("carbrand", "t.carbrand"),
			numCond("carcolorcode", "t.carcolorcode"), eqCond("carcolor", "t.carcolor"),
			numCond("cartypecode", "t.cartypecode"), eqCond("cartype", "t.cartype"),
			numCond("cardirectioncode", "t.cardirectioncode"),
			eqCond("cardirection", "t.cardirection"), eqCond("snappicturepath", "t.snappicturepath"),
			numCond("loadtime", "t.loadtime"), numCond("gradelevel", "t.gradelevel"),
			eqCond("datauuid", "t.datauuid"), eqCond("maindirection", "t.maindirection"),
			likeCond("maindirectionname", "t.maindirectionname"), eqCond("reserve3", "t.reserve3"),
		},
	}

	// dwd_lczt_fwqjcxx —— order by t.fwqmc
	fwqjcxxSpec = &tableSpec{
		table: "dwd_lczt_fwqjcxx",
		selectSQL: `t.agent_pk, t.yxtzj, t.fwqbm, t.fwqmc, t.wd, t.fxmc, t.fxdm, t.jd,
			t.sslxbh, t.sslxmc, t.ssldbh, t.ssldmc, t.sczhkgs, t.sczhszgs, t.ssglzxbm,
			t.ssglzxmc, t.xzqhmc, t.yyrq, t.cws, t.sfszlkk, t.cdzs, t.sfcyfw, t.sftgzsfw,
			t.sftgqxfw, t.sftgcsfw, t.sftgjyfw, t.mj, t.sftgcshfw, t.xzqhdm, t.synx, t.lyxt,
			t.load_time, t.all_col_pk`,
		orderBy:   "t.fwqmc",
		pk:        "agent_pk",
		prototype: &dwdLcztFwqjcxx{},
		conditions: []cond{
			eqCond("agentPk", "t.agent_pk"), eqCond("yxtzj", "t.yxtzj"), eqCond("fwqbm", "t.fwqbm"),
			likeCond("fwqmc", "t.fwqmc"), eqCond("wd", "t.wd"), eqCond("fxmc", "t.fxmc"),
			eqCond("fxdm", "t.fxdm"), eqCond("jd", "t.jd"), eqCond("sslxbh", "t.sslxbh"),
			eqCond("sslxmc", "t.sslxmc"), eqCond("ssldbh", "t.ssldbh"),
			likeCond("ssldmc", "t.ssldmc"), eqCond("sczhkgs", "t.sczhkgs"),
			eqCond("sczhszgs", "t.sczhszgs"), eqCond("ssglzxbm", "t.ssglzxbm"),
			eqCond("ssglzxmc", "t.ssglzxmc"), eqCond("xzqhmc", "t.xzqhmc"),
			eqCond("yyrq", "t.yyrq"), eqCond("cws", "t.cws"), eqCond("sfszlkk", "t.sfszlkk"),
			eqCond("cdzs", "t.cdzs"), eqCond("sfcyfw", "t.sfcyfw"), eqCond("sftgzsfw", "t.sftgzsfw"),
			eqCond("sftgqxfw", "t.sftgqxfw"), eqCond("sftgcsfw", "t.sftgcsfw"),
			eqCond("sftgjyfw", "t.sftgjyfw"), eqCond("mj", "t.mj"), eqCond("sftgcshfw", "t.sftgcshfw"),
			eqCond("xzqhdm", "t.xzqhdm"), eqCond("synx", "t.synx"), eqCond("lyxt", "t.lyxt"),
			eqCond("loadTime", "t.load_time"), eqCond("allColPk", "t.all_col_pk"),
		},
	}

	// dwd_lczt_sfsjcxx —— 含 XML 原文的 "and and t.agent_pk = #{id}" 破损条件（照抄）
	sfsjcxxSpec = &tableSpec{
		table: "dwd_lczt_sfsjcxx",
		selectSQL: `t.agent_pk, t.yxtzj, t.sfsbm, t.sfsmc, t.jd, t.wd, t.sslxbh, t.sslxmc,
			t.ssldbh, t.ssldmc, t.sczh_k, t.sczh_n, t.ssglzxbm, t.ssglzxmc, t.lyxt,
			t.load_time, t.all_col_pk`,
		orderBy:   "t.agent_pk",
		pk:        "agent_pk",
		prototype: &dwdLcztSfsjcxx{},
		conditions: []cond{
			// JAVA 对照: XML 第 51 行附近写的是 "and and t.agent_pk = #{id}" —— 保留，
			// 一旦传 agentPk，MySQL 报语法错误（Java 侧同样是 500）。
			rawCond("agentPk", "and and t.agent_pk = ?"),
			eqCond("yxtzj", "t.yxtzj"), eqCond("sfsbm", "t.sfsbm"),
			likeCond("sfsmc", "t.sfsmc"), eqCond("jd", "t.jd"), eqCond("wd", "t.wd"),
			eqCond("sslxbh", "t.sslxbh"), eqCond("sslxmc", "t.sslxmc"),
			eqCond("ssldbh", "t.ssldbh"), likeCond("ssldmc", "t.ssldmc"),
			eqCond("sczhK", "t.sczh_k"), eqCond("sczhN", "t.sczh_n"),
			eqCond("ssglzxbm", "t.ssglzxbm"), eqCond("ssglzxmc", "t.ssglzxmc"),
			eqCond("lyxt", "t.lyxt"), eqCond("loadTime", "t.load_time"),
			eqCond("allColPk", "t.all_col_pk"),
		},
	}

	// dwd_lczt_sfzjcxx —— order by t.agent_pk
	sfzjcxxSpec = &tableSpec{
		table: "dwd_lczt_sfzjcxx",
		selectSQL: `t.agent_pk, t.yxtzj, t.sfzdm, t.sfzmc, t.jd, t.wd, t.sslxbh, t.sslxmc,
			t.ssldbh, t.ssldmc, t.sczh_k, t.sczh_n, t.ssglzxbm, t.ssglzxmc, t.lyxt,
			t.load_time, t.all_col_pk`,
		orderBy:   "t.agent_pk",
		pk:        "agent_pk",
		prototype: &dwdLcztSfzjcxx{},
		conditions: []cond{
			eqCond("agentPk", "t.agent_pk"), eqCond("yxtzj", "t.yxtzj"), eqCond("sfzdm", "t.sfzdm"),
			likeCond("sfzmc", "t.sfzmc"), eqCond("jd", "t.jd"), eqCond("wd", "t.wd"),
			eqCond("sslxbh", "t.sslxbh"), eqCond("sslxmc", "t.sslxmc"),
			eqCond("ssldbh", "t.ssldbh"), eqCond("ssldmc", "t.ssldmc"),
			eqCond("sczhK", "t.sczh_k"), eqCond("sczhN", "t.sczh_n"),
			eqCond("ssglzxbm", "t.ssglzxbm"), eqCond("ssglzxmc", "t.ssglzxmc"),
			eqCond("lyxt", "t.lyxt"), eqCond("loadTime", "t.load_time"),
			eqCond("allColPk", "t.all_col_pk"),
		},
	}
)

// init 在包初始化后挂上依赖 spec 自身的缓存刷新钩子（避免 var 初始化环）。
func init() {
	geometrySpec.afterChange = refreshGeometryCache
	carWarningConfigSpec.afterChange = refreshWarningConfigCache

}
