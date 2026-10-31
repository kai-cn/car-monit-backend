// JAVA 对照: com.ruoyi.base.domain.BaseConfigServiceArea
// JAVA 对照: com.ruoyi.base.domain.CarWarningConfig
// 类/职责: 服务区配置 / 服务区判定规则实体
// 对应 Go 文件: internal/modules/base/models_config.go
//
// DIFF: CarWarningConfig 的 fwqmc/lon/lat/roadCode/sectionCode/pileNo 来自 join 的
// base_config_service_area（t1），写入时必须排除，见 carWarningConfigSpec.readOnly。
package base

// baseConfigServiceArea 对应 BaseConfigServiceArea（继承 BasePlusEntity）。
type baseConfigServiceArea struct {
	entityBase
	Fwqbm       *string `json:"fwqbm" gorm:"column:fwqbm"`
	Fwqmc       *string `json:"fwqmc" gorm:"column:fwqmc"`
	Lon         *string `json:"lon" gorm:"column:lon"`
	Lat         *string `json:"lat" gorm:"column:lat"`
	RoadCode    *string `json:"roadCode" gorm:"column:road_code"`
	SectionCode *string `json:"sectionCode" gorm:"column:section_code"`
	PileNo      *string `json:"pileNo" gorm:"column:pile_no"`
}

// carWarningConfig 对应 CarWarningConfig（@TableId id, ASSIGN_UUID）。
type carWarningConfig struct {
	ID            *string `json:"id" gorm:"column:id"`
	GantryCodeIn  *string `json:"gantryCodeIn" gorm:"column:gantry_code_in"`
	GantryNameIn  *string `json:"gantryNameIn" gorm:"column:gantry_name_in"`
	GantryCodeOut *string `json:"gantryCodeOut" gorm:"column:gantry_code_out"`
	GantryNameOut *string `json:"gantryNameOut" gorm:"column:gantry_name_out"`
	TimeSpan      *int64  `json:"timeSpan" gorm:"column:time_span"`
	Fwqbm         *string `json:"fwqbm" gorm:"column:fwqbm"`
	Fwqmc         *string `json:"fwqmc" gorm:"column:fwqmc"`
	Lon           *string `json:"lon" gorm:"column:lon"`
	Lat           *string `json:"lat" gorm:"column:lat"`
	RoadCode      *string `json:"roadCode" gorm:"column:road_code"`
	SectionCode   *string `json:"sectionCode" gorm:"column:section_code"`
	PileNo        *string `json:"pileNo" gorm:"column:pile_no"`
	Remark        *string `json:"remark" gorm:"column:remark"`
}
