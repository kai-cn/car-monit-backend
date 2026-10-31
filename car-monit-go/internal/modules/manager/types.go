// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/BasePlusEntity.java
// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/BasePlusEntityInputNew.java
// JAVA 对照: ruoyi-base/src/main/java/com/ruoyi/base/domain/TrailInfo.java (轨迹包装 VO)
// 类/职责: 实体基类与少量自定义类型
// 对应 Go 文件: internal/modules/manager/types.go
//
// DIFF: Java 的实体由 MyBatis-Plus 按驼峰-下划线映射；Go 用 gorm column 标签显式声明。
// DIFF: Java 的 Long/BigDecimal 可为 null（前端能拿到 null）；Go 用指针保留“null / 缺省”语义。
// DIFF: 各实体的表名与列名写在本包常量里，internal/model 不做改动（并行开发的约定）。
package manager

import (
	"database/sql/driver"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"car-monit-go/internal/web"
)

// EntityBase 对应 BasePlusEntity / BasePlusEntityInputNew。
//
// DIFF: Java 的 id 是 String，列表 SQL 少选该列时前端拿到 null；
// Go 侧同样用指针，避免未查询的列被序列化成 ""。
type EntityBase struct {
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

// baseColumns 是审计字段的「JSON 键 -> 列名」映射，供 pickColumns 使用。
var baseColumns = map[string]string{
	"epsId":    "eps_id",
	"delFlag":  "del_flag",
	"createBy": "create_by",
	"updateBy": "update_by",
	"sort":     "sort",
	"tenantId": "tenant_id",
}

// dateOnly 对应 Jackson 的 @JsonFormat(pattern = "yyyy-MM-dd")。
//
// DIFF: 基础库只有 web.DateTime（yyyy-MM-dd HH:mm:ss），这里在本包内补一个只输出日期的类型，
// 保证 CarInfo.lastPassTime / CarFeeRecord.inTime 等字段的 JSON 形态与 Java 一致。
type dateOnly struct {
	time.Time
}

const dateOnlyLayout = "2006-01-02"

func (d dateOnly) MarshalJSON() ([]byte, error) {
	if d.IsZero() {
		return []byte("null"), nil
	}
	return []byte(`"` + d.Format(dateOnlyLayout) + `"`), nil
}

func (d *dateOnly) UnmarshalJSON(b []byte) error {
	s := strings.Trim(string(b), `"`)
	if s == "" || s == "null" {
		d.Time = time.Time{}
		return nil
	}
	t, err := web.ParseDate(s)
	if err != nil {
		return err
	}
	d.Time = t
	return nil
}

func (d dateOnly) Value() (driver.Value, error) {
	if d.IsZero() {
		return nil, nil
	}
	return d.Time, nil
}

func (d *dateOnly) Scan(v any) error {
	if v == nil {
		d.Time = time.Time{}
		return nil
	}
	switch x := v.(type) {
	case time.Time:
		d.Time = x
	case []byte:
		t, err := web.ParseDate(string(x))
		if err != nil {
			return err
		}
		d.Time = t
	case string:
		t, err := web.ParseDate(x)
		if err != nil {
			return err
		}
		d.Time = t
	default:
		return fmt.Errorf("不支持的日期类型 %T", v)
	}
	return nil
}

// trailBO 对应 com.ruoyi.base.domain.TrailBo 的全部字段。
//
// JAVA 对照: com/ruoyi/base/domain/TrailBo.java:8
// DIFF: Java 里 9 个 *BO 字段（省界称重/门架抓拍/省界抓拍/收费站抓拍/流水/进出口流水/IP）
// 只在轨迹服务回填时才有值，本模块保持 null。
type trailBO struct {
	PointUUID               *string  `json:"pointUuid"`
	StateType               *string  `json:"stateType"`
	PointFlag               *string  `json:"pointFlag"`
	PointJosn               *string  `json:"pointJosn"`
	BorderWeighingCaptureBO any      `json:"borderWeighingCaptureBO"`
	GantryCaptureBO         any      `json:"gantryCaptureBO"`
	ProvCaptureBO           any      `json:"provCaptureBO"`
	StationCapture          any      `json:"stationCapture"`
	FeeRecord               any      `json:"feeRecord"`
	FeeStationEnter         any      `json:"feeStationEnter"`
	FeeStationExit          any      `json:"feeStationExit"`
	CaptureTime             *string  `json:"captureTime"`
	DirectionIn             *bool    `json:"directionIn"`
	LocationCode            *string  `json:"locationCode"`
	LocationFlag            *string  `json:"locationFlag"`
	IPType                  *string  `json:"ipType"`
	LocationJosn            *string  `json:"locationJosn"`
	GantryIpBO              any      `json:"gantryIpBO"`
	StationIpBO             any      `json:"stationIpBO"`
	DevCode                 *string  `json:"devCode"`
	DevName                 *string  `json:"devName"`
	ImagesArry              *string  `json:"imagesArry"`
	Lon                     *float64 `json:"lon"`
	Lat                     *float64 `json:"lat"`
	RoadCode                *string  `json:"roadCode"`
	SectionCode             *string  `json:"sectionCode"`
	Direction               *string  `json:"direction"`
	Pileno                  *string  `json:"pileno"`
	PreCaptureTime          *string  `json:"preCaptureTime"`
	CountNum                *int64   `json:"countNum"`
	PilenoDec               *float64 `json:"pilenoDec"`
	IsQuery                 *string  `json:"isQuery"`
}

// parseTrailInfo 把 track_josn 解析成 Java 的 TrailInfo 形态（字段全集，缺失为 null）。
//
// JAVA 对照: CarInfoServiceImpl.selectCarInfoById / CarSuspiciousServiceImpl.selectCarSuspiciousById
// 两处都是 JSON.parseObject(trackJosn, TrailInfo.class)。
func parseTrailInfo(raw string) (*trailInfo, *zdataTrailTracks, []*trailBO, error) {
	var shell struct {
		TrailUUID *string           `json:"trailUuid"`
		EnterTime *web.DateTime     `json:"enterTime"`
		Tracks    *zdataTrailTracks `json:"tracks"`
		TrailList []*trailBO        `json:"trailList"`
	}
	if err := json.Unmarshal([]byte(raw), &shell); err != nil {
		return nil, nil, nil, err
	}
	info := &trailInfo{TrailUUID: shell.TrailUUID, EnterTime: shell.EnterTime, Tracks: shell.Tracks}
	if shell.TrailList != nil {
		info.TrailList = shell.TrailList
	}
	return info, shell.Tracks, shell.TrailList, nil
}

// trailInfo 对应 com.ruoyi.base.domain.TrailInfo。
//
// DIFF: Java 的 trailDevCountBO 由 ICarTrackInfoService 计算（依赖路网/地图服务）；
// 本模块只做 CarInfo 详情里的轨迹回填，不计算设备统计与路网 Geometry，
// 因此 raodTrailList 固定输出空数组、trailDevCountBO 输出 null（见 carinfo.go 的 // DIFF:）。
type trailInfo struct {
	TrailUUID       *string       `json:"trailUuid"`
	EnterTime       *web.DateTime `json:"enterTime"`
	Tracks          any           `json:"tracks"`
	TrailList       any           `json:"trailList"`
	RaodTrailList   []any         `json:"raodTrailList"`
	TrailDevCountBO any           `json:"trailDevCountBO"`
}

// carVO 对应 com.ruoyi.base.domain.CarVO（Redis 缓存 car_list_jc 的元素）。
type carVO struct {
	CarID string `json:"carId"`
	CarNo string `json:"carNo"`
}
