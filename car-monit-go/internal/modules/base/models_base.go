// JAVA 对照: com.ruoyi.base.domain.OdsSzdnSection / OdsSzdnToll / OdsSzdnGantry / OdsYhglVBaseOrg
// JAVA 对照: Geometry / ZdataLocationDict / ZdataTrailFitting / ZdataTrailTracks / OdsCxztFwqclls
// JAVA 对照: OdsSzdnGantryIp / OdsSzdnTollStationIp
// 类/职责: 路段、收费站、门架、机构、几何、轨迹等基础表实体
// 对应 Go 文件: internal/modules/base/models_base.go
//
// DIFF: Java 的实体由 MyBatis-Plus 按驼峰-下划线映射；Go 用 gorm column 标签显式声明。
// DIFF: Java 的 Long/BigDecimal/Date 可为 null（前端能拿到 null）；Go 用指针保留“null / 缺省”语义。
// DIFF: Java 的 String 也可为 null，这里用零值 "" 近似（与 manager 包约定一致）。
// 瞬态字段（@TableField(exist = false)）只留 json 标签、不带 gorm column，拼写写入列时会被忽略。
package base

import (
	"car-monit-go/internal/web"
)

// entityBase 对应 BasePlusEntity（仅 base_config_service_area 使用）。
type entityBase struct {
	ID         *string       `json:"id" form:"id" gorm:"column:id"`
	EpsID      *int64        `json:"epsId" form:"epsId" gorm:"column:eps_id"`
	DelFlag    *string       `json:"delFlag" form:"delFlag" gorm:"column:del_flag"`
	CreateBy   *int64        `json:"createBy" form:"createBy" gorm:"column:create_by"`
	CreateTime *web.DateTime `json:"createTime" gorm:"column:create_time"`
	UpdateBy   *int64        `json:"updateBy" form:"updateBy" gorm:"column:update_by"`
	UpdateTime *web.DateTime `json:"updateTime" gorm:"column:update_time"`
	Sort       *int          `json:"sort" form:"sort" gorm:"column:sort"`
	TenantID   *int64        `json:"tenantId" form:"tenantId" gorm:"column:tenant_id"`
}

// ---------------------------------------------------------------------------
// ods_szdn_section 路段信息
// ---------------------------------------------------------------------------

type odsSzdnSection struct {
	ID           *string   `json:"id" gorm:"column:id"`
	RoadCode     *string   `json:"roadCode" gorm:"column:road_code"`
	RoadName     *string   `json:"roadName" gorm:"column:road_name"`
	SectionCode  *string   `json:"sectionCode" gorm:"column:section_code"`
	SectionName  *string   `json:"sectionName" gorm:"column:section_name"`
	StartPileNo  *int64    `json:"startPileNo" gorm:"column:start_pile_no"`
	EndPileNo    *int64    `json:"endPileNo" gorm:"column:end_pile_no"`
	OrgCode      *string   `json:"orgCode" gorm:"column:org_code"`
	OrgName      *string   `json:"orgName" gorm:"column:org_name"`
	OrgLevelCode *string   `json:"orgLevelCode" gorm:"column:org_level_code"`
	OrgCategory  *string   `json:"orgCategory" gorm:"column:org_category"`
	Mileage      *int64    `json:"mileage" gorm:"column:mileage"`
	OpenDate     *dateOnly `json:"openDate" gorm:"column:open_date"`
}

// ---------------------------------------------------------------------------
// ods_szdn_toll 收费站基础信息
// ---------------------------------------------------------------------------

type odsSzdnToll struct {
	ID                     *string   `json:"id" gorm:"column:id"`
	RoadCode               *string   `json:"roadCode" gorm:"column:road_code"`
	IDCard                 *string   `json:"idCard" gorm:"column:id_card"`
	TollCode               *string   `json:"tollCode" gorm:"column:toll_code"`
	TollName               *string   `json:"tollName" gorm:"column:toll_name"`
	PileNo                 *string   `json:"pileNo" gorm:"column:pile_no"`
	OrgName                *string   `json:"orgName" gorm:"column:org_name"`
	HexCode                *string   `json:"hexCode" gorm:"column:hex_code"`
	StateCode              *string   `json:"stateCode" gorm:"column:state_code"`
	OrgCode                *string   `json:"orgCode" gorm:"column:org_code"`
	Longitude              *string   `json:"longitude" gorm:"column:longitude"`
	Latitude               *string   `json:"latitude" gorm:"column:latitude"`
	OpenDate               *dateOnly `json:"openDate" gorm:"column:open_date"`
	TollAliasName          *string   `json:"tollAliasName" gorm:"column:toll_alias_name"`
	InMonitorResource      *string   `json:"inMonitorResource" gorm:"column:in_monitor_resource"`
	LaneMonitorResource    *string   `json:"laneMonitorResource" gorm:"column:lane_monitor_resource"`
	SquareMonitorResource  *string   `json:"squareMonitorResource" gorm:"column:square_monitor_resource"`
	DynamicMonitorResource *string   `json:"dynamicMonitorResource" gorm:"column:dynamic_monitor_resource"`
	TollCodeMerge          *string   `json:"tollCodeMerge" gorm:"column:toll_code_merge"`
	StateCodeMerge         *string   `json:"stateCodeMerge" gorm:"column:state_code_merge"`
	TollNameMerge          *string   `json:"tollNameMerge" gorm:"column:toll_name_merge"`
	SectionCode            *string   `json:"sectionCode" gorm:"column:section_code"`
	TollOrgCode            *string   `json:"tollOrgCode" gorm:"column:toll_org_code"`
	IsAccess               *string   `json:"isAccess" gorm:"column:is_access"`

	// @TableField(exist = false)：列表接口用 redis section_list 回填。
	SectionName     *string   `json:"sectionName"`
	SectionCodeList []*string `json:"sectionCodeList" gorm:"-"`
}

// ---------------------------------------------------------------------------
// ods_szdn_gantry 门架信息
// ---------------------------------------------------------------------------

type odsSzdnGantry struct {
	ID                 *string `json:"id" gorm:"column:id"`
	GantryCode         *string `json:"gantryCode" gorm:"column:gantry_code"`
	GantryName         *string `json:"gantryName" gorm:"column:gantry_name"`
	RoadCode           *string `json:"roadCode" gorm:"column:road_code"`
	SectionCode        *string `json:"sectionCode" gorm:"column:section_code"`
	TollCode           *string `json:"tollCode" gorm:"column:toll_code"`
	OrgCode            *string `json:"orgCode" gorm:"column:org_code"`
	HexCode            *string `json:"hexCode" gorm:"column:hex_code"`
	Direction          *string `json:"direction" gorm:"column:direction"`
	PileNo             *string `json:"pileNo" gorm:"column:pile_no"`
	Lon                *string `json:"lon" gorm:"column:lon"`
	Lat                *string `json:"lat" gorm:"column:lat"`
	IsVirtual          *string `json:"isVirtual" gorm:"column:is_virtual"`
	Mileage            *string `json:"mileage" gorm:"column:mileage"`
	BoundaryGantryType *string `json:"boundaryGantryType" gorm:"column:boundary_gantry_type"`
	GantryType         *string `json:"gantryType" gorm:"column:gantry_type"`
	CityCode           *string `json:"cityCode" gorm:"column:city_code"`
	DistrictName       *string `json:"districtName" gorm:"column:district_name"`
	BelongGroup        *string `json:"belongGroup" gorm:"column:belong_group"`
	GantryCodeMerge    *string `json:"gantryCodeMerge" gorm:"column:gantry_code_merge"`
	GantryNameAlias    *string `json:"gantryNameAlias" gorm:"column:gantry_name_alias"`
	Remark             *string `json:"remark" gorm:"column:remark"`

	// @TableField(exist = false)
	IsData          *string   `json:"isData"`
	RoadName        *string   `json:"roadName"`
	SectionName     *string   `json:"sectionName"`
	TollName        *string   `json:"tollName"`
	OrgName         *string   `json:"orgName"`
	SectionCodeList []*string `json:"sectionCodeList" gorm:"-"`
}

// ---------------------------------------------------------------------------
// ods_yhgl_v_base_org 机构信息
// ---------------------------------------------------------------------------

type odsYhglVBaseOrg struct {
	BigID           *string   `json:"bigId" gorm:"column:big_id"`
	OrgCode         *string   `json:"orgCode" gorm:"column:org_code"`
	OrgName         *string   `json:"orgName" gorm:"column:org_name"`
	OrgShortName    *string   `json:"orgShortName" gorm:"column:org_short_name"`
	OrgParentID     *string   `json:"orgParentId" gorm:"column:org_parent_id"`
	OrgLevelCode    *string   `json:"orgLevelCode" gorm:"column:org_level_code"`
	OrgIsVirtual    *string   `json:"orgIsVirtual" gorm:"column:org_is_virtual"`
	OrgMaintenance  *string   `json:"orgMaintenance" gorm:"column:org_maintenance"`
	OrgSequence     *int64    `json:"orgSequence" gorm:"column:org_sequence"`
	OrgIsManager    *string   `json:"orgIsManager" gorm:"column:org_is_manager"`
	OrgIsDeleted    *string   `json:"orgIsDeleted" gorm:"column:org_is_deleted"`
	OrgCategory     *string   `json:"orgCategory" gorm:"column:org_category"`
	OrgIsAuthorized *string   `json:"orgIsAuthorized" gorm:"column:org_is_authorized"`
	OrgAddress      *string   `json:"orgAddress" gorm:"column:org_address"`
	OrgIsYhAutarky  *string   `json:"orgIsYhAutarky" gorm:"column:org_is_yh_autarky"`
	LoadTime        *dateOnly `json:"loadTime" gorm:"column:load_time"`
	GradeLevel      *int      `json:"gradeLevel" gorm:"column:grade_level"`
	ParentID        *int64    `json:"parentId" gorm:"column:parentId"`
}

// ---------------------------------------------------------------------------
// geometry 路线经纬度
// ---------------------------------------------------------------------------

type geometry struct {
	ID    *int    `json:"id" gorm:"column:id"`
	Lxbh  *string `json:"lxbh" gorm:"column:lxbh"`
	Lxfx  *string `json:"lxfx" gorm:"column:lxfx"`
	Qdzh  *int    `json:"qdzh" gorm:"column:qdzh"`
	Zdzh  *int    `json:"zdzh" gorm:"column:zdzh"`
	Paths *string `json:"paths" gorm:"column:paths"`

	// @TableField(exist = false)：HenDa 查询用的桩号字符串。
	ZhStr *string `json:"zhStr"`
}

// ---------------------------------------------------------------------------
// zdata_location_dict 车辆位置字典
// ---------------------------------------------------------------------------

type zdataLocationDict struct {
	ID           *int64    `json:"id" gorm:"column:id"`
	Type         *string   `json:"type" gorm:"column:type"`
	Name         *string   `json:"name" gorm:"column:name"`
	RawCode      *string   `json:"rawCode" gorm:"column:raw_code"`
	StandardCode *string   `json:"standardCode" gorm:"column:standard_code"`
	Roadcode     *string   `json:"roadcode" gorm:"column:roadcode"`
	Roadname     *string   `json:"roadname" gorm:"column:roadname"`
	Sectioncode  *string   `json:"sectioncode" gorm:"column:sectioncode"`
	Sectionname  *string   `json:"sectionname" gorm:"column:sectionname"`
	Tollcode     *string   `json:"tollcode" gorm:"column:tollcode"`
	Tollname     *string   `json:"tollname" gorm:"column:tollname"`
	Orgcode      *string   `json:"orgcode" gorm:"column:orgcode"`
	Orgname      *string   `json:"orgname" gorm:"column:orgname"`
	CreatedAt    *dateOnly `json:"createdAt" gorm:"column:created_at"`
	UpdatedAt    *dateOnly `json:"updatedAt" gorm:"column:updated_at"`
}

// ---------------------------------------------------------------------------
// zdata_trail_fitting 车辆出入口拟合轨迹
// ---------------------------------------------------------------------------

type zdataTrailFitting struct {
	Cid               *string      `json:"cid" gorm:"column:cid"`
	Enaxlecount       *int         `json:"enaxlecount" gorm:"column:enaxlecount"`
	Entime            *dateOnly    `json:"entime" gorm:"column:entime"`
	Entolllaneid      *string      `json:"entolllaneid" gorm:"column:entolllaneid"`
	Entollstationid   *string      `json:"entollstationid" gorm:"column:entollstationid"`
	Entollstationname *string      `json:"entollstationname" gorm:"column:entollstationname"`
	Envehicleclass    *int         `json:"envehicleclass" gorm:"column:envehicleclass"`
	Envehicleid       *string      `json:"envehicleid" gorm:"column:envehicleid"`
	Envehicletype     *int         `json:"envehicletype" gorm:"column:envehicletype"`
	Enweight          *int64       `json:"enweight" gorm:"column:enweight"`
	Extime            *isoDateTime `json:"extime" gorm:"column:extime"`
	Extolllaneid      *string      `json:"extolllaneid" gorm:"column:extolllaneid"`
	Extollstationid   *string      `json:"extollstationid" gorm:"column:extollstationid"`
	Extollstationname *string      `json:"extollstationname" gorm:"column:extollstationname"`
	Exvehicleclass    *int         `json:"exvehicleclass" gorm:"column:exvehicleclass"`
	Exvehicleid       *string      `json:"exvehicleid" gorm:"column:exvehicleid"`
	Exvehicletype     *int         `json:"exvehicletype" gorm:"column:exvehicletype"`
	Exweight          *int64       `json:"exweight" gorm:"column:exweight"`
	Trailpoints       *string      `json:"trailpoints" gorm:"column:trailpoints"`
}

// ---------------------------------------------------------------------------
// zdata_trail_tracks 轨迹数据
// ---------------------------------------------------------------------------

type zdataTrailTracks struct {
	UUID              *string       `json:"uuid" gorm:"column:uuid"`
	Type              *int          `json:"type" gorm:"column:type"`
	PointCount        *int64        `json:"pointCount" gorm:"column:point_count"`
	PlateKey          *string       `json:"plateKey" gorm:"column:plate_key"`
	EnterTime         *web.DateTime `json:"enterTime" gorm:"column:enter_time"`
	ExitTime          *web.DateTime `json:"exitTime" gorm:"column:exit_time"`
	TrailPoints       *string       `json:"trailPoints" gorm:"column:trail_points"`
	EnterLocationcode *string       `json:"enterLocationcode" gorm:"column:enter_locationcode"`
	ExitLocationcode  *string       `json:"exitLocationcode" gorm:"column:exit_locationcode"`
	TrackJosn         *string       `json:"trackJosn" gorm:"column:track_josn"`
	Enaxlecount       *int          `json:"enaxlecount" gorm:"column:enaxlecount"`
	Entolllaneid      *string       `json:"entolllaneid" gorm:"column:entolllaneid"`
	Entollstationid   *string       `json:"entollstationid" gorm:"column:entollstationid"`
	Entollstationname *string       `json:"entollstationname" gorm:"column:entollstationname"`
	Envehicleclass    *string       `json:"envehicleclass" gorm:"column:envehicleclass"`
	Envehicleid       *string       `json:"envehicleid" gorm:"column:envehicleid"`
	Envehicletype     *string       `json:"envehicletype" gorm:"column:envehicletype"`
	Enweight          *float64      `json:"enweight" gorm:"column:enweight"`
	Extolllaneid      *string       `json:"extolllaneid" gorm:"column:extolllaneid"`
	Extollstationid   *string       `json:"extollstationid" gorm:"column:extollstationid"`
	Extollstationname *string       `json:"extollstationname" gorm:"column:extollstationname"`
	Exvehicleclass    *string       `json:"exvehicleclass" gorm:"column:exvehicleclass"`
	Exvehicleid       *string       `json:"exvehicleid" gorm:"column:exvehicleid"`
	Exvehicletype     *string       `json:"exvehicletype" gorm:"column:exvehicletype"`
	Exweight          *float64      `json:"exweight" gorm:"column:exweight"`
	StartLon          *string       `json:"startLon" gorm:"column:start_lon"`
	StratLat          *string       `json:"stratLat" gorm:"column:strat_lat"`
	EndLon            *string       `json:"endLon" gorm:"column:end_lon"`
	EndLat            *string       `json:"endLat" gorm:"column:end_lat"`

	// @TableField(exist = false) —— 与 Java 一致地参与 JSON 输出（未赋值时为 null）。
	FirtStationCode   *string   `json:"firtStationCode"`
	FirtStationName   *string   `json:"firtStationName"`
	FirtStationTime   *string   `json:"firtStationTime"`
	PlateColor        *string   `json:"plateColor"`
	CarType           *string   `json:"carType"`
	CarNo             *string   `json:"carNo"`
	CarVehicle        *string   `json:"carVehicle"`
	CarNum            *int64    `json:"carNum"`
	EscapedType       *string   `json:"escapedType"`
	PassType          *string   `json:"passType"`
	EscapedTypeRemark *string   `json:"escapedTypeRemark"`
	ApplyTime1        *string   `json:"applyTime1"`
	ApplyTime2        *string   `json:"applyTime2"`
	IsCylx            *string   `json:"isCylx"`
	Flag              *string   `json:"flag"`
	StartLonDec       *float64  `json:"startLonDec"`
	StratLatDec       *float64  `json:"stratLatDec"`
	EndLonDec         *float64  `json:"endLonDec"`
	EndLatDec         *float64  `json:"endLatDec"`
	UUIDList          []*string `json:"uuidList"`
	PassCount         *int      `json:"passCount"`
	EscapedTfcj       *string   `json:"escapedTfcj"`
}

// ---------------------------------------------------------------------------
// ods_cxzt_fwqclls 服务区车辆流水（控制器挂在 /manager/fwqclls）
// ---------------------------------------------------------------------------

type odsCxztFwqclls struct {
	BigID            *int64       `json:"bigId" gorm:"column:big_id"`
	Datauuid         *string      `json:"datauuid" gorm:"column:datauuid"`
	Targetpicurl     *string      `json:"targetpicurl" gorm:"column:targetpicurl"`
	Vehiclebrand     *string      `json:"vehiclebrand" gorm:"column:vehiclebrand"`
	Platepicurl      *string      `json:"platepicurl" gorm:"column:platepicurl"`
	Rollvehiclestype *string      `json:"rollvehiclestype" gorm:"column:rollvehiclestype"`
	Plateno          *string      `json:"plateno" gorm:"column:plateno"`
	Directionname    *string      `json:"directionname" gorm:"column:directionname"`
	Platetype        *string      `json:"platetype" gorm:"column:platetype"`
	Dangmark         *string      `json:"dangmark" gorm:"column:dangmark"`
	Crosstime        *isoDateTime `json:"crosstime" gorm:"column:crosstime"`
	Axles            *string      `json:"axles" gorm:"column:axles"`
	Devicename       *string      `json:"devicename" gorm:"column:devicename"`
	Ipaddress        *string      `json:"ipaddress" gorm:"column:ipaddress"`
	Servicename      *string      `json:"servicename" gorm:"column:servicename"`
	Vehicletype      *string      `json:"vehicletype" gorm:"column:vehicletype"`
	LoadTime         *string      `json:"loadTime" gorm:"column:load_time"`
	GradeLevel       *string      `json:"gradeLevel" gorm:"column:grade_level"`
}

// ---------------------------------------------------------------------------
// ods_szdn_gantry_ip / ods_szdn_toll_station_ip 设备 IP
// ---------------------------------------------------------------------------

type odsSzdnGantryIp struct {
	ID         *int64  `json:"id" gorm:"column:id"`
	GantryCode *string `json:"gantryCode" gorm:"column:gantry_code"`
	GantryName *string `json:"gantryName" gorm:"column:gantry_name"`
	OrgCode    *string `json:"orgCode" gorm:"column:org_code"`
	IP         *string `json:"ip" gorm:"column:ip"`
	Brand      *string `json:"brand" gorm:"column:brand"`
	Type       *string `json:"type" gorm:"column:type"`
}

type odsSzdnTollStationIp struct {
	ID       *int64  `json:"id" gorm:"column:id"`
	TollCode *string `json:"tollCode" gorm:"column:toll_code"`
	TollName *string `json:"tollName" gorm:"column:toll_name"`
	OrgCode  *string `json:"orgCode" gorm:"column:org_code"`
	IP       *string `json:"ip" gorm:"column:ip"`
	Brand    *string `json:"brand" gorm:"column:brand"`
}
