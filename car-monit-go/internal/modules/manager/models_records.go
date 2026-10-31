// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarFeeRecord.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarExceptRecord.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSplitRecord.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarWhiteInfo.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarQueryLog.java
// 类/职责: 收费流水 / 异常流水 / 拆分流水 / 白名单 / 查询日志的领域模型
// 对应 Go 文件: internal/modules/manager/models_records.go
package manager

import "car-monit-go/internal/web"

// ---------------------------------------------------------------------------
// car_fee_record
// ---------------------------------------------------------------------------

const carFeeRecordTable = "car_fee_record"

type carFeeRecord struct {
	EntityBase
	CarID        *string   `json:"carId" form:"carId" gorm:"column:car_id"`
	CarNo        *string   `json:"carNo" form:"carNo" gorm:"column:car_no"`
	CarType      *string   `json:"carType" form:"carType" gorm:"column:car_type"`
	CarVehicle   *string   `json:"carVehicle" form:"carVehicle" gorm:"column:car_vehicle"`
	InStationID  *string   `json:"inStationId" form:"inStationId" gorm:"column:in_station_id"`
	InStation    *string   `json:"inStation" form:"inStation" gorm:"column:in_station"`
	InTime       *dateOnly `json:"inTime" gorm:"column:in_time"`
	OutStationID *string   `json:"outStationId" form:"outStationId" gorm:"column:out_station_id"`
	OutStation   *string   `json:"outStation" form:"outStation" gorm:"column:out_station"`
	OutTime      *dateOnly `json:"outTime" gorm:"column:out_time"`
	ChargeType   *string   `json:"chargeType" form:"chargeType" gorm:"column:charge_type"`
	Amount       *float64  `json:"amount" form:"amount" gorm:"column:amount"`
	ExceptID     *string   `json:"exceptId" form:"exceptId" gorm:"column:except_id"`
	BackCol1     *string   `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	BackCol2     *string   `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	Status       *string   `json:"status" form:"status" gorm:"column:status"`
	Remark       *string   `json:"remark" form:"remark" gorm:"column:remark"`

	ApplyTime1 *string `json:"applyTime1" form:"applyTime1" gorm:"-"`
	ApplyTime2 *string `json:"applyTime2" form:"applyTime2" gorm:"-"`
}

var carFeeRecordColumns = mergeColumns(baseColumns, map[string]string{
	"carId":        "car_id",
	"carNo":        "car_no",
	"carType":      "car_type",
	"carVehicle":   "car_vehicle",
	"inStationId":  "in_station_id",
	"inStation":    "in_station",
	"inTime":       "in_time",
	"outStationId": "out_station_id",
	"outStation":   "out_station",
	"outTime":      "out_time",
	"chargeType":   "charge_type",
	"amount":       "amount",
	"exceptId":     "except_id",
	"backCol1":     "back_col1",
	"backCol2":     "back_col2",
	"status":       "status",
	"remark":       "remark",
})

const carFeeRecordSelectColumns = `t.id, t.car_id, t.car_no, t.car_type, t.car_vehicle, t.in_station_id,
	t.in_station, t.in_time, t.out_station_id, t.out_station, t.out_time, t.charge_type, t.amount,
	t.except_id, t.back_col1, t.back_col2, t.remark, t.status, t.sort, t.eps_id, t.del_flag, t.create_by,
	t.create_time, t.update_by, t.update_time, t.tenant_id`

// ---------------------------------------------------------------------------
// car_except_record
// ---------------------------------------------------------------------------

const carExceptRecordTable = "car_except_record"

// carExceptRecord 对应 CarExceptRecord。
//
// DIFF: supplementaryStatus 在 Java 里有字段默认值 "0"；Go 结构体没有默认值，
// 查询后由 normalize() 补齐，保证 JSON 里始终出现 "supplementaryStatus":"0"。
type carExceptRecord struct {
	EntityBase
	CarID        *string       `json:"carId" form:"carId" gorm:"column:car_id"`
	CarNo        *string       `json:"carNo" form:"carNo" gorm:"column:car_no"`
	CarType      *string       `json:"carType" form:"carType" gorm:"column:car_type"`
	CarVehicle   *string       `json:"carVehicle" form:"carVehicle" gorm:"column:car_vehicle"`
	CarNum       *int64        `json:"carNum" form:"carNum" gorm:"column:car_num"`
	PassType     *string       `json:"passType" form:"passType" gorm:"column:pass_type"`
	InStationID  *string       `json:"inStationId" form:"inStationId" gorm:"column:in_station_id"`
	InStation    *string       `json:"inStation" form:"inStation" gorm:"column:in_station"`
	InTime       *web.DateTime `json:"inTime" gorm:"column:in_time"`
	OutStationID *string       `json:"outStationId" form:"outStationId" gorm:"column:out_station_id"`
	OutStation   *string       `json:"outStation" form:"outStation" gorm:"column:out_station"`
	OutTime      *web.DateTime `json:"outTime" gorm:"column:out_time"`
	TotalAmount  *float64      `json:"totalAmount" form:"totalAmount" gorm:"column:total_amount"`
	ChargeAmount *float64      `json:"chargeAmount" form:"chargeAmount" gorm:"column:charge_amount"`
	DifAmount    *float64      `json:"difAmount" form:"difAmount" gorm:"column:dif_amount"`
	EscapedType  *string       `json:"escapedType" form:"escapedType" gorm:"column:escaped_type"`
	Remark       *string       `json:"remark" form:"remark" gorm:"column:remark"`
	BackCol1     *string       `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	BackCol2     *string       `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	Status       *string       `json:"status" form:"status" gorm:"column:status"`

	ApplyTime1          *string  `json:"applyTime1" form:"applyTime1" gorm:"-"`
	ApplyTime2          *string  `json:"applyTime2" form:"applyTime2" gorm:"-"`
	ApplyTime3          *string  `json:"applyTime3" form:"applyTime3" gorm:"-"`
	ApplyTime4          *string  `json:"applyTime4" form:"applyTime4" gorm:"-"`
	CreateTimeStr       *string  `json:"createTimeStr" gorm:"-"`
	OrgID               *string  `json:"orgId" form:"orgId" gorm:"-"`
	SupplementaryStatus *string  `json:"supplementaryStatus" form:"supplementaryStatus" gorm:"-"`
	ExceptIDs           *string  `json:"exceptIds" form:"exceptIds" gorm:"-"`
	CarNoQuery          *string  `json:"carNoQuery" form:"carNoQuery" gorm:"-"`
	CreateInfo          *string  `json:"createInfo" form:"createInfo" gorm:"column:create_info"`
	ExceptNum           *int64   `json:"exceptNum" gorm:"-"`
	ExceptAmount        *float64 `json:"exceptAmount" gorm:"-"`
	InTimeStr           *string  `json:"inTimeStr" gorm:"-"`
	OutTimeStr          *string  `json:"outTimeStr" gorm:"-"`
}

// normalize 补齐 Java 字段默认值（supplementaryStatus 默认 "0"）。
func (r *carExceptRecord) normalize() {
	if strOf(r.SupplementaryStatus) == "" {
		r.SupplementaryStatus = strPtr("0")
	}
}

var carExceptRecordColumns = mergeColumns(baseColumns, map[string]string{
	"carId":        "car_id",
	"carNo":        "car_no",
	"carType":      "car_type",
	"carVehicle":   "car_vehicle",
	"carNum":       "car_num",
	"passType":     "pass_type",
	"inStationId":  "in_station_id",
	"inStation":    "in_station",
	"inTime":       "in_time",
	"outStationId": "out_station_id",
	"outStation":   "out_station",
	"outTime":      "out_time",
	"totalAmount":  "total_amount",
	"chargeAmount": "charge_amount",
	"difAmount":    "dif_amount",
	"escapedType":  "escaped_type",
	"remark":       "remark",
	"backCol1":     "back_col1",
	"backCol2":     "back_col2",
	"status":       "status",
})

const carExceptRecordSelectColumns = `t.id, t.car_id, t.car_no, t.car_type, t.car_vehicle, t.car_num,
	t.pass_type, t.in_station_id, t.in_station, t.in_time, t.out_station_id, t.out_station, t.out_time,
	t.total_amount, t.charge_amount, t.dif_amount, t.escaped_type, t.remark, t.back_col1, t.back_col2,
	t.status, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time,
	t.tenant_id`

// ---------------------------------------------------------------------------
// car_split_record
// ---------------------------------------------------------------------------

const carSplitRecordTable = "car_split_record"

type carSplitRecord struct {
	EntityBase
	CarID        *string   `json:"carId" form:"carId" gorm:"column:car_id"`
	CarNo        *string   `json:"carNo" form:"carNo" gorm:"column:car_no"`
	CarType      *string   `json:"carType" form:"carType" gorm:"column:car_type"`
	CarVehicle   *string   `json:"carVehicle" form:"carVehicle" gorm:"column:car_vehicle"`
	PassType     *string   `json:"passType" form:"passType" gorm:"column:pass_type"`
	InStationID  *string   `json:"inStationId" form:"inStationId" gorm:"column:in_station_id"`
	InStation    *string   `json:"inStation" form:"inStation" gorm:"column:in_station"`
	InTime       *dateOnly `json:"inTime" gorm:"column:in_time"`
	OutStationID *string   `json:"outStationId" form:"outStationId" gorm:"column:out_station_id"`
	OutStation   *string   `json:"outStation" form:"outStation" gorm:"column:out_station"`
	OutTime      *dateOnly `json:"outTime" gorm:"column:out_time"`
	Amount       *float64  `json:"amount" form:"amount" gorm:"column:amount"`
	BackCol1     *string   `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	BackCol2     *string   `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	Status       *string   `json:"status" form:"status" gorm:"column:status"`

	ApplyTime1    *string `json:"applyTime1" form:"applyTime1" gorm:"-"`
	ApplyTime2    *string `json:"applyTime2" form:"applyTime2" gorm:"-"`
	CreateTimeStr *string `json:"createTimeStr" gorm:"-"`
}

var carSplitRecordColumns = mergeColumns(baseColumns, map[string]string{
	"carId":        "car_id",
	"carNo":        "car_no",
	"carType":      "car_type",
	"carVehicle":   "car_vehicle",
	"passType":     "pass_type",
	"inStationId":  "in_station_id",
	"inStation":    "in_station",
	"inTime":       "in_time",
	"outStationId": "out_station_id",
	"outStation":   "out_station",
	"outTime":      "out_time",
	"amount":       "amount",
	"backCol1":     "back_col1",
	"backCol2":     "back_col2",
	"status":       "status",
})

const carSplitRecordSelectColumns = `t.id, t.car_id, t.car_no, t.car_type, t.car_vehicle, t.pass_type,
	t.in_station_id, t.in_station, t.in_time, t.out_station_id, t.out_station, t.out_time, t.amount,
	t.back_col1, t.back_col2, t.status, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time,
	t.update_by, t.update_time, t.tenant_id`

// ---------------------------------------------------------------------------
// car_white_info
// ---------------------------------------------------------------------------

const carWhiteInfoTable = "car_white_info"

type carWhiteInfo struct {
	EntityBase
	PlateColor *string `json:"plateColor" form:"plateColor" gorm:"column:plate_color"`
	CarNo      *string `json:"carNo" form:"carNo" gorm:"column:car_no"`
	CarType    *string `json:"carType" form:"carType" gorm:"column:car_type"`
	CarVehicle *string `json:"carVehicle" form:"carVehicle" gorm:"column:car_vehicle"`
	CarNum     *int64  `json:"carNum" form:"carNum" gorm:"column:car_num"`
	FileIDs    *string `json:"fileIds" form:"fileIds" gorm:"column:file_ids"`
	BackCol1   *string `json:"backCol1" form:"backCol1" gorm:"column:back_col1"`
	BackCol2   *string `json:"backCol2" form:"backCol2" gorm:"column:back_col2"`
	Status     *string `json:"status" form:"status" gorm:"column:status"`
	Remark     *string `json:"remark" form:"remark" gorm:"column:remark"`

	CreateTimeStr *string `json:"createTimeStr" gorm:"-"`
	CreateInfo    *string `json:"createInfo" form:"createInfo" gorm:"column:create_info"`
	CarNoQuery    *string `json:"carNoQuery" form:"carNoQuery" gorm:"-"`
}

var carWhiteInfoColumns = mergeColumns(baseColumns, map[string]string{
	"plateColor": "plate_color",
	"carNo":      "car_no",
	"carType":    "car_type",
	"carVehicle": "car_vehicle",
	"carNum":     "car_num",
	"fileIds":    "file_ids",
	"backCol1":   "back_col1",
	"backCol2":   "back_col2",
	"status":     "status",
	"remark":     "remark",
})

const carWhiteInfoSelectColumns = `t.id, t.plate_color, t.car_no, t.car_type, t.car_vehicle, t.car_num,
	t.file_ids, t.back_col1, t.back_col2, t.remark, t.status, t.sort, t.eps_id, t.del_flag, t.create_by,
	t.create_time, t.update_by, t.update_time, t.tenant_id`

// ---------------------------------------------------------------------------
// car_query_log
// ---------------------------------------------------------------------------

const carQueryLogTable = "car_query_log"

// carQueryLog 对应 CarQueryLog。注意 userId 在 Java 里是 String（不是 Long）。
type carQueryLog struct {
	EntityBase
	UserID         *string `json:"userId" form:"userId" gorm:"column:user_id"`
	UserName       *string `json:"userName" form:"userName" gorm:"column:user_name"`
	UserIP         *string `json:"userIp" form:"userIp" gorm:"column:user_ip"`
	ModelType      *string `json:"modelType" form:"modelType" gorm:"column:model_type"`
	MenuPoint      *string `json:"menuPoint" form:"menuPoint" gorm:"column:menu_point"`
	QueryCondition *string `json:"queryCondition" form:"queryCondition" gorm:"column:query_condition"`
	BackCol1       *string `json:"backCol1" gorm:"column:back_col1"`
	BackCol2       *string `json:"backCol2" gorm:"column:back_col2"`
	Status         *string `json:"status" gorm:"column:status"`
	Remark         *string `json:"remark" form:"remark" gorm:"column:remark"`

	ApplyTime1 *string `json:"applyTime1" form:"applyTime1" gorm:"-"`
	ApplyTime2 *string `json:"applyTime2" form:"applyTime2" gorm:"-"`
}

var carQueryLogColumns = mergeColumns(baseColumns, map[string]string{
	"userId":         "user_id",
	"userName":       "user_name",
	"userIp":         "user_ip",
	"modelType":      "model_type",
	"menuPoint":      "menu_point",
	"queryCondition": "query_condition",
	"backCol1":       "back_col1",
	"backCol2":       "back_col2",
	"status":         "status",
	"remark":         "remark",
})

const carQueryLogSelectColumns = `t.id, t.user_id, t.user_name, t.user_ip, t.model_type, t.menu_point,
	t.query_condition, t.back_col1, t.back_col2, t.remark, t.status, t.sort, t.eps_id, t.del_flag,
	t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id`

// mergeColumns 合并「基础审计列」与实体自有列。
func mergeColumns(base, extra map[string]string) map[string]string {
	out := make(map[string]string, len(base)+len(extra))
	for k, v := range base {
		out[k] = v
	}
	for k, v := range extra {
		out[k] = v
	}
	return out
}
