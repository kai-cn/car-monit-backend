// 由 scripts/gen_crud_spec.py 生成（area=manager）。
// 重新生成: python scripts/gen_crud_spec.py --area manager
//
// 只覆盖同构 CRUD：list / export / getInfo / add / edit / remove。
// 非 CRUD 接口、唯一性校验、tenant 过滤、软删除、外部服务依赖等仍由手写控制器负责
// （src/cm/web/controller/**）。解析不到的控制器整只跳过，见生成器输出。
//
// 每个实体的 Spec 通过 spec<Entity>() 暴露（声明见 ManagerCrudSpecs.hpp），
// 手写控制器可以复用同一份列定义，避免把几十个字段再抄一遍。
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"
#include "cm/web/specs/ManagerCrudSpecs.hpp"

namespace cm::web::crud {

const Spec& specBussTest() {
    static const Spec s = [] {
        Spec s;
        s.table = "buss_test";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"billName", "bill_name", Fmt::Str, Cond::Like, "业务名称", false, false, true, true},
            {"billType", "bill_type", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"amount", "amount", Fmt::Double, Cond::Eq, "金额", false, false, true, true},
            {"deptId", "dept_id", Fmt::Long, Cond::Eq, "部门id", false, false, true, true},
            {"userId", "user_id", Fmt::Long, Cond::Eq, "人员id", false, false, true, true},
            {"applyTime", "apply_time", Fmt::DateYmd, Cond::Eq, "申请时间", false, false, true, true},
            {"applyTime2", "apply_time2", Fmt::DateYmd, Cond::Eq, "时间时分秒", false, false, true, true},
            {"fileIds", "file_ids", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"flowKey", "flow_key", Fmt::Str, Cond::Eq, "流程key", false, false, true, true},
            {"flowRuid", "flow_ruid", Fmt::Str, Cond::Eq, "流程实例ID", false, false, true, true},
            {"flowApplyOid", "flow_apply_oid", Fmt::Str, Cond::Eq, "流程申请ID", false, false, true, true},
            {"flowStatus", "flow_status", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"shTime", "sh_time", Fmt::DateYmd, Cond::Eq, "审核时间", false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "业务测试";
        return s;
    }();
    return s;
}

const Spec& specCarAduitFree() {
    static const Spec s = [] {
        Spec s;
        s.table = "car_aduit_free";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"confirmId", "confirm_id", Fmt::Str, Cond::Eq, "确认补缴id", false, false, true, true},
            {"carId", "car_id", Fmt::Str, Cond::Eq, "车辆id", false, false, true, true},
            {"carNo", "car_no", Fmt::Str, Cond::Like, "车牌号", false, false, true, true},
            {"carType", "car_type", Fmt::Str, Cond::Eq, "车型", false, false, true, true},
            {"carVehicle", "car_vehicle", Fmt::Str, Cond::Eq, "车种", false, false, true, true},
            {"orgId", "org_id", Fmt::Str, Cond::Eq, "处理单位id", false, false, true, true},
            {"orgName", "org_name", Fmt::Str, Cond::Like, "处理单位", false, false, true, true},
            {"userIds", "user_ids", Fmt::Str, Cond::Eq, "处理人员ids", false, false, true, true},
            {"userNames", "user_names", Fmt::Str, Cond::Eq, "处理人员", false, false, true, true},
            {"amount", "amount", Fmt::Double, Cond::Eq, "拆分金额", false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
            {"applyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.create_time,t.id";
        s.excelSheetName = "补缴处理";
        return s;
    }();
    return s;
}

const Spec& specCarConfimFree() {
    static const Spec s = [] {
        Spec s;
        s.table = "car_confim_free";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"carId", "car_id", Fmt::Str, Cond::Eq, "车辆id", false, false, true, true},
            {"carNo", "car_no", Fmt::Str, Cond::Eq, "车牌号", false, false, true, true},
            {"carType", "car_type", Fmt::Str, Cond::Eq, "车型", false, false, true, true},
            {"carVehicle", "car_vehicle", Fmt::Str, Cond::Eq, "车种", false, false, true, true},
            {"linkName", "link_name", Fmt::Str, Cond::Like, "司机名称", false, false, true, true},
            {"linkPhone", "link_phone", Fmt::Str, Cond::Eq, "联系方式", false, false, true, true},
            {"orgId", "org_id", Fmt::Str, Cond::Eq, "录入单位id", false, false, true, true},
            {"orgName", "org_name", Fmt::Str, Cond::Like, "录入单位", false, false, true, true},
            {"userIds", "user_ids", Fmt::Str, Cond::Eq, "录入人员ids", false, false, true, true},
            {"userNames", "user_names", Fmt::Str, Cond::Eq, "录入人员", false, false, true, true},
            {"amount", "amount", Fmt::Double, Cond::Eq, "拆分金额", false, false, true, true},
            {"aduitAmount", "aduit_amount", Fmt::Double, Cond::None, "处理金额", false, false, true, true},
            {"exceptIds", "except_ids", Fmt::Str, Cond::FindInSetCol, "异常流水ids", false, false, true, true, "id"},
            {"escapedTypes", "escaped_types", Fmt::Str, Cond::Eq, "逃费类型s", false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "比例", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
            {"carAduitFreeList", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"carExceptRecordList", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"totalAmount", nullptr, Fmt::Double, Cond::None, "应缴金额", false, false, false, false, nullptr, nullptr},
            {"chargeAmount", nullptr, Fmt::Double, Cond::None, "收费金额", false, false, false, false, nullptr, nullptr},
            {"difAmount", nullptr, Fmt::Double, Cond::None, "差额", false, false, false, false, nullptr, nullptr},
            {"applyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime3", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime4", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"carNoQuery", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"confimFreeNum", nullptr, Fmt::Int, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"confimFreeAmount", nullptr, Fmt::Double, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"escapedType", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"comfimFreeType", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"number", nullptr, Fmt::Int, Cond::None, nullptr, false, false, false, false, nullptr, "0"},
            {"escapedAmount", nullptr, Fmt::Double, Cond::None, nullptr, false, false, false, false, nullptr, "0"},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "确认补缴";
        return s;
    }();
    return s;
}

const Spec& specCarExceptRecord() {
    static const Spec s = [] {
        Spec s;
        s.table = "car_except_record";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"carId", "car_id", Fmt::Str, Cond::Eq, "车辆id", false, false, true, true},
            {"carNo", "car_no", Fmt::Str, Cond::Eq, "车牌号", false, false, true, true},
            {"carType", "car_type", Fmt::Str, Cond::Eq, "车型", false, false, true, true},
            {"carVehicle", "car_vehicle", Fmt::Str, Cond::Eq, "车种", false, false, true, true},
            {"carNum", "car_num", Fmt::Long, Cond::Eq, "轴数", false, false, true, true},
            {"passType", "pass_type", Fmt::Str, Cond::Eq, "通行标识", false, false, true, true},
            {"inStationId", "in_station_id", Fmt::Str, Cond::Eq, "入口站id", false, false, true, true},
            {"inStation", "in_station", Fmt::Str, Cond::Like, "入口站", false, false, true, true},
            {"inTime", "in_time", Fmt::DateYmdHms, Cond::Eq, "入口时间", false, false, true, true},
            {"outStationId", "out_station_id", Fmt::Str, Cond::Eq, "出口站id", false, false, true, true},
            {"outStation", "out_station", Fmt::Str, Cond::Like, "出口站", false, false, true, true},
            {"outTime", "out_time", Fmt::DateYmdHms, Cond::Eq, "出口时间", false, false, true, true},
            {"totalAmount", "total_amount", Fmt::Double, Cond::Eq, "应缴金额", false, false, true, true},
            {"chargeAmount", "charge_amount", Fmt::Double, Cond::Eq, "收费金额", false, false, true, true},
            {"difAmount", "dif_amount", Fmt::Double, Cond::Eq, "差额", false, false, true, true},
            {"escapedType", "escaped_type", Fmt::Str, Cond::Eq, "逃费类型", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"applyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime3", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime4", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"createTimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"orgId", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"supplementaryStatus", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, "\"0\""},
            {"exceptIds", nullptr, Fmt::Str, Cond::FindInSetCol, "异常流水ids", false, false, false, false, "id", nullptr},
            {"carNoQuery", nullptr, Fmt::Str, Cond::None, "车俩查询", false, false, false, false, nullptr, nullptr},
            {"createInfo", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"exceptNum", nullptr, Fmt::Int, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"exceptAmount", nullptr, Fmt::Double, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"inTimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"outTimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "异常车辆流水";
        return s;
    }();
    return s;
}

const Spec& specCarFeeRecord() {
    static const Spec s = [] {
        Spec s;
        s.table = "car_fee_record";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"carId", "car_id", Fmt::Str, Cond::Eq, "车辆id", false, false, true, true},
            {"carNo", "car_no", Fmt::Str, Cond::Eq, "车牌号", false, false, true, true},
            {"carType", "car_type", Fmt::Str, Cond::Eq, "车型", false, false, true, true},
            {"carVehicle", "car_vehicle", Fmt::Str, Cond::Eq, "车种", false, false, true, true},
            {"inStationId", "in_station_id", Fmt::Str, Cond::Eq, "入口站id", false, false, true, true},
            {"inStation", "in_station", Fmt::Str, Cond::Eq, "入口站", false, false, true, true},
            {"inTime", "in_time", Fmt::DateYmd, Cond::Eq, "入口时间", false, false, true, true},
            {"outStationId", "out_station_id", Fmt::Str, Cond::Eq, "出口站id", false, false, true, true},
            {"outStation", "out_station", Fmt::Str, Cond::Eq, "出口站", false, false, true, true},
            {"outTime", "out_time", Fmt::DateYmd, Cond::Eq, "出口时间", false, false, true, true},
            {"chargeType", "charge_type", Fmt::Str, Cond::Eq, "交易类型", false, false, true, true},
            {"amount", "amount", Fmt::Double, Cond::Eq, "收费金额", false, false, true, true},
            {"exceptId", "except_id", Fmt::Str, Cond::Eq, "异常流水id", false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
            {"applyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "收费流水";
        return s;
    }();
    return s;
}

const Spec& specCarInfo() {
    static const Spec s = [] {
        Spec s;
        s.table = "car_info";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0' and t.status = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"carNo", "car_no", Fmt::Str, Cond::Eq, "车牌号", false, false, true, true},
            {"carType", "car_type", Fmt::Str, Cond::Eq, "车型", false, false, true, true},
            {"carVehicle", "car_vehicle", Fmt::Str, Cond::Eq, "车种", false, false, true, true},
            {"carNum", "car_num", Fmt::Long, Cond::Eq, "轴数", false, false, true, true},
            {"escapedType", "escaped_type", Fmt::Str, Cond::Like, "逃费类型", false, false, true, true},
            {"escapedTypeName", "escaped_type_name", Fmt::Str, Cond::Like, "逃费类型名称", false, false, true, true},
            {"escapedAmount", "escaped_amount", Fmt::Double, Cond::Eq, "逃费金额", false, false, true, true},
            {"escapedNum", "escaped_num", Fmt::Long, Cond::Eq, nullptr, false, false, true, true},
            {"returnAmount", "return_amount", Fmt::Double, Cond::Eq, "累计追缴金额", false, false, true, true},
            {"totalAmount", "total_amount", Fmt::Double, Cond::Eq, "应缴金额", false, false, true, true},
            {"chargeAmount", "charge_amount", Fmt::Double, Cond::Eq, "收费金额", false, false, true, true},
            {"difAmount", "dif_amount", Fmt::Double, Cond::Eq, "差额", false, false, true, true},
            {"auitOrgId", "auit_org_id", Fmt::Str, Cond::Eq, "处理单位id", false, false, true, true},
            {"auitOrgName", "auit_org_name", Fmt::Str, Cond::Like, "处理单位", false, false, true, true},
            {"isWhite", "is_white", Fmt::Str, Cond::Eq, "是否在白名单", false, false, true, true},
            {"whiteRemark", "white_remark", Fmt::Str, Cond::Eq, "白名单原因", false, false, true, true},
            {"fileIds", "file_ids", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"brand", "brand", Fmt::Str, Cond::Eq, "车辆品牌", false, false, true, true},
            {"plateColor", "plate_color", Fmt::Str, Cond::Eq, "车牌颜色", false, false, true, true},
            {"plateType", "plate_type", Fmt::Str, Cond::Eq, "车牌类型", false, false, true, true},
            {"carColor", "car_color", Fmt::Str, Cond::Eq, "车辆颜色", false, false, true, true},
            {"dataSource", "data_source", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"dataSourceName", "data_source_name", Fmt::Str, Cond::Like, "来源名称", false, false, true, true},
            {"lastPassTime", "last_pass_time", Fmt::DateYmd, Cond::Eq, "最后通行时间", false, false, true, true},
            {"lastPassPicture", "last_pass_picture", Fmt::Str, Cond::Eq, "最后通行图片", false, false, true, true},
            {"lastPassType", "last_pass_type", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"lastPassAddress", "last_pass_address", Fmt::Str, Cond::Eq, "最后通行地址", false, false, true, true},
            {"lastPassLongitude", "last_pass_longitude", Fmt::Str, Cond::Eq, "最后通行经度", false, false, true, true},
            {"lastPassLatitude", "last_pass_latitude", Fmt::Str, Cond::Eq, "最后通行维度", false, false, true, true},
            {"lastPassCardirection", "last_pass_cardirection", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"roadSectionId", "road_section_id", Fmt::Str, Cond::Eq, "管理中心路段id", false, false, true, true},
            {"sectionCode", "section_code", Fmt::Str, Cond::Eq, "所属路段编码", false, false, true, true},
            {"roadSectionName", "road_section_name", Fmt::Str, Cond::Like, "管理中心路段名称", false, false, true, true},
            {"nextPassTime", "next_pass_time", Fmt::DateYmd, Cond::Eq, "预计下一个通行时间", false, false, true, true},
            {"nextPassType", "next_pass_type", Fmt::Str, Cond::Eq, "预计下一个通行类型", false, false, true, true},
            {"nextPassAddress", "next_pass_address", Fmt::Str, Cond::Eq, "预计下一个通行地址", false, false, true, true},
            {"nextPassLongitude", "next_pass_longitude", Fmt::Str, Cond::Eq, "预计下一个通行经度", false, false, true, true},
            {"nextPassLatitude", "next_pass_latitude", Fmt::Str, Cond::Eq, "预计下一个通行维度", false, false, true, true},
            {"trackId", "track_id", Fmt::Str, Cond::None, "行驶轨迹id", false, false, true, true},
            {"trackJosn", "track_josn", Fmt::Str, Cond::None, "行驶轨迹josn", false, false, true, true},
            {"orgId", "org_id", Fmt::Str, Cond::Eq, "管理中心id", false, false, true, true},
            {"orgCode", "org_code", Fmt::Str, Cond::Eq, "所属管理中心机构编码", false, false, true, true},
            {"orgName", "org_name", Fmt::Str, Cond::Like, "管理中心名称", false, false, true, true},
            {"gantryCode", "gantry_code", Fmt::Str, Cond::Like, "门架编号", false, false, true, true},
            {"roadCode", "road_code", Fmt::Str, Cond::Like, "所属路线编码", false, false, true, true},
            {"roadName", "road_name", Fmt::Str, Cond::Like, "所属路线名称", false, false, true, true},
            {"tollCode", "toll_code", Fmt::Str, Cond::Like, "所属收费站编码", false, false, true, true},
            {"tollName", "toll_name", Fmt::Str, Cond::Like, "所属收费站名称", false, false, true, true},
            {"linkName", "link_name", Fmt::Str, Cond::Like, "司机名称", false, false, true, true},
            {"linkPhone", "link_phone", Fmt::Str, Cond::Eq, "联系方式", false, false, true, true},
            {"fwqbm", "fwqbm", Fmt::Str, Cond::Like, "服务区编码", false, false, true, true},
            {"fwqmc", "fwqmc", Fmt::Str, Cond::Eq, "服务区名称", false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
            {"applyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"carNoQuery", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"createTimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"createInfo", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"trailList", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"flag", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "车辆信息";
        return s;
    }();
    return s;
}

const Spec& specCarQueryLog() {
    static const Spec s = [] {
        Spec s;
        s.table = "car_query_log";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::None, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"userId", "user_id", Fmt::Str, Cond::Eq, "用户ID", false, false, true, true},
            {"userName", "user_name", Fmt::Str, Cond::Like, "用户名称", false, false, true, true},
            {"userIp", "user_ip", Fmt::Str, Cond::Eq, "用户IP", false, false, true, true},
            {"modelType", "model_type", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"menuPoint", "menu_point", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"queryCondition", "query_condition", Fmt::Str, Cond::None, "查询条件", false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::None, nullptr, false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::None, nullptr, false, false, true, true},
            {"status", "status", Fmt::Str, Cond::None, nullptr, false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
            {"applyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "查询日志";
        return s;
    }();
    return s;
}

const Spec& specCarRouteDetail() {
    static const Spec s = [] {
        Spec s;
        s.table = "car_route_detail";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"routeId", "route_id", Fmt::Str, Cond::Eq, "路线d", false, false, true, true},
            {"carId", "car_id", Fmt::Str, Cond::Eq, "车辆id", false, false, true, true},
            {"carNo", "car_no", Fmt::Str, Cond::Eq, "车牌号", false, false, true, true},
            {"dataSource", "data_source", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"dataSourceName", "data_source_name", Fmt::Str, Cond::Like, "来源名称", false, false, true, true},
            {"lastPassTime", "last_pass_time", Fmt::DateYmd, Cond::Eq, "最后通行时间", false, false, true, true},
            {"lastPassPicture", "last_pass_picture", Fmt::Str, Cond::Eq, "最后通行图片", false, false, true, true},
            {"lastPassType", "last_pass_type", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"lastPassAddress", "last_pass_address", Fmt::Str, Cond::Eq, "最后通行地址", false, false, true, true},
            {"lastPassLongitude", "last_pass_longitude", Fmt::Str, Cond::Eq, "最后通行经度", false, false, true, true},
            {"lastPassLatitude", "last_pass_latitude", Fmt::Str, Cond::Eq, "最后通行维度", false, false, true, true},
            {"lastPassCardirection", "last_pass_cardirection", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"roadSectionId", "road_section_id", Fmt::Str, Cond::Eq, "管理中心路段id", false, false, true, true},
            {"roadSectionName", "road_section_name", Fmt::Str, Cond::Like, "管理中心路段名称", false, false, true, true},
            {"nextPassTime", "next_pass_time", Fmt::DateYmd, Cond::Eq, "预计下一个通行时间", false, false, true, true},
            {"nextPassType", "next_pass_type", Fmt::Str, Cond::Eq, "预计下一个通行类型", false, false, true, true},
            {"nextPassAddress", "next_pass_address", Fmt::Str, Cond::Eq, "预计下一个通行地址", false, false, true, true},
            {"nextPassLongitude", "next_pass_longitude", Fmt::Str, Cond::Eq, "预计下一个通行经度", false, false, true, true},
            {"nextPassLatitude", "next_pass_latitude", Fmt::Str, Cond::Eq, "预计下一个通行维度", false, false, true, true},
            {"orgId", "org_id", Fmt::Str, Cond::Eq, "管理中心id", false, false, true, true},
            {"orgName", "org_name", Fmt::Str, Cond::Like, "管理中心名称", false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
            {"applyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "常用路线明细";
        return s;
    }();
    return s;
}

const Spec& specCarRouteInfo() {
    static const Spec s = [] {
        Spec s;
        s.table = "car_route_info";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"carId", "car_id", Fmt::Str, Cond::Eq, "车辆id", false, false, true, true},
            {"carNo", "car_no", Fmt::Str, Cond::Eq, "车牌号", false, false, true, true},
            {"carType", "car_type", Fmt::Str, Cond::Eq, "车型", false, false, true, true},
            {"carVehicle", "car_vehicle", Fmt::Str, Cond::Eq, "车种", false, false, true, true},
            {"carNum", "car_num", Fmt::Long, Cond::Eq, "轴数", false, false, true, true},
            {"startAddress", "start_address", Fmt::Str, Cond::Eq, "起点通行地址", false, false, true, true},
            {"startLongitude", "start_longitude", Fmt::Str, Cond::Eq, "最后通行经度", false, false, true, true},
            {"startLatitude", "start_latitude", Fmt::Str, Cond::Eq, "起点通行维度", false, false, true, true},
            {"endAddress", "end_address", Fmt::Str, Cond::Eq, "终点通行地址", false, false, true, true},
            {"endLongitude", "end_longitude", Fmt::Str, Cond::Eq, "终点通行经度", false, false, true, true},
            {"endLatitude", "end_latitude", Fmt::Str, Cond::Eq, "终点通行维度", false, false, true, true},
            {"routeDetail", "route_detail", Fmt::Str, Cond::Eq, "路线明细JOSN", false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
            {"applyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"createTimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "常用路线";
        return s;
    }();
    return s;
}

const Spec& specCarSplitRecord() {
    static const Spec s = [] {
        Spec s;
        s.table = "car_split_record";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"carId", "car_id", Fmt::Str, Cond::Eq, "车辆id", false, false, true, true},
            {"carNo", "car_no", Fmt::Str, Cond::Eq, "车牌号", false, false, true, true},
            {"carType", "car_type", Fmt::Str, Cond::Eq, "车型", false, false, true, true},
            {"carVehicle", "car_vehicle", Fmt::Str, Cond::Eq, "车种", false, false, true, true},
            {"passType", "pass_type", Fmt::Str, Cond::Eq, "通信标识", false, false, true, true},
            {"inStationId", "in_station_id", Fmt::Str, Cond::Eq, "入口站id", false, false, true, true},
            {"inStation", "in_station", Fmt::Str, Cond::Eq, "入口站", false, false, true, true},
            {"inTime", "in_time", Fmt::DateYmd, Cond::Eq, "入口时间", false, false, true, true},
            {"outStationId", "out_station_id", Fmt::Str, Cond::Eq, "出口站id", false, false, true, true},
            {"outStation", "out_station", Fmt::Str, Cond::Eq, "出口站", false, false, true, true},
            {"outTime", "out_time", Fmt::DateYmd, Cond::Eq, "出口时间", false, false, true, true},
            {"amount", "amount", Fmt::Double, Cond::Eq, "拆分金额", false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"applyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"createTimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "拆分流水";
        return s;
    }();
    return s;
}

const Spec& specCarSuspiciousBack() {
    static const Spec s = [] {
        Spec s;
        s.table = "car_suspicious_back";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"plateColor", "plate_color", Fmt::Str, Cond::Eq, "车牌颜色", false, false, true, true},
            {"carNo", "car_no", Fmt::Str, Cond::Eq, "车牌号", false, false, true, true},
            {"carType", "car_type", Fmt::Str, Cond::Eq, "车型", false, false, true, true},
            {"carVehicle", "car_vehicle", Fmt::Str, Cond::Eq, "车种", false, false, true, true},
            {"carNum", "car_num", Fmt::Long, Cond::Eq, "轴数", false, false, true, true},
            {"passType", "pass_type", Fmt::Str, Cond::Eq, "通行标识", false, false, true, true},
            {"inStationId", "in_station_id", Fmt::Str, Cond::Eq, "入口站id", false, false, true, true},
            {"inStation", "in_station", Fmt::Str, Cond::Eq, "入口站", false, false, true, true},
            {"inTime", "in_time", Fmt::DateYmd, Cond::Eq, "通行时间", false, false, true, true},
            {"outStationId", "out_station_id", Fmt::Str, Cond::Eq, "出口站id", false, false, true, true},
            {"outStation", "out_station", Fmt::Str, Cond::Eq, "出口站", false, false, true, true},
            {"outTime", "out_time", Fmt::DateYmd, Cond::Eq, "出口时间", false, false, true, true},
            {"gantryStationId", "gantry_station_id", Fmt::Str, Cond::Eq, "门架id", false, false, true, true},
            {"gantrytStation", "gantryt_station", Fmt::Str, Cond::Eq, "门架名称", false, false, true, true},
            {"gantryTime", "gantry_time", Fmt::DateYmd, Cond::Eq, "经过时间", false, false, true, true},
            {"fileIds", "file_ids", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"outGantryStationId", "out_gantry_station_id", Fmt::Str, Cond::Eq, "终止门架id", false, false, true, true},
            {"outGantrytStation", "out_gantryt_station", Fmt::Str, Cond::Eq, "终止门架名称", false, false, true, true},
            {"outGantryTime", "out_gantry_time", Fmt::DateYmd, Cond::Eq, "终止经过时间", false, false, true, true},
            {"outFileIds", "out_file_ids", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"escapedType", "escaped_type", Fmt::Str, Cond::Eq, "逃费类型", false, false, true, true},
            {"escapedTypeName", "escaped_type_name", Fmt::Str, Cond::Like, "逃费类型名称", false, false, true, true},
            {"escapedNum", "escaped_num", Fmt::Long, Cond::Eq, "异常通行门架次数", false, false, true, true},
            {"isExcept", "is_except", Fmt::Str, Cond::Eq, "是否为可疑车辆", false, false, true, true},
            {"exceptRemark", "except_remark", Fmt::Str, Cond::Eq, "可疑原因", false, false, true, true},
            {"exceptFileIds", "except_file_ids", Fmt::Str, Cond::Eq, "可疑材料", false, false, true, true},
            {"checkStatus", "check_status", Fmt::Str, Cond::Eq, "核实状态", false, false, true, true},
            {"orgId", "org_id", Fmt::Str, Cond::Eq, "管理中心id", false, false, true, true},
            {"orgName", "org_name", Fmt::Str, Cond::Like, "管理中心名称", false, false, true, true},
            {"isWhite", "is_white", Fmt::Str, Cond::Eq, "是否在白名单", false, false, true, true},
            {"whiteRemark", "white_remark", Fmt::Str, Cond::Eq, "白名单原因", false, false, true, true},
            {"whiteFileIds", "white_file_ids", Fmt::Str, Cond::Eq, "白名单材料", false, false, true, true},
            {"roadCode", "road_code", Fmt::Str, Cond::Eq, "所属路线编码", false, false, true, true},
            {"roadName", "road_name", Fmt::Str, Cond::Like, "所属路线名称", false, false, true, true},
            {"sectionCode", "section_code", Fmt::Str, Cond::Eq, "所属路段编码", false, false, true, true},
            {"sectionName", "section_name", Fmt::Str, Cond::Like, "所属路段名称", false, false, true, true},
            {"trackId", "track_id", Fmt::Str, Cond::Eq, "行驶轨迹id", false, false, true, true},
            {"trackJosn", "track_josn", Fmt::Str, Cond::Eq, "行驶轨迹josn", false, false, true, true},
            {"trackNames", "track_names", Fmt::Str, Cond::Eq, "轨迹点集合", false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "可疑车辆备份";
        return s;
    }();
    return s;
}

const Spec& specCarSuspiciousCheck() {
    static const Spec s = [] {
        Spec s;
        s.table = "car_suspicious_check";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"carId", "car_id", Fmt::Str, Cond::Eq, "车辆id", false, false, true, true},
            {"carNo", "car_no", Fmt::Str, Cond::Eq, "车牌号", false, false, true, true},
            {"suspicousFlag", "suspicous_flag", Fmt::Str, Cond::Eq, "是否为可疑车辆", false, false, true, true},
            {"escapedType", "escaped_type", Fmt::Str, Cond::Eq, "逃费类型", false, false, true, true},
            {"chargeAmount", "charge_amount", Fmt::Double, Cond::Eq, "收费金额", false, false, true, true},
            {"totalAmount", "total_amount", Fmt::Double, Cond::Eq, "应缴金额", false, false, true, true},
            {"difAmount", "dif_amount", Fmt::Double, Cond::Eq, "差额", false, false, true, true},
            {"attachments", "attachments", Fmt::Str, Cond::Eq, "附件", false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
            {"applyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"createTimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.create_time,t.id";
        s.excelSheetName = "可疑车辆人工核实";
        return s;
    }();
    return s;
}

const Spec& specCarSuspicious() {
    static const Spec s = [] {
        Spec s;
        s.table = "car_suspicious";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"plateColor", "plate_color", Fmt::Str, Cond::Eq, "车牌颜色", false, false, true, true},
            {"carNo", "car_no", Fmt::Str, Cond::Eq, "车牌号", false, false, true, true},
            {"carType", "car_type", Fmt::Str, Cond::Eq, "车型", false, false, true, true},
            {"carVehicle", "car_vehicle", Fmt::Str, Cond::Eq, "车种", false, false, true, true},
            {"carNum", "car_num", Fmt::Long, Cond::Eq, "轴数", false, false, true, true},
            {"passType", "pass_type", Fmt::Str, Cond::Eq, "通行标识", false, false, true, true},
            {"inStationId", "in_station_id", Fmt::Str, Cond::Eq, "入口站id", false, false, true, true},
            {"inStation", "in_station", Fmt::Str, Cond::Eq, "入口站", false, false, true, true},
            {"inTime", "in_time", Fmt::DateYmdHms, Cond::Eq, "通行时间", false, false, true, true},
            {"outStationId", "out_station_id", Fmt::Str, Cond::Eq, "出口站id", false, false, true, true},
            {"outStation", "out_station", Fmt::Str, Cond::Eq, "出口站", false, false, true, true},
            {"outTime", "out_time", Fmt::DateYmdHms, Cond::Eq, "出口时间", false, false, true, true},
            {"gantryStationId", "gantry_station_id", Fmt::Str, Cond::Eq, "门架id", false, false, true, true},
            {"gantrytStation", "gantryt_station", Fmt::Str, Cond::Eq, "门架名称", false, false, true, true},
            {"gantryTime", "gantry_time", Fmt::DateYmdHms, Cond::Eq, "经过时间", false, false, true, true},
            {"fileIds", "file_ids", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"outGantryStationId", "out_gantry_station_id", Fmt::Str, Cond::Eq, "终止门架id", false, false, true, true},
            {"outGantrytStation", "out_gantryt_station", Fmt::Str, Cond::Eq, "终止门架名称", false, false, true, true},
            {"outGantryTime", "out_gantry_time", Fmt::DateYmdHms, Cond::Eq, "终止经过时间", false, false, true, true},
            {"outFileIds", "out_file_ids", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"escapedType", "escaped_type", Fmt::Str, Cond::Eq, "逃费类型", false, false, true, true},
            {"escapedTypeName", "escaped_type_name", Fmt::Str, Cond::Like, "逃费类型名称", false, false, true, true},
            {"escapedNum", "escaped_num", Fmt::Long, Cond::Eq, "异常通行门架次数", false, false, true, true},
            {"isExcept", "is_except", Fmt::Str, Cond::Eq, "是否为可疑车辆", false, false, true, true},
            {"exceptRemark", "except_remark", Fmt::Str, Cond::Eq, "可疑原因", false, false, true, true},
            {"exceptFileIds", "except_file_ids", Fmt::Str, Cond::Eq, "可疑材料", false, false, true, true},
            {"checkStatus", "check_status", Fmt::Str, Cond::Eq, "核实状态", false, false, true, true},
            {"orgId", "org_id", Fmt::Str, Cond::Eq, "管理中心id", false, false, true, true},
            {"orgName", "org_name", Fmt::Str, Cond::Like, "管理中心名称", false, false, true, true},
            {"isWhite", "is_white", Fmt::Str, Cond::Eq, "是否在白名单", false, false, true, true},
            {"whiteRemark", "white_remark", Fmt::Str, Cond::Eq, "白名单原因", false, false, true, true},
            {"whiteFileIds", "white_file_ids", Fmt::Str, Cond::Eq, "白名单材料", false, false, true, true},
            {"roadCode", "road_code", Fmt::Str, Cond::Eq, "所属路线编码", false, false, true, true},
            {"roadName", "road_name", Fmt::Str, Cond::Like, "所属路线名称", false, false, true, true},
            {"sectionCode", "section_code", Fmt::Str, Cond::Like, "所属路段编码", false, false, true, true},
            {"sectionName", "section_name", Fmt::Str, Cond::Like, "所属路段名称", false, false, true, true},
            {"trackId", "track_id", Fmt::Str, Cond::Eq, "行驶轨迹id", false, false, true, true},
            {"trackJosn", "track_josn", Fmt::Str, Cond::Eq, "行驶轨迹josn", false, false, true, true},
            {"trackNames", "track_names", Fmt::Str, Cond::Like, "轨迹点集合", false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "逃费场景", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
            {"carNoQuery", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"createTimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"checkList", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"trailList", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"gantryCode", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"tollCode", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"fwqbm", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"type", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"code", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"chargeAmount", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"totalAmount", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"difAmount", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"mjTime", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"mjAddress", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"txTime", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"txAddress", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.out_time desc,t.id";
        s.excelSheetName = "可疑车辆";
        return s;
    }();
    return s;
}

const Spec& specCarTrackInfo() {
    static const Spec s = [] {
        Spec s;
        s.table = "car_track_info";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"carId", "car_id", Fmt::Str, Cond::Eq, "车辆id", false, false, true, true},
            {"carNo", "car_no", Fmt::Str, Cond::Eq, "车牌号", false, false, true, true},
            {"longitude", "longitude", Fmt::Str, Cond::Eq, "经度", false, false, true, true},
            {"latitude", "latitude", Fmt::Str, Cond::Eq, "维度", false, false, true, true},
            {"deviceType", "device_type", Fmt::Str, Cond::Eq, "设备类型", false, false, true, true},
            {"deviceNo", "device_no", Fmt::Str, Cond::Eq, "设备编号", false, false, true, true},
            {"laneNo", "lane_no", Fmt::Str, Cond::Eq, "车道编号", false, false, true, true},
            {"snapTime", "snap_time", Fmt::DateYmd, Cond::Eq, "抓拍时间", false, false, true, true},
            {"receiveTime", "receive_time", Fmt::DateYmd, Cond::Eq, "接收时间", false, false, true, true},
            {"snapPic", "snap_pic", Fmt::Str, Cond::Eq, "抓拍图片", false, false, true, true},
            {"roadSectionId", "road_section_id", Fmt::Str, Cond::Eq, "管理中心路段id", false, false, true, true},
            {"roadSectionName", "road_section_name", Fmt::Str, Cond::Like, "管理中心路段名称", false, false, true, true},
            {"trackId", "track_id", Fmt::Str, Cond::None, "行驶轨迹id", false, false, true, true},
            {"trackJosn", "track_josn", Fmt::Str, Cond::None, "行驶轨迹josn", false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
            {"applyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"longitudeDec", nullptr, Fmt::Double, Cond::None, "经度", false, false, false, false, nullptr, nullptr},
            {"latitudeDec", nullptr, Fmt::Double, Cond::None, "维度", false, false, false, false, nullptr, nullptr},
            {"pageNum", nullptr, Fmt::Int, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"pageSize", nullptr, Fmt::Int, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.create_time,t.id";
        s.excelSheetName = "车辆行驶轨迹";
        return s;
    }();
    return s;
}

const Spec& specCarWarningInfo() {
    static const Spec s = [] {
        Spec s;
        s.table = "car_warning_info";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"carId", "car_id", Fmt::Str, Cond::Eq, "车辆id", false, false, true, true},
            {"carNo", "car_no", Fmt::Str, Cond::Like, "车牌号", false, false, true, true},
            {"carType", "car_type", Fmt::Str, Cond::Eq, "车型", false, false, true, true},
            {"carVehicle", "car_vehicle", Fmt::Str, Cond::Eq, "车种", false, false, true, true},
            {"carNum", "car_num", Fmt::Long, Cond::Eq, "轴数", false, false, true, true},
            {"inStationId", "in_station_id", Fmt::Str, Cond::Eq, "入口站id", false, false, true, true},
            {"inStation", "in_station", Fmt::Str, Cond::Eq, "入口站", false, false, true, true},
            {"inTime", "in_time", Fmt::DateYmdHms, Cond::Eq, "入口时间", false, false, true, true},
            {"gantryStationId", "gantry_station_id", Fmt::Str, Cond::Eq, "门架id", false, false, true, true},
            {"gantrytStation", "gantryt_station", Fmt::Str, Cond::Like, "门架名称", false, false, true, true},
            {"gantryTime", "gantry_time", Fmt::DateYmdHms, Cond::Eq, "经过时间", false, false, true, true},
            {"fileIds", "file_ids", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"nextPassTime", "next_pass_time", Fmt::DateYmdHms, Cond::Eq, "预计下一个通行时间", false, false, true, true},
            {"nextPassType", "next_pass_type", Fmt::Str, Cond::Eq, "预计下一个通行类型", false, false, true, true},
            {"nextPassAddress", "next_pass_address", Fmt::Str, Cond::Eq, "预计下一个通行地址", false, false, true, true},
            {"nextPassLongitude", "next_pass_longitude", Fmt::Str, Cond::Eq, "预计下一个通行经度", false, false, true, true},
            {"nextPassLatitude", "next_pass_latitude", Fmt::Str, Cond::Eq, "预计下一个通行维度", false, false, true, true},
            {"roadCode", "road_code", Fmt::Str, Cond::Like, "所属路线编码", false, false, true, true},
            {"roadName", "road_name", Fmt::Str, Cond::Like, "所属路线名称", false, false, true, true},
            {"sectionCode", "section_code", Fmt::Str, Cond::Like, "所属路段编码", false, false, true, true},
            {"sectionName", "section_name", Fmt::Str, Cond::Like, "所属路段名称", false, false, true, true},
            {"trackId", "track_id", Fmt::Str, Cond::Eq, "行驶轨迹id", false, false, true, true},
            {"trackJosn", "track_josn", Fmt::Str, Cond::Eq, "行驶轨迹josn", false, false, true, true},
            {"trackNames", "track_names", Fmt::Str, Cond::Like, "轨迹点集合", false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "同步日期", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"gantryTimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"escapedType", nullptr, Fmt::Str, Cond::None, "逃费类型", false, false, false, false, nullptr, nullptr},
            {"escapedAmount", nullptr, Fmt::Double, Cond::None, "逃费金额", false, false, false, false, nullptr, nullptr},
            {"carNoQuery", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"createTimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"inTimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"flag", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"flagTime", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"queryRante", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"gantryCode", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"tollCode", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"fwqbm", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"type", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"code", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"plateColor", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"trailFwqList", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"needToWarnStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"nextPassTimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.gantry_time desc,t.id";
        s.excelSheetName = "预警车辆";
        return s;
    }();
    return s;
}

const Spec& specCarWarningRule() {
    static const Spec s = [] {
        Spec s;
        s.table = "car_warning_rule";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"ruleName", "rule_name", Fmt::Str, Cond::Like, "规则名称", false, false, true, true},
            {"noticeRangeId", "notice_range_id", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"noticeRangeAnme", "notice_range_anme", Fmt::Str, Cond::Like, nullptr, false, false, true, true},
            {"notice", "notice", Fmt::Str, Cond::Eq, "通知", false, false, true, true},
            {"noticeType", "notice_type", Fmt::Str, Cond::Eq, "通知方式", false, false, true, true},
            {"noticeUserId", "notice_user_id", Fmt::Str, Cond::Eq, "通知人员id", false, false, true, true},
            {"noticeUserName", "notice_user_name", Fmt::Str, Cond::Like, "通知人员", false, false, true, true},
            {"orgId", "org_id", Fmt::Str, Cond::Eq, "所属站/所", false, false, true, true},
            {"orgName", "org_name", Fmt::Str, Cond::Like, "所属站/所", false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
            {"applyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"createTimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "预警规则";
        return s;
    }();
    return s;
}

const Spec& specCarWhiteInfo() {
    static const Spec s = [] {
        Spec s;
        s.table = "car_white_info";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"plateColor", "plate_color", Fmt::Str, Cond::Eq, "车牌颜色", false, false, true, true},
            {"carNo", "car_no", Fmt::Str, Cond::Eq, "车牌号", false, false, true, true},
            {"carType", "car_type", Fmt::Str, Cond::Eq, "车型", false, false, true, true},
            {"carVehicle", "car_vehicle", Fmt::Str, Cond::Eq, "车种", false, false, true, true},
            {"carNum", "car_num", Fmt::Long, Cond::Eq, "轴数", false, false, true, true},
            {"fileIds", "file_ids", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
            {"createTimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"createInfo", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"carNoQuery", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "车俩白名单";
        return s;
    }();
    return s;
}

const Spec& specGantryCar() {
    static const Spec s = [] {
        Spec s;
        s.table = "gantry_car";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"carNo", "car_no", Fmt::Str, Cond::Eq, "车牌号", false, false, true, true},
            {"carType", "car_type", Fmt::Str, Cond::Eq, "车型", false, false, true, true},
            {"carVehicle", "car_vehicle", Fmt::Str, Cond::Eq, "车种", false, false, true, true},
            {"carNum", "car_num", Fmt::Long, Cond::Eq, "轴数", false, false, true, true},
            {"inStationId", "in_station_id", Fmt::Str, Cond::Eq, "入口站id", false, false, true, true},
            {"inStation", "in_station", Fmt::Str, Cond::Eq, "入口站", false, false, true, true},
            {"inTime", "in_time", Fmt::DateYmd, Cond::Eq, "通行时间", false, false, true, true},
            {"gantryStationId", "gantry_station_id", Fmt::Str, Cond::Eq, "门架id", false, false, true, true},
            {"gantrytStation", "gantryt_station", Fmt::Str, Cond::Eq, "门架名称", false, false, true, true},
            {"gantryTime", "gantry_time", Fmt::DateYmd, Cond::Eq, "经过时间", false, false, true, true},
            {"fileIds", "file_ids", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
            {"applyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"createTimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "门架拍识查询";
        return s;
    }();
    return s;
}

const Spec& specGantryTradeInfo() {
    static const Spec s = [] {
        Spec s;
        s.table = "gantry_trade_info";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "id", Fmt::Str, Cond::Eq, nullptr, true, false, true, true, nullptr},
            {"epsId", "eps_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true, nullptr},
            {"createBy", "create_by", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true, nullptr},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true, nullptr},
            {"sort", "sort", Fmt::Int, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"tenantId", "tenant_id", Fmt::Long, Cond::Eq, nullptr, false, false, true, true, nullptr},
            {"carNo", "car_no", Fmt::Str, Cond::Eq, "车牌号", false, false, true, true},
            {"carType", "car_type", Fmt::Str, Cond::Eq, "车型", false, false, true, true},
            {"carVehicle", "car_vehicle", Fmt::Str, Cond::Eq, "车种", false, false, true, true},
            {"carNum", "car_num", Fmt::Long, Cond::Eq, "轴数", false, false, true, true},
            {"inStationId", "in_station_id", Fmt::Str, Cond::Eq, "入门架id", false, false, true, true},
            {"inStation", "in_station", Fmt::Str, Cond::Eq, "入门架", false, false, true, true},
            {"inTime", "in_time", Fmt::DateYmd, Cond::Eq, "入门时间", false, false, true, true},
            {"outStationId", "out_station_id", Fmt::Str, Cond::Eq, "出口门架id", false, false, true, true},
            {"outStation", "out_station", Fmt::Str, Cond::Eq, "出口门架", false, false, true, true},
            {"outTime", "out_time", Fmt::DateYmd, Cond::Eq, "出口时间", false, false, true, true},
            {"chargeType", "charge_type", Fmt::Str, Cond::Eq, "交易类型", false, false, true, true},
            {"amount", "amount", Fmt::Double, Cond::Eq, "收费金额", false, false, true, true},
            {"backCol1", "back_col1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "back_col2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"status", "status", Fmt::Str, Cond::Eq, "状态", false, false, true, true},
            {"remark", "remark", Fmt::Str, Cond::None, "备注", false, false, true, true},
            {"applyTime1", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"applyTime2", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"createTimeStr", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "门架交易查询";
        return s;
    }();
    return s;
}

void registerManagerArea(Router& r) {
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/BussTest.java
        // ruoyi-system/src/main/resources/mapper/manager/BussTestMapper.xml
        Perms p;
        p.list = "manager:busstest:list";
        registerCrud(r, "/manager/busstest", specBussTest(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarAduitFree.java
        // ruoyi-system/src/main/resources/mapper/manager/CarAduitFreeMapper.xml
        Perms p;
        registerCrud(r, "/manager/aduitfree", specCarAduitFree(), p, "id");
        registerListVariant(r, "/manager/aduitfree/incomeStatics", specCarAduitFree(), ListKind::Paged);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarConfimFree.java
        // ruoyi-system/src/main/resources/mapper/manager/CarConfimFreeMapper.xml
        Perms p;
        registerCrud(r, "/manager/confimfree", specCarConfimFree(), p, "exceptIds");
        registerListVariant(r, "/manager/confimfree/concernedList", specCarConfimFree(), ListKind::Paged);
        registerListVariant(r, "/manager/confimfree/carStatics", specCarConfimFree(), ListKind::Paged);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarExceptRecord.java
        // ruoyi-system/src/main/resources/mapper/manager/CarExceptRecordMapper.xml
        Perms p;
        registerCrud(r, "/manager/exceptrecord", specCarExceptRecord(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarFeeRecord.java
        // ruoyi-system/src/main/resources/mapper/manager/CarFeeRecordMapper.xml
        Perms p;
        p.list = "manager:feerecord:list";
        registerCrud(r, "/manager/feerecord", specCarFeeRecord(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarInfo.java
        // ruoyi-system/src/main/resources/mapper/manager/CarInfoMapper.xml
        Perms p;
        p.list = "manager:carinfo:list";
        registerCrud(r, "/manager/carinfo", specCarInfo(), p, "id");
        registerListVariant(r, "/manager/carinfo/listAll", specCarInfo(), ListKind::Paged);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarQueryLog.java
        // ruoyi-system/src/main/resources/mapper/manager/CarQueryLogMapper.xml
        Perms p;
        p.list = "manager:querylog:list";
        registerCrud(r, "/manager/querylog", specCarQueryLog(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarRouteDetail.java
        // ruoyi-system/src/main/resources/mapper/manager/CarRouteDetailMapper.xml
        Perms p;
        p.list = "manager:routedetail:list";
        registerCrud(r, "/manager/routedetail", specCarRouteDetail(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarRouteInfo.java
        // ruoyi-system/src/main/resources/mapper/manager/CarRouteInfoMapper.xml
        Perms p;
        p.list = "manager:routeinfo:list";
        registerCrud(r, "/manager/routeinfo", specCarRouteInfo(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSplitRecord.java
        // ruoyi-system/src/main/resources/mapper/manager/CarSplitRecordMapper.xml
        Perms p;
        p.list = "manager:splitrecord:list";
        registerCrud(r, "/manager/splitrecord", specCarSplitRecord(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSuspiciousBack.java
        // ruoyi-system/src/main/resources/mapper/manager/CarSuspiciousBackMapper.xml
        Perms p;
        p.list = "manager:carsuspiciousback:list";
        registerCrud(r, "/manager/carsuspiciousback", specCarSuspiciousBack(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSuspiciousCheck.java
        // ruoyi-system/src/main/resources/mapper/manager/CarSuspiciousCheckMapper.xml
        Perms p;
        p.list = "manager:suspiciouscheck:list";
        registerCrud(r, "/manager/suspiciouscheck", specCarSuspiciousCheck(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarSuspicious.java
        // ruoyi-system/src/main/resources/mapper/manager/CarSuspiciousMapper.xml
        Perms p;
        p.list = "manager:suspicious:list";
        registerCrud(r, "/manager/suspicious", specCarSuspicious(), p, "id");
        registerListVariant(r, "/manager/suspicious/listAll", specCarSuspicious(), ListKind::Paged);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarTrackInfo.java
        // ruoyi-system/src/main/resources/mapper/manager/CarTrackInfoMapper.xml
        Perms p;
        p.list = "manager:cartrackinfo:list";
        registerCrud(r, "/manager/cartrackinfo", specCarTrackInfo(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarWarningInfo.java
        // ruoyi-system/src/main/resources/mapper/manager/CarWarningInfoMapper.xml
        Perms p;
        p.list = "manager:carwarning:list";
        registerCrud(r, "/manager/carwarning", specCarWarningInfo(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarWarningRule.java
        // ruoyi-system/src/main/resources/mapper/manager/CarWarningRuleMapper.xml
        Perms p;
        p.list = "manager:warningrule:list";
        registerCrud(r, "/manager/warningrule", specCarWarningRule(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/CarWhiteInfo.java
        // ruoyi-system/src/main/resources/mapper/manager/CarWhiteInfoMapper.xml
        Perms p;
        p.list = "manager:whiteinfo:list";
        registerCrud(r, "/manager/whiteinfo", specCarWhiteInfo(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/GantryCar.java
        // ruoyi-system/src/main/resources/mapper/manager/GantryCarMapper.xml
        Perms p;
        p.list = "manager:gantrycar:list";
        registerCrud(r, "/manager/gantrycar", specGantryCar(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/manager/domain/GantryTradeInfo.java
        // ruoyi-system/src/main/resources/mapper/manager/GantryTradeInfoMapper.xml
        Perms p;
        p.list = "manager:gantrytrade:list";
        registerCrud(r, "/manager/gantrytrade", specGantryTradeInfo(), p, "id");
    }
}

} // namespace cm::web::crud
