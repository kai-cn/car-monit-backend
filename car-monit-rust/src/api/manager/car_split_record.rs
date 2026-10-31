// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarSplitRecordController.java
//       ruoyi-system/src/main/resources/mapper/manager/car_split_recordMapper.xml
// 职责: 拆分记录 CRUD 与导出（BasePlusEntity 通用逻辑）。
// 对应关系: manager_crud! 宏生成 list/export/get/add/edit/remove。

crate::manager_crud! {
    route: "/manager/splitrecord",
    perm: "manager:splitrecord",
    title: "拆分记录",
    class: "com.ruoyi.web.controller.manager.CarSplitRecordController",
    sheet: "拆分记录数据",
    table: "car_split_record",
    select: "t.id, t.car_id, t.car_no, t.car_type, t.car_vehicle, t.pass_type, t.in_station_id, t.in_station, t.in_time, t.out_station_id, t.out_station, t.out_time, t.amount, t.back_col1, t.back_col2, t.status, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id",
    from: "from car_split_record t",
    order: "t.create_time desc,t.id",
    filters: [
        Filter::eq("id", "t.id"),
        Filter::eq("carId", "t.car_id"),
        Filter::eq("carNo", "t.car_no"),
        Filter::eq("carType", "t.car_type"),
        Filter::eq("carVehicle", "t.car_vehicle"),
        Filter::eq("passType", "t.pass_type"),
        Filter::eq("inStationId", "t.in_station_id"),
        Filter::eq("inStation", "t.in_station"),
        Filter::eq("inTime", "t.in_time"),
        Filter::eq("outStationId", "t.out_station_id"),
        Filter::eq("outStation", "t.out_station"),
        Filter::eq("outTime", "t.out_time"),
        Filter::eq("amount", "t.amount"),
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
    headers: ["车辆id", "车牌号", "车型", "车种", "通信标识", "入口站id", "入口站", "入口时间", "出口站id", "出口站", "出口时间", "拆分金额", "备用字段1", "备用字段2", "状态"],
    fields: ["carId", "carNo", "carType", "carVehicle", "passType", "inStationId", "inStation", "inTime", "outStationId", "outStation", "outTime", "amount", "backCol1", "backCol2", "status"],
}
