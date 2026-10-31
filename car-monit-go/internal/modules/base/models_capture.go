// JAVA 对照: com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode
// JAVA 对照: com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowProvcaptureAddcode
// JAVA 对照: com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowStationcaptureAddcode
// JAVA 对照: com.ruoyi.base.domain.OdsLwzxsfsjFeeStationEnter01
// JAVA 对照: com.ruoyi.base.domain.OdsSzdnProvinceBorderVehicleWeightNewstructure
// 类/职责: 抓拍流水、省界/收费站抓拍、收费站入口、省界称重实体
// 对应 Go 文件: internal/modules/base/models_capture.go
//
// DIFF: 这些表的列名全是小写无下划线（datasource / gantrycode / snapshottime），
// Java 属性名与之同名，因此 JSON 键名也保持全小写。
package base

// odsRtSzdnSnapshotFlowAddcode 对应门架抓拍流水（@TableId big_id, INPUT）。
type odsRtSzdnSnapshotFlowAddcode struct {
	BigID            *string      `json:"bigId" gorm:"column:big_id"`
	Datasource       *string      `json:"datasource" gorm:"column:datasource"`
	Cameratype       *string      `json:"cameratype" gorm:"column:cameratype"`
	Deviceid         *string      `json:"deviceid" gorm:"column:deviceid"`
	Gantrycode       *string      `json:"gantrycode" gorm:"column:gantrycode"`
	Gantryname       *string      `json:"gantryname" gorm:"column:gantryname"`
	Roadcode         *string      `json:"roadcode" gorm:"column:roadcode"`
	Roadname         *string      `json:"roadname" gorm:"column:roadname"`
	Sectioncode      *string      `json:"sectioncode" gorm:"column:sectioncode"`
	Sectionname      *string      `json:"sectionname" gorm:"column:sectionname"`
	Tollcode         *string      `json:"tollcode" gorm:"column:tollcode"`
	Tollname         *string      `json:"tollname" gorm:"column:tollname"`
	Orgcode          *string      `json:"orgcode" gorm:"column:orgcode"`
	Orgname          *string      `json:"orgname" gorm:"column:orgname"`
	Direction        *int         `json:"direction" gorm:"column:direction"`
	Hexcode          *string      `json:"hexcode" gorm:"column:hexcode"`
	Pileno           *string      `json:"pileno" gorm:"column:pileno"`
	Lon              *float64     `json:"lon" gorm:"column:lon"`
	Lat              *float64     `json:"lat" gorm:"column:lat"`
	Deviceip         *string      `json:"deviceip" gorm:"column:deviceip"`
	Siteid           *int64       `json:"siteid" gorm:"column:siteid"`
	Laneid           *int         `json:"laneid" gorm:"column:laneid"`
	Snapshottimeunix *int64       `json:"snapshottimeunix" gorm:"column:snapshottimeunix"`
	Snapshottime     *isoDateTime `json:"snapshottime" gorm:"column:snapshottime"`
	Receivedtimeunix *int64       `json:"receivedtimeunix" gorm:"column:receivedtimeunix"`
	Receivedtime     *dateOnly    `json:"receivedtime" gorm:"column:receivedtime"`
	Platenumber      *string      `json:"platenumber" gorm:"column:platenumber"`
	Platecolor       *string      `json:"platecolor" gorm:"column:platecolor"`
	Platecolorcode   *int         `json:"platecolorcode" gorm:"column:platecolorcode"`
	Platetype        *string      `json:"platetype" gorm:"column:platetype"`
	Platetypecode    *int         `json:"platetypecode" gorm:"column:platetypecode"`
	Plateconfidence  *int         `json:"plateconfidence" gorm:"column:plateconfidence"`
	Carbrand         *string      `json:"carbrand" gorm:"column:carbrand"`
	Carcolor         *string      `json:"carcolor" gorm:"column:carcolor"`
	Carcolorcode     *int         `json:"carcolorcode" gorm:"column:carcolorcode"`
	Cartype          *string      `json:"cartype" gorm:"column:cartype"`
	Cartypecode      *int         `json:"cartypecode" gorm:"column:cartypecode"`
	Cardirection     *string      `json:"cardirection" gorm:"column:cardirection"`
	Snappicturepath  *string      `json:"snappicturepath" gorm:"column:snappicturepath"`
	Loadtime         *dateOnly    `json:"loadtime" gorm:"column:loadtime"`
	Gradelevel       *int         `json:"gradelevel" gorm:"column:gradelevel"`
	Datauuid         *string      `json:"datauuid" gorm:"column:datauuid"`
	Reserve3         *string      `json:"reserve3" gorm:"column:reserve3"`

	// @TableField(exist = false) —— 与 Java 一致地参与 JSON 输出。
	ID              *string `json:"id"`
	SnapshottimeStr *string `json:"snapshottimeStr"`
	ApplyTime1      *string `json:"applyTime1"`
	ApplyTime2      *string `json:"applyTime2"`
	DirectionStr    *string `json:"directionStr"`
	SectionCodeStr  *string `json:"sectionCodeStr"`
}

// odsRtSzdnSnapshotFlowProvcaptureAddcode 对应省界抓拍（78 列）。
type odsRtSzdnSnapshotFlowProvcaptureAddcode struct {
	BigID                    *int64       `json:"bigId" gorm:"column:big_id"`
	Deviceip                 *string      `json:"deviceip" gorm:"column:deviceip"`
	Tailcapturetimeunix      *int64       `json:"tailcapturetimeunix" gorm:"column:tailcapturetimeunix"`
	Tailcapturetime          *isoDateTime `json:"tailcapturetime" gorm:"column:tailcapturetime"`
	Extendattribute          *string      `json:"extendattribute" gorm:"column:extendattribute"`
	Smallsideimagewidth      *int         `json:"smallsideimagewidth" gorm:"column:smallsideimagewidth"`
	Axletype                 *string      `json:"axletype" gorm:"column:axletype"`
	Smallsideimageheight     *int         `json:"smallsideimageheight" gorm:"column:smallsideimageheight"`
	Platecolorcode           *int         `json:"platecolorcode" gorm:"column:platecolorcode"`
	Platecolor               *string      `json:"platecolor" gorm:"column:platecolor"`
	Cover                    *string      `json:"cover" gorm:"column:cover"`
	Averageauthoritative     *int         `json:"averageauthoritative" gorm:"column:averageauthoritative"`
	Headlanecode             *int         `json:"headlanecode" gorm:"column:headlanecode"`
	Specialvehicle           *int         `json:"specialvehicle" gorm:"column:specialvehicle"`
	Carlength                *int         `json:"carlength" gorm:"column:carlength"`
	Resulttype               *string      `json:"resulttype" gorm:"column:resulttype"`
	Carhight                 *int         `json:"carhight" gorm:"column:carhight"`
	Carmodelscode            *int         `json:"carmodelscode" gorm:"column:carmodelscode"`
	Carmodels                *string      `json:"carmodels" gorm:"column:carmodels"`
	Laneposition             *string      `json:"laneposition" gorm:"column:laneposition"`
	Firstauthoritative       *int         `json:"firstauthoritative" gorm:"column:firstauthoritative"`
	Tailplateimageheight     *int         `json:"tailplateimageheight" gorm:"column:tailplateimageheight"`
	Axlecount                *int         `json:"axlecount" gorm:"column:axlecount"`
	Plateimagewidth          *int         `json:"plateimagewidth" gorm:"column:plateimagewidth"`
	Specialclass             *string      `json:"specialclass" gorm:"column:specialclass"`
	Tailplatenumber          *string      `json:"tailplatenumber" gorm:"column:tailplatenumber"`
	Tailimage                *string      `json:"tailimage" gorm:"column:tailimage"`
	Sidecapturetimeunix      *int64       `json:"sidecapturetimeunix" gorm:"column:sidecapturetimeunix"`
	Sidecapturetime          *dateOnly    `json:"sidecapturetime" gorm:"column:sidecapturetime"`
	Sidelanecode             *int         `json:"sidelanecode" gorm:"column:sidelanecode"`
	Wheelbase                *int         `json:"wheelbase" gorm:"column:wheelbase"`
	Attached                 *string      `json:"attached" gorm:"column:attached"`
	Wheelcount               *int         `json:"wheelcount" gorm:"column:wheelcount"`
	Guid                     *string      `json:"guid" gorm:"column:guid"`
	Sideimagewidth           *int         `json:"sideimagewidth" gorm:"column:sideimagewidth"`
	Plateimageheight         *int         `json:"plateimageheight" gorm:"column:plateimageheight"`
	Datasource               *string      `json:"datasource" gorm:"column:datasource"`
	Carclass                 *string      `json:"carclass" gorm:"column:carclass"`
	Gantryid                 *string      `json:"gantryid" gorm:"column:gantryid"`
	Smallsideimage           *string      `json:"smallsideimage" gorm:"column:smallsideimage"`
	Headimageheight          *int         `json:"headimageheight" gorm:"column:headimageheight"`
	Sidescenetypecode        *int         `json:"sidescenetypecode" gorm:"column:sidescenetypecode"`
	Sidescenetype            *string      `json:"sidescenetype" gorm:"column:sidescenetype"`
	Tailimagewidth           *int         `json:"tailimagewidth" gorm:"column:tailimagewidth"`
	Envstate                 *string      `json:"envstate" gorm:"column:envstate"`
	Headscenetypecode        *int         `json:"headscenetypecode" gorm:"column:headscenetypecode"`
	Headscenetype            *string      `json:"headscenetype" gorm:"column:headscenetype"`
	Sidedrivingdirectioncode *int         `json:"sidedrivingdirectioncode" gorm:"column:sidedrivingdirectioncode"`
	Sidedrivingdirection     *string      `json:"sidedrivingdirection" gorm:"column:sidedrivingdirection"`
	Sideimageheight          *int         `json:"sideimageheight" gorm:"column:sideimageheight"`
	Speed                    *string      `json:"speed" gorm:"column:speed"`
	Tailplateimage           *string      `json:"tailplateimage" gorm:"column:tailplateimage"`
	Headdrivingdirectioncode *int         `json:"headdrivingdirectioncode" gorm:"column:headdrivingdirectioncode"`
	Headdrivingdirection     *string      `json:"headdrivingdirection" gorm:"column:headdrivingdirection"`
	Cartype                  *string      `json:"cartype" gorm:"column:cartype"`
	Plateimage               *string      `json:"plateimage" gorm:"column:plateimage"`
	Changelane               *string      `json:"changelane" gorm:"column:changelane"`
	Sideimage                *string      `json:"sideimage" gorm:"column:sideimage"`
	Tailplateposition        *string      `json:"tailplateposition" gorm:"column:tailplateposition"`
	Headimagewidth           *int         `json:"headimagewidth" gorm:"column:headimagewidth"`
	Headimage                *string      `json:"headimage" gorm:"column:headimage"`
	Carweight                *int         `json:"carweight" gorm:"column:carweight"`
	Tailimageheight          *int         `json:"tailimageheight" gorm:"column:tailimageheight"`
	Devicecode               *string      `json:"devicecode" gorm:"column:devicecode"`
	Platenumber              *string      `json:"platenumber" gorm:"column:platenumber"`
	Tailplatecolorcode       *int         `json:"tailplatecolorcode" gorm:"column:tailplatecolorcode"`
	Tailplatecolor           *string      `json:"tailplatecolor" gorm:"column:tailplatecolor"`
	Uploadtimeunix           *int64       `json:"uploadtimeunix" gorm:"column:uploadtimeunix"`
	Uploadtime               *dateOnly    `json:"uploadtime" gorm:"column:uploadtime"`
	Impostoraxlecount        *int         `json:"impostoraxlecount" gorm:"column:impostoraxlecount"`
	Taillanecode             *int         `json:"taillanecode" gorm:"column:taillanecode"`
	Siteid                   *int         `json:"siteid" gorm:"column:siteid"`
	Headcapturetimeunix      *int64       `json:"headcapturetimeunix" gorm:"column:headcapturetimeunix"`
	Headcapturetime          *dateOnly    `json:"headcapturetime" gorm:"column:headcapturetime"`
	Plateposition            *string      `json:"plateposition" gorm:"column:plateposition"`
	Tailplateimagewidth      *int         `json:"tailplateimagewidth" gorm:"column:tailplateimagewidth"`
	Loadtime                 *isoDateTime `json:"loadtime" gorm:"column:loadtime"`
	Gradelevel               *int         `json:"gradelevel" gorm:"column:gradelevel"`
	Datauuid                 *string      `json:"datauuid" gorm:"column:datauuid"`
	Reserve1                 *string      `json:"reserve1" gorm:"column:reserve1"`
	Reserve2                 *string      `json:"reserve2" gorm:"column:reserve2"`
	Reserve3                 *string      `json:"reserve3" gorm:"column:reserve3"`
}

// odsRtSzdnSnapshotFlowStationcaptureAddcode 对应收费站抓拍。
type odsRtSzdnSnapshotFlowStationcaptureAddcode struct {
	BigID             *int64    `json:"bigId" gorm:"column:big_id"`
	Datasource        *string   `json:"datasource" gorm:"column:datasource"`
	Cameratype        *string   `json:"cameratype" gorm:"column:cameratype"`
	Deviceid          *string   `json:"deviceid" gorm:"column:deviceid"`
	Deviceip          *string   `json:"deviceip" gorm:"column:deviceip"`
	Tollcode          *string   `json:"tollcode" gorm:"column:tollcode"`
	Tollname          *string   `json:"tollname" gorm:"column:tollname"`
	Orgcode           *int64    `json:"orgcode" gorm:"column:orgcode"`
	Siteid            *int64    `json:"siteid" gorm:"column:siteid"`
	Laneid            *int      `json:"laneid" gorm:"column:laneid"`
	Snapshottimeunix  *int64    `json:"snapshottimeunix" gorm:"column:snapshottimeunix"`
	Snapshottime      *dateOnly `json:"snapshottime" gorm:"column:snapshottime"`
	Receivedtimeunix  *int64    `json:"receivedtimeunix" gorm:"column:receivedtimeunix"`
	Receivedtime      *dateOnly `json:"receivedtime" gorm:"column:receivedtime"`
	Platenumber       *string   `json:"platenumber" gorm:"column:platenumber"`
	Platecolorcode    *int      `json:"platecolorcode" gorm:"column:platecolorcode"`
	Platecolor        *string   `json:"platecolor" gorm:"column:platecolor"`
	Platetypecode     *int      `json:"platetypecode" gorm:"column:platetypecode"`
	Platetype         *string   `json:"platetype" gorm:"column:platetype"`
	Plateconfidence   *int      `json:"plateconfidence" gorm:"column:plateconfidence"`
	Carbrand          *string   `json:"carbrand" gorm:"column:carbrand"`
	Carcolorcode      *int      `json:"carcolorcode" gorm:"column:carcolorcode"`
	Carcolor          *string   `json:"carcolor" gorm:"column:carcolor"`
	Cartypecode       *int      `json:"cartypecode" gorm:"column:cartypecode"`
	Cartype           *string   `json:"cartype" gorm:"column:cartype"`
	Cardirectioncode  *int      `json:"cardirectioncode" gorm:"column:cardirectioncode"`
	Cardirection      *string   `json:"cardirection" gorm:"column:cardirection"`
	Snappicturepath   *string   `json:"snappicturepath" gorm:"column:snappicturepath"`
	Loadtime          *dateOnly `json:"loadtime" gorm:"column:loadtime"`
	Gradelevel        *int      `json:"gradelevel" gorm:"column:gradelevel"`
	Datauuid          *string   `json:"datauuid" gorm:"column:datauuid"`
	Maindirection     *string   `json:"maindirection" gorm:"column:maindirection"`
	Maindirectionname *string   `json:"maindirectionname" gorm:"column:maindirectionname"`
	Reserve3          *string   `json:"reserve3" gorm:"column:reserve3"`
}

// odsLwzxsfsjFeeStationEnter01 对应收费站入口数据（@TableId big_id, INPUT）。
type odsLwzxsfsjFeeStationEnter01 struct {
	BigID                *int64    `json:"bigId" gorm:"column:big_id"`
	Cardid               *string   `json:"cardid" gorm:"column:cardid"`
	Electricalpercentage *int64    `json:"electricalpercentage" gorm:"column:electricalpercentage"`
	Enaxlecount          *int64    `json:"enaxlecount" gorm:"column:enaxlecount"`
	Entime               *dateOnly `json:"entime" gorm:"column:entime"`
	Entolllanehex        *string   `json:"entolllanehex" gorm:"column:entolllanehex"`
	Entolllaneid         *string   `json:"entolllaneid" gorm:"column:entolllaneid"`
	Entollstationid      *string   `json:"entollstationid" gorm:"column:entollstationid"`
	Enweight             *float64  `json:"enweight" gorm:"column:enweight"`
	Identifyvehicleid    *string   `json:"identifyvehicleid" gorm:"column:identifyvehicleid"`
	Lanetype             *string   `json:"lanetype" gorm:"column:lanetype"`
	Mediatype            *string   `json:"mediatype" gorm:"column:mediatype"`
	Operid               *string   `json:"operid" gorm:"column:operid"`
	Operationmedia       *string   `json:"operationmedia" gorm:"column:operationmedia"`
	Params               *string   `json:"params" gorm:"column:params"`
	Passid               *string   `json:"passid" gorm:"column:passid"`
	Receivetime          *dateOnly `json:"receivetime" gorm:"column:receivetime"`
	Shift                *string   `json:"shift" gorm:"column:shift"`
	Signstatus           *string   `json:"signstatus" gorm:"column:signstatus"`
	Specialtype          *string   `json:"specialtype" gorm:"column:specialtype"`
	Tac                  *string   `json:"tac" gorm:"column:tac"`
	Terminalno           *string   `json:"terminalno" gorm:"column:terminalno"`
	Terminaltransno      *string   `json:"terminaltransno" gorm:"column:terminaltransno"`
	Transfee             *float64  `json:"transfee" gorm:"column:transfee"`
	Transtype            *string   `json:"transtype" gorm:"column:transtype"`
	Vcount               *int64    `json:"vcount" gorm:"column:vcount"`
	Vehicleclass         *string   `json:"vehicleclass" gorm:"column:vehicleclass"`
	Vehicleid            *string   `json:"vehicleid" gorm:"column:vehicleid"`
	Vehiclesign          *string   `json:"vehiclesign" gorm:"column:vehiclesign"`
	Vehiclesignid        *string   `json:"vehiclesignid" gorm:"column:vehiclesignid"`
	Vehicletype          *string   `json:"vehicletype" gorm:"column:vehicletype"`
	LoadTime             *dateOnly `json:"loadTime" gorm:"column:load_time"`
	GradeLevel           *string   `json:"gradeLevel" gorm:"column:grade_level"`
	Cid                  *string   `json:"cid" gorm:"column:cid"`
}

// odsSzdnProvinceBorderVehicleWeightNewstructure 对应省界称重。
//
// JAVA 对照: 列名是 camelCase（dataSource），@TableId 是 datauuid，
// 而 XML 的 selectXxxById 过滤的是 dataSource（生成器笔误，照抄）。
type odsSzdnProvinceBorderVehicleWeightNewstructure struct {
	DataSource         *string   `json:"dataSource" gorm:"column:dataSource"`
	DataType           *string   `json:"dataType" gorm:"column:dataType"`
	PlateNo            *string   `json:"plateNo" gorm:"column:plateNo"`
	SiteID             *string   `json:"siteId" gorm:"column:siteId"`
	Location           *string   `json:"location" gorm:"column:location"`
	DriveNo            *int64    `json:"driveNo" gorm:"column:driveNo"`
	PlateColor         *string   `json:"plateColor" gorm:"column:plateColor"`
	PlateColorCode     *string   `json:"plateColorCode" gorm:"column:plateColorCode"`
	PlateType          *string   `json:"plateType" gorm:"column:plateType"`
	PlateTypeCode      *string   `json:"plateTypeCode" gorm:"column:plateTypeCode"`
	VehicleColor       *string   `json:"vehicleColor" gorm:"column:vehicleColor"`
	VehicleColorCode   *string   `json:"vehicleColorCode" gorm:"column:vehicleColorCode"`
	VehicleType        *string   `json:"vehicleType" gorm:"column:vehicleType"`
	VehicleTypeCode    *string   `json:"vehicleTypeCode" gorm:"column:vehicleTypeCode"`
	VehicleSpeed       *int64    `json:"vehicleSpeed" gorm:"column:vehicleSpeed"`
	IsOverweight       *int64    `json:"isOverweight" gorm:"column:isOverweight"`
	AxleNum            *int64    `json:"axleNum" gorm:"column:axleNum"`
	OverWeight         *int64    `json:"overWeight" gorm:"column:overWeight"`
	VehicleWeight      *int64    `json:"vehicleWeight" gorm:"column:vehicleWeight"`
	LimitWeight        *int64    `json:"limitWeight" gorm:"column:limitWeight"`
	CheckTimeUnix      *int64    `json:"checkTimeUnix" gorm:"column:checkTimeUnix"`
	CheckTime          *dateOnly `json:"checkTime" gorm:"column:checkTime"`
	AxleModel          *int64    `json:"axleModel" gorm:"column:axleModel"`
	LoadRate           *int64    `json:"loadRate" gorm:"column:loadRate"`
	AxleArray          *string   `json:"axleArray" gorm:"column:axleArray"`
	WeighingImagesArry *string   `json:"weighingImagesArry" gorm:"column:weighingImagesArry"`
	LoadTime           *dateOnly `json:"loadTime" gorm:"column:load_time"`
	GradeLevel         *int64    `json:"gradeLevel" gorm:"column:grade_level"`
	Datauuid           *string   `json:"datauuid" gorm:"column:datauuid"`
	Reserve1           *string   `json:"reserve1" gorm:"column:reserve1"`
	Reserve2           *string   `json:"reserve2" gorm:"column:reserve2"`
	Reserve3           *string   `json:"reserve3" gorm:"column:reserve3"`
}
