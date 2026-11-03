// 由 scripts/gen_crud_spec.py 生成（area=flow）。
// 重新生成: python scripts/gen_crud_spec.py --area flow
//
// 只覆盖同构 CRUD：list / export / getInfo / add / edit / remove。
// 非 CRUD 接口、唯一性校验、tenant 过滤、软删除、外部服务依赖等仍由手写控制器负责
// （src/cm/web/controller/**）。解析不到的控制器整只跳过，见生成器输出。
//
// 每个实体的 Spec 通过 spec<Entity>() 暴露（声明见 FlowCrudSpecs.hpp），
// 手写控制器可以复用同一份列定义，避免把几十个字段再抄一遍。
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"
#include "cm/web/specs/FlowCrudSpecs.hpp"

namespace cm::web::crud {

const Spec& specFlowApplyInfo() {
    static const Spec s = [] {
        Spec s;
        s.table = "flow_apply_info";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "ID", Fmt::Str, Cond::None, nullptr, true, false, true, false},
            {"epsId", "eps_id", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true},
            {"createBy", "create_by", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true},
            {"sort", "sort", Fmt::Int, Cond::None, nullptr, false, false, true, true},
            {"remark", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"tenantId", nullptr, Fmt::Long, Cond::None, nullptr, false, false, false, false},
            {"deptSubCode", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"flag", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"searchValue", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"params", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"billOid", "BILL_OID", Fmt::Str, Cond::Eq, "单据OID", false, false, true, true},
            {"bussType", "BUSS_TYPE", Fmt::Str, Cond::Eq, "业务类型-字典", false, false, true, true},
            {"flowRuid", "FLOW_RUID", Fmt::Str, Cond::Eq, "流程实例ID", false, false, true, true},
            {"msgTitle", "MSG_TITLE", Fmt::Str, Cond::Eq, "标题", false, false, true, true},
            {"msgContext", "MSG_CONTEXT", Fmt::Str, Cond::Eq, "内容", false, false, true, true},
            {"msgType", "MSG_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"msgUrl", "MSG_URL", Fmt::Str, Cond::Eq, "处理的URL", false, false, true, true},
            {"applyName", "APPLY_NAME", Fmt::Str, Cond::Eq, "申请人", false, false, true, true},
            {"currentOid", "CURRENT_OID", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"pcOid", "PC_OID", Fmt::Str, Cond::Eq, "批次OID", false, false, true, true},
            {"backCol1", "BACK_COL1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "BACK_COL2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"backCol3", "BACK_COL3", Fmt::Str, Cond::Eq, "备用字段3", false, false, true, true},
            {"flowStatus", "FLOW_STATUS", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"auitEmpName", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"entrustInfo", "entrust_info", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "我的申请";
        return s;
    }();
    return s;
}

const Spec& specFlowCurrentNode() {
    static const Spec s = [] {
        Spec s;
        s.table = "flow_current_node";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "ID", Fmt::Str, Cond::None, nullptr, true, false, true, false},
            {"epsId", "eps_id", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true},
            {"createBy", "create_by", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true},
            {"sort", "sort", Fmt::Int, Cond::None, nullptr, false, false, true, true},
            {"remark", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"tenantId", nullptr, Fmt::Long, Cond::None, nullptr, false, false, false, false},
            {"deptSubCode", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"flag", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"searchValue", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"params", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"flowOid", "FLOW_OID", Fmt::Str, Cond::Eq, "流程OID", false, false, true, true},
            {"currentOid", "CURRENT_OID", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"nodeOrder", "NODE_ORDER", Fmt::Int, Cond::Eq, "节点顺序", false, false, true, true},
            {"nodeKey", "NODE_KEY", Fmt::Str, Cond::Eq, "节点KEY", false, false, true, true},
            {"nodeName", "NODE_NAME", Fmt::Str, Cond::Eq, "节点名称", false, false, true, true},
            {"configType", "CONFIG_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"configId", "CONFIG_ID", Fmt::Str, Cond::Eq, "节点配置id", false, false, true, true},
            {"configName", "CONFIG_NAME", Fmt::Str, Cond::Eq, "节点配置名称", false, false, true, true},
            {"billOid", "BILL_OID", Fmt::Str, Cond::Eq, "单据OID", false, false, true, true},
            {"auitEmpOid", "AUIT_EMP_OID", Fmt::Str, Cond::Eq, "处理人ID", false, false, true, true},
            {"auitEmpName", "AUIT_EMP_NAME", Fmt::Str, Cond::Eq, "处理人名称", false, false, true, true},
            {"backCol1", "BACK_COL1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "BACK_COL2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"backCol3", "BACK_COL3", Fmt::Str, Cond::Eq, "备用字段3", false, false, true, true},
            {"roleId", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"tableName", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"projectId", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"flowKey", nullptr, Fmt::Str, Cond::None, "流程key", false, false, false, false, nullptr, nullptr},
            {"flowRuid", nullptr, Fmt::Str, Cond::None, "流程实例ID", false, false, false, false, nullptr, nullptr},
            {"flowApplyOid", nullptr, Fmt::Str, Cond::None, "流程申请ID", false, false, false, false, nullptr, nullptr},
            {"flowStatus", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"shValue", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"shContext", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"entrustUserId", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"entrustUserName", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"roleKey", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"deptId", nullptr, Fmt::Long, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "流程_当前节点";
        return s;
    }();
    return s;
}

const Spec& specFlowList() {
    static const Spec s = [] {
        Spec s;
        s.table = "flow_list";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "ID", Fmt::Str, Cond::None, nullptr, true, false, true, false},
            {"epsId", "eps_id", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true},
            {"createBy", "create_by", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true},
            {"sort", "sort", Fmt::Int, Cond::None, nullptr, false, false, true, true},
            {"remark", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"tenantId", nullptr, Fmt::Long, Cond::None, nullptr, false, false, false, false},
            {"deptSubCode", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"flag", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"searchValue", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"params", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"billOid", "BILL_OID", Fmt::Str, Cond::Eq, "单据OID", false, false, true, true},
            {"bussType", "BUSS_TYPE", Fmt::Str, Cond::Eq, "流程类型", false, false, true, true},
            {"taskId", "TASK_ID", Fmt::Str, Cond::Eq, "任务ID", false, false, true, true},
            {"flowRuid", "flow_ruid", Fmt::Str, Cond::Eq, "流程实例ID", false, false, true, true},
            {"currentOid", "CURRENT_OID", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"shUser", "SH_USER", Fmt::Str, Cond::Eq, "审核人", false, false, true, true},
            {"shKey", "SH_KEY", Fmt::Str, Cond::Eq, "审核结论KEY", false, false, true, true},
            {"shValue", "SH_VALUE", Fmt::Str, Cond::Eq, "审核结论", false, false, true, true},
            {"shContext", "SH_CONTEXT", Fmt::Str, Cond::Eq, "内容", false, false, true, true},
            {"backCol1", "BACK_COL1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "BACK_COL2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"backCol3", "BACK_COL3", Fmt::Str, Cond::Eq, "备用字段3", false, false, true, true},
        };
        s.orderBy = "t.create_time ASC ,t.id";
        s.excelSheetName = "审核历史记录";
        return s;
    }();
    return s;
}

const Spec& specFlowMessageDispose() {
    static const Spec s = [] {
        Spec s;
        s.table = "flow_message_dispose";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "ID", Fmt::Str, Cond::None, nullptr, true, false, true, false},
            {"epsId", "eps_id", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true},
            {"createBy", "create_by", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true},
            {"sort", "sort", Fmt::Int, Cond::None, nullptr, false, false, true, true},
            {"remark", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"tenantId", nullptr, Fmt::Long, Cond::None, nullptr, false, false, false, false},
            {"deptSubCode", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"flag", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"searchValue", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"params", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"mid", "MID", Fmt::Str, Cond::Eq, "消息外键", false, false, true, true},
            {"bussId", "BUSS_ID", Fmt::Str, Cond::Eq, "处理对象ID", false, false, true, true},
            {"bussName", "BUSS_NAME", Fmt::Str, Cond::Eq, "处理对象名称", false, false, true, true},
            {"msgStatus", "MSG_STATUS", Fmt::Str, Cond::Eq, "消息状态", false, false, true, true},
            {"hangTime", "HANG_TIME", Fmt::DateIso, Cond::Eq, "处理时间", false, false, true, true},
            {"disposeOther", "DISPOSE_OTHER", Fmt::Str, Cond::Eq, "其他", false, false, true, true},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "系统消息处理人";
        return s;
    }();
    return s;
}

const Spec& specFlowMessageInfo() {
    static const Spec s = [] {
        Spec s;
        s.table = "flow_message_info";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "ID", Fmt::Str, Cond::None, nullptr, true, false, true, false},
            {"epsId", "eps_id", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true},
            {"createBy", "create_by", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true},
            {"sort", "sort", Fmt::Int, Cond::None, nullptr, false, false, true, true},
            {"remark", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"tenantId", nullptr, Fmt::Long, Cond::None, nullptr, false, false, false, false},
            {"deptSubCode", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"flag", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"searchValue", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"params", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"messageNo", "message_no", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"billOid", "BILL_OID", Fmt::Str, Cond::Eq, "单据OID", false, false, true, true},
            {"bussType", "BUSS_TYPE", Fmt::Str, Cond::Eq, "业务类型-字典", false, false, true, true},
            {"flowRuid", "FLOW_RUID", Fmt::Str, Cond::Eq, "流程实例ID", false, false, true, true},
            {"msgTitle", "MSG_TITLE", Fmt::Str, Cond::Eq, "标题", false, false, true, true},
            {"msgContext", "MSG_CONTEXT", Fmt::Str, Cond::Eq, "内容", false, false, true, true},
            {"msgType", "MSG_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"msgUrl", "MSG_URL", Fmt::Str, Cond::Eq, "处理的URL", false, false, true, true},
            {"pcOid", "PC_OID", Fmt::Str, Cond::Eq, "批次OID", false, false, true, true},
            {"applyName", "APPLY_NAME", Fmt::Str, Cond::Eq, "申请人", false, false, true, true},
            {"backCol1", "BACK_COL1", Fmt::Str, Cond::Eq, "备用字段1", false, false, true, true},
            {"backCol2", "BACK_COL2", Fmt::Str, Cond::Eq, "备用字段2", false, false, true, true},
            {"backCol3", "BACK_COL3", Fmt::Str, Cond::Eq, "备用字段3", false, false, true, true},
            {"userId", nullptr, Fmt::Long, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"msgStatus", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"flowStatus", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"curEmpNames", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
            {"disposeList", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false, nullptr, nullptr},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "系统内部消息";
        return s;
    }();
    return s;
}

const Spec& specFlowName() {
    static const Spec s = [] {
        Spec s;
        s.table = "flow_name";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "ID", Fmt::Str, Cond::None, nullptr, true, false, true, false},
            {"epsId", "eps_id", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true},
            {"createBy", "create_by", Fmt::Long, Cond::None, nullptr, false, false, true, false},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, false},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true},
            {"sort", "sort", Fmt::Int, Cond::None, nullptr, false, false, true, true},
            {"remark", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"tenantId", "tenant_id", Fmt::Long, Cond::None, nullptr, false, false, true, false},
            {"deptSubCode", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"flag", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"searchValue", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"params", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"flowKey", "FLOW_KEY", Fmt::Str, Cond::Eq, "流程KEY", false, false, true, true},
            {"flowTitle", "FLOW_TITLE", Fmt::Str, Cond::Eq, "流程名称", false, false, true, true},
            {"flowContext", "FLOW_CONTEXT", Fmt::Str, Cond::Eq, "内容", false, false, true, true},
            {"bussName", "BUSS_NAME", Fmt::Str, Cond::Eq, "业务名称", false, false, true, true},
            {"tenantName", nullptr, Fmt::Str, Cond::None, "单位名称", false, false, false, false, nullptr, nullptr},
            {"flowBusinessType", "flow_business_type", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
        };
        s.orderBy = "t.tenant_id,t.flow_key,t.id";
        s.excelSheetName = "流程名称";
        return s;
    }();
    return s;
}

const Spec& specFlowTemplate() {
    static const Spec s = [] {
        Spec s;
        s.table = "flow_template";
        s.alias = "t";
        s.extraWhere = " and t.del_flag = '0'";
        s.fields = {
            {"id", "ID", Fmt::Str, Cond::None, nullptr, true, false, true, false},
            {"epsId", "eps_id", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, true, true},
            {"createBy", "create_by", Fmt::Long, Cond::None, nullptr, false, false, true, false},
            {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, false},
            {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, true, true},
            {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, true, true},
            {"sort", "sort", Fmt::Int, Cond::None, nullptr, false, false, true, true},
            {"remark", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"tenantId", nullptr, Fmt::Long, Cond::None, nullptr, false, false, false, false},
            {"deptSubCode", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"flag", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"searchValue", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"params", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
            {"flowOid", "FLOW_OID", Fmt::Str, Cond::Eq, "流程OID", false, false, true, true},
            {"flowType", "FLOW_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"nodeOrder", "NODE_ORDER", Fmt::Int, Cond::Eq, "节点顺序", false, false, true, true},
            {"nodeKey", "NODE_KEY", Fmt::Str, Cond::Eq, "节点KEY", false, false, true, true},
            {"nodeName", "NODE_NAME", Fmt::Str, Cond::Eq, "节点名称", false, false, true, true},
            {"nextNodeOid", "NEXT_NODE_OID", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"previousNodeOid", "PREVIOUS_NODE_OID", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"returnNum", "RETURN_NUM", Fmt::Int, Cond::Eq, "驳回到第几步 0 是发起人", false, false, true, true},
            {"returnNodeOid", "RETURN_NODE_OID", Fmt::Str, Cond::Eq, "驳回节点OID", false, false, true, true},
            {"configCondtion", "CONFIG_CONDTION", Fmt::Str, Cond::Eq, "节点配置条件", false, false, true, true},
            {"configType", "CONFIG_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false, true, true},
            {"configId", "CONFIG_ID", Fmt::Str, Cond::Eq, "节点配置id", false, false, true, true},
            {"configName", "CONFIG_NAME", Fmt::Str, Cond::Eq, "节点配置名称", false, false, true, true},
        };
        s.orderBy = "t.NODE_ORDER ,t.id";
        s.excelSheetName = "流程节点";
        return s;
    }();
    return s;
}

void registerFlowArea(Router& r) {
    {
        // ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowApplyInfo.java
        // ruoyi-system/src/main/resources/mapper/flow/FlowApplyInfoMapper.xml
        Perms p;
        p.query = "flow:applyinfo:query";
        registerCrud(r, "/flow/applyinfo", specFlowApplyInfo(), p, "id");
        registerListVariant(r, "/flow/applyinfo/listAll", specFlowApplyInfo(), ListKind::Paged, "flow:applyinfo:list");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowCurrentNode.java
        // ruoyi-system/src/main/resources/mapper/flow/FlowCurrentNodeMapper.xml
        Perms p;
        p.list = "flow:currentnode:list";
        p.query = "flow:currentnode:query";
        registerCrud(r, "/flow/currentnode", specFlowCurrentNode(), p, "billOid");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowList.java
        // ruoyi-system/src/main/resources/mapper/flow/FlowListMapper.xml
        Perms p;
        p.list = "flow:flowlist:list";
        p.query = "flow:flowlist:query";
        registerCrud(r, "/flow/flowlist", specFlowList(), p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowMessageDispose.java
        // ruoyi-system/src/main/resources/mapper/flow/FlowMessageDisposeMapper.xml
        Perms p;
        p.list = "flow:messagedispose:list";
        p.query = "flow:messagedispose:query";
        registerCrud(r, "/flow/messagedispose", specFlowMessageDispose(), p, "mid");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowMessageInfo.java
        // ruoyi-system/src/main/resources/mapper/flow/FlowMessageInfoMapper.xml
        Perms p;
        p.query = "flow:messageinfo:query";
        registerCrud(r, "/flow/messageinfo", specFlowMessageInfo(), p, "id");
        registerListVariant(r, "/flow/messageinfo/listyb", specFlowMessageInfo(), ListKind::Paged);
        registerListVariant(r, "/flow/messageinfo/listyj", specFlowMessageInfo(), ListKind::Paged);
        registerListVariant(r, "/flow/messageinfo/listxx", specFlowMessageInfo(), ListKind::Paged);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowName.java
        // ruoyi-system/src/main/resources/mapper/flow/FlowNameMapper.xml
        Perms p;
        p.list = "flow:flowname:list";
        p.query = "flow:flowname:query";
        registerCrud(r, "/flow/flowname", specFlowName(), p, "id");
        registerListVariant(r, "/flow/flowname/listQuery", specFlowName(), ListKind::Paged);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowTemplate.java
        // ruoyi-system/src/main/resources/mapper/flow/FlowTemplateMapper.xml
        Perms p;
        p.list = "flow:flowtemplate:list";
        p.query = "flow:flowtemplate:query";
        registerCrud(r, "/flow/flowtemplate", specFlowTemplate(), p, "id");
    }
}

} // namespace cm::web::crud
