// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/GantryTradeInfoController.java
//       ruoyi-system/src/main/resources/mapper/manager/gantry_trade_infoMapper.xml
// 职责: 门架交易 CRUD 与导出（BasePlusEntity 通用逻辑）。
// 对应关系: manager_crud! 宏生成 list/export/get/add/edit/remove。

crate::manager_crud! {
    route: "/manager/gantrytrade",
    perm: "manager:gantrytrade",
    title: "门架交易",
    class: "com.ruoyi.web.controller.manager.GantryTradeInfoController",
    sheet: "门架交易数据",
    table: "gantry_trade_info",
    select: "t.id, t.car_no, t.car_type, t.car_vehicle, t.car_num, t.in_station_id, t.in_station, t.in_time, t.out_station_id, t.out_station, t.out_time, t.charge_type, t.amount, t.back_col1, t.back_col2, t.remark, t.status, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id",
    from: "from gantry_trade_info t",
    order: "t.create_time desc,t.id",
    filters: [
        Filter::eq("id", "t.id"),
        Filter::eq("carNo", "t.car_no"),
        Filter::eq("carType", "t.car_type"),
        Filter::eq("carVehicle", "t.car_vehicle"),
        Filter::eq("carNum", "t.car_num"),
        Filter::eq("inStationId", "t.in_station_id"),
        Filter::eq("inStation", "t.in_station"),
        Filter::eq("inTime", "t.in_time"),
        Filter::eq("outStationId", "t.out_station_id"),
        Filter::eq("outStation", "t.out_station"),
        Filter::eq("outTime", "t.out_time"),
        Filter::eq("chargeType", "t.charge_type"),
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
    headers: ["车牌号", "车型", "车种", "轴数", "入门架id", "入门架", "入门时间", "出口门架id", "出口门架", "出口时间", "交易类型", "收费金额", "备用字段1", "备用字段2", "状态", "备注"],
    fields: ["carNo", "carType", "carVehicle", "carNum", "inStationId", "inStation", "inTime", "outStationId", "outStation", "outTime", "chargeType", "amount", "backCol1", "backCol2", "status", "remark"],
}
