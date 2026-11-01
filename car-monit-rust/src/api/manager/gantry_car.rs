// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/GantryCarController.java
//       ruoyi-system/src/main/resources/mapper/manager/gantry_carMapper.xml
// 职责: 门架车辆 CRUD 与导出（BasePlusEntity 通用逻辑）。
// 对应关系: manager_crud! 宏生成 list/export/get/add/edit/remove。

use crate::api::support::FieldFormat;

crate::manager_crud! {
    route: "/manager/gantrycar",
    perm: "manager:gantrycar",
    title: "门架车辆",
    class: "com.ruoyi.web.controller.manager.GantryCarController",
    sheet: "门架车辆数据",
    table: "gantry_car",
    select: "t.id, t.car_no, t.car_type, t.car_vehicle, t.car_num, t.in_station_id, t.in_station, t.in_time, t.gantry_station_id, t.gantryt_station, t.gantry_time, t.file_ids, t.back_col1, t.back_col2, t.remark, t.status, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id, null as applyTime1, null as applyTime2, null as createTimeStr",
    from: "from gantry_car t",
    order: "t.create_time desc,t.id",
    dates: [
        ("inTime", FieldFormat::DateOnly),
        ("gantryTime", FieldFormat::DateOnly),
    ],
    binary: true,
    filters: [
        Filter::eq("id", "t.id"),
        Filter::eq("carNo", "t.car_no"),
        Filter::eq("carType", "t.car_type"),
        Filter::eq("carVehicle", "t.car_vehicle"),
        Filter::eq("carNum", "t.car_num"),
        Filter::eq("inStationId", "t.in_station_id"),
        Filter::eq("inStation", "t.in_station"),
        Filter::eq("inTime", "t.in_time"),
        Filter::eq("gantryStationId", "t.gantry_station_id"),
        Filter::eq("gantrytStation", "t.gantryt_station"),
        Filter::eq("gantryTime", "t.gantry_time"),
        Filter::eq("fileIds", "t.file_ids"),
        Filter::eq("backCol1", "t.back_col1"),
        Filter::eq("backCol2", "t.back_col2"),
        Filter::eq("status", "t.status"),
        Filter::eq("sort", "t.sort"),
        Filter::eq("epsId", "t.eps_id"),
        Filter::eq("tenantId", "t.tenant_id"),
        Filter::eq("createBy", "t.create_by"),
        Filter::raw("applyTime1", " and t.create_time >= STR_TO_DATE(?, '%Y-%m-%d')"),
        Filter::raw("applyTime2", " and t.create_time < date_add(STR_TO_DATE(?, '%Y-%m-%d'), interval 1 day)"),
    ],
    headers: ["车牌号", "车型", "车种", "轴数", "入口站id", "入口站", "通行时间", "门架id", "门架名称", "经过时间", "图片(附件ids)", "备用字段1", "备用字段2", "状态", "备注"],
    fields: ["carNo", "carType", "carVehicle", "carNum", "inStationId", "inStation", "inTime", "gantryStationId", "gantrytStation", "gantryTime", "fileIds", "backCol1", "backCol2", "status", "remark"],
}
