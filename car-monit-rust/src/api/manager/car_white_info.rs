// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarWhiteInfoController.java
//       ruoyi-system/src/main/resources/mapper/manager/car_white_infoMapper.xml
// 职责: 白名单 CRUD 与导出（BasePlusEntity 通用逻辑）。
// 对应关系: manager_crud! 宏生成 list/export/get/add/edit/remove。

use crate::api::support::FieldFormat;

crate::manager_crud! {
    route: "/manager/whiteinfo",
    perm: "manager:whiteinfo",
    title: "白名单",
    class: "com.ruoyi.web.controller.manager.CarWhiteInfoController",
    sheet: "白名单数据",
    table: "car_white_info",
    select: "t.id, t.plate_color, t.car_no, t.car_type, t.car_vehicle, t.car_num, t.file_ids, t.back_col1, t.back_col2, t.remark, t.status, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id, null as carNoQuery, concat(sd.dept_name, ' ', su.nick_name) as createInfo, \
             null as createTimeStr",
    from: "from car_white_info t left join sys_user su on su.user_id = t.create_by \
           left join sys_dept sd on t.eps_id = sd.dept_id",
    order: "t.create_time desc,t.id",
    dates: [
        ("inTime", FieldFormat::DateOnly),
        ("outTime", FieldFormat::DateOnly),
    ],
    get_info_nulls: ["createInfo"],
    binary: true,
    filters: [
        Filter::eq("id", "t.id"),
        Filter::eq("plateColor", "t.plate_color"),
        Filter::eq("carNo", "t.car_no"),
        Filter::like("carNoQuery", "t.car_no"),
        Filter::eq("carType", "t.car_type"),
        Filter::eq("carVehicle", "t.car_vehicle"),
        Filter::eq("carNum", "t.car_num"),
        Filter::eq("fileIds", "t.file_ids"),
        Filter::eq("backCol1", "t.back_col1"),
        Filter::eq("backCol2", "t.back_col2"),
        Filter::eq("status", "t.status"),
        Filter::eq("sort", "t.sort"),
        Filter::eq("epsId", "t.eps_id"),
        Filter::eq("tenantId", "t.tenant_id"),
        Filter::eq("createBy", "t.create_by"),
    ],
    headers: ["车牌颜色", "车牌号", "车型", "车种", "轴数", "相关附件(附件ids)", "备用字段1", "备用字段2", "状态", "备注"],
    fields: ["plateColor", "carNo", "carType", "carVehicle", "carNum", "fileIds", "backCol1", "backCol2", "status", "remark"],
}
