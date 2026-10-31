// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarQueryLogController.java
//       ruoyi-system/src/main/resources/mapper/manager/car_query_logMapper.xml
// 职责: 查询日志 CRUD 与导出（BasePlusEntity 通用逻辑）。
// 对应关系: manager_crud! 宏生成 list/export/get/add/edit/remove。

crate::manager_crud! {
    route: "/manager/querylog",
    perm: "manager:querylog",
    title: "查询日志",
    class: "com.ruoyi.web.controller.manager.CarQueryLogController",
    sheet: "查询日志数据",
    table: "car_query_log",
    select: "t.id, t.user_id, t.user_name, t.user_ip, t.model_type, t.menu_point, t.query_condition, t.back_col1, t.back_col2, t.remark, t.status, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id",
    from: "from car_query_log t",
    order: "t.create_time desc,t.id",
    filters: [
        Filter::eq("id", "t.id"),
        Filter::eq("userId", "t.user_id"),
        Filter::like("userName", "t.user_name"),
        Filter::eq("userIp", "t.user_ip"),
        Filter::eq("modelType", "t.model_type"),
        Filter::eq("menuPoint", "t.menu_point"),
        Filter::eq("createBy", "t.create_by"),
        Filter::raw("applyTime1", " and t.create_time >= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')"),
        Filter::raw("applyTime2", " and t.create_time <= STR_TO_DATE(?, '%Y-%m-%d %H:%i:%s')"),
    ],
    headers: ["用户ID", "用户名称", "用户IP", "模块菜单(1轨迹单2门架拍识3门架交易流水)", "模块功能(1查看2导出)", "查询条件", "备注"],
    fields: ["userId", "userName", "userIp", "modelType", "menuPoint", "queryCondition", "remark"],
}
