// 由 scripts/gen_crud_spec.py 生成（area=flow）。
// 重新生成: python scripts/gen_crud_spec.py --area flow
//
// 只覆盖同构 CRUD：list / export / getInfo / add / edit / remove。
// 非 CRUD 接口、唯一性校验、tenant 过滤、软删除、外部服务依赖等仍由手写控制器负责
// （src/cm/web/controller/**）。解析不到的控制器整只跳过，见生成器输出。
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"

namespace cm::web::crud {

void registerFlowArea(Router& r) {
    {
        // ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowApplyInfo.java
        // ruoyi-system/src/main/resources/mapper/flow/FlowApplyInfoMapper.xml
        Spec s;
        s.table = "flow_apply_info";
        s.alias = "t";
        s.fields = {
            {"billOid", "BILL_OID", Fmt::Str, Cond::Eq, "单据OID", false, false},
            {"bussType", "BUSS_TYPE", Fmt::Str, Cond::Eq, "业务类型-字典", false, false},
            {"flowRuid", "FLOW_RUID", Fmt::Str, Cond::Eq, "流程实例ID", false, false},
            {"msgTitle", "MSG_TITLE", Fmt::Str, Cond::Eq, "标题", false, false},
            {"msgContext", "MSG_CONTEXT", Fmt::Str, Cond::Eq, "内容", false, false},
            {"msgType", "MSG_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"msgUrl", "MSG_URL", Fmt::Str, Cond::Eq, "处理的URL", false, false},
            {"applyName", "APPLY_NAME", Fmt::Str, Cond::Eq, "申请人", false, false},
            {"currentOid", "CURRENT_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"pcOid", "PC_OID", Fmt::Str, Cond::Eq, "批次OID", false, false},
            {"backCol1", "BACK_COL1", Fmt::Str, Cond::Eq, "备用字段1", false, false},
            {"backCol2", "BACK_COL2", Fmt::Str, Cond::Eq, "备用字段2", false, false},
            {"backCol3", "BACK_COL3", Fmt::Str, Cond::Eq, "备用字段3", false, false},
            {"flowStatus", "FLOW_STATUS", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"entrustInfo", "entrust_info", Fmt::Str, Cond::Eq, nullptr, false, false},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "我的申请";
        Perms p;
        p.query = "flow:applyinfo:query";
        registerCrud(r, "/flow/applyinfo", s, p, "id");
        registerListVariant(r, "/flow/applyinfo/listAll", s, ListKind::Paged, "flow:applyinfo:list");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowCurrentNode.java
        // ruoyi-system/src/main/resources/mapper/flow/FlowCurrentNodeMapper.xml
        Spec s;
        s.table = "flow_current_node";
        s.alias = "t";
        s.fields = {
            {"flowOid", "FLOW_OID", Fmt::Str, Cond::Eq, "流程OID", false, false},
            {"currentOid", "CURRENT_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"nodeOrder", "NODE_ORDER", Fmt::Int, Cond::Eq, "节点顺序", false, false},
            {"nodeKey", "NODE_KEY", Fmt::Str, Cond::Eq, "节点KEY", false, false},
            {"nodeName", "NODE_NAME", Fmt::Str, Cond::Eq, "节点名称", false, false},
            {"configType", "CONFIG_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"configId", "CONFIG_ID", Fmt::Str, Cond::Eq, "节点配置id", false, false},
            {"configName", "CONFIG_NAME", Fmt::Str, Cond::Eq, "节点配置名称", false, false},
            {"billOid", "BILL_OID", Fmt::Str, Cond::Eq, "单据OID", false, false},
            {"auitEmpOid", "AUIT_EMP_OID", Fmt::Str, Cond::Eq, "处理人ID", false, false},
            {"auitEmpName", "AUIT_EMP_NAME", Fmt::Str, Cond::Eq, "处理人名称", false, false},
            {"backCol1", "BACK_COL1", Fmt::Str, Cond::Eq, "备用字段1", false, false},
            {"backCol2", "BACK_COL2", Fmt::Str, Cond::Eq, "备用字段2", false, false},
            {"backCol3", "BACK_COL3", Fmt::Str, Cond::Eq, "备用字段3", false, false},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "流程_当前节点";
        Perms p;
        p.list = "flow:currentnode:list";
        p.query = "flow:currentnode:query";
        registerCrud(r, "/flow/currentnode", s, p, "billOid");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowList.java
        // ruoyi-system/src/main/resources/mapper/flow/FlowListMapper.xml
        Spec s;
        s.table = "flow_list";
        s.alias = "t";
        s.fields = {
            {"billOid", "BILL_OID", Fmt::Str, Cond::Eq, "单据OID", false, false},
            {"bussType", "BUSS_TYPE", Fmt::Str, Cond::Eq, "流程类型", false, false},
            {"taskId", "TASK_ID", Fmt::Str, Cond::Eq, "任务ID", false, false},
            {"flowRuid", "flow_ruid", Fmt::Str, Cond::Eq, "流程实例ID", false, false},
            {"currentOid", "CURRENT_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"shUser", "SH_USER", Fmt::Str, Cond::Eq, "审核人", false, false},
            {"shKey", "SH_KEY", Fmt::Str, Cond::Eq, "审核结论KEY", false, false},
            {"shValue", "SH_VALUE", Fmt::Str, Cond::Eq, "审核结论", false, false},
            {"shContext", "SH_CONTEXT", Fmt::Str, Cond::Eq, "内容", false, false},
            {"backCol1", "BACK_COL1", Fmt::Str, Cond::Eq, "备用字段1", false, false},
            {"backCol2", "BACK_COL2", Fmt::Str, Cond::Eq, "备用字段2", false, false},
            {"backCol3", "BACK_COL3", Fmt::Str, Cond::Eq, "备用字段3", false, false},
        };
        s.orderBy = "t.create_time ASC ,t.id";
        s.excelSheetName = "审核历史记录";
        Perms p;
        p.list = "flow:flowlist:list";
        p.query = "flow:flowlist:query";
        registerCrud(r, "/flow/flowlist", s, p, "id");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowMessageDispose.java
        // ruoyi-system/src/main/resources/mapper/flow/FlowMessageDisposeMapper.xml
        Spec s;
        s.table = "flow_message_dispose";
        s.alias = "t";
        s.fields = {
            {"mid", "MID", Fmt::Str, Cond::Eq, "消息外键", false, false},
            {"bussId", "BUSS_ID", Fmt::Str, Cond::Eq, "处理对象ID", false, false},
            {"bussName", "BUSS_NAME", Fmt::Str, Cond::Eq, "处理对象名称", false, false},
            {"msgStatus", "MSG_STATUS", Fmt::Str, Cond::Eq, "消息状态", false, false},
            {"hangTime", "HANG_TIME", Fmt::DateIso, Cond::Eq, "处理时间", false, false},
            {"disposeOther", "DISPOSE_OTHER", Fmt::Str, Cond::Eq, "其他", false, false},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "系统消息处理人";
        Perms p;
        p.list = "flow:messagedispose:list";
        p.query = "flow:messagedispose:query";
        registerCrud(r, "/flow/messagedispose", s, p, "mid");
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowMessageInfo.java
        // ruoyi-system/src/main/resources/mapper/flow/FlowMessageInfoMapper.xml
        Spec s;
        s.table = "flow_message_info";
        s.alias = "t";
        s.fields = {
            {"messageNo", "message_no", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"billOid", "BILL_OID", Fmt::Str, Cond::Eq, "单据OID", false, false},
            {"bussType", "BUSS_TYPE", Fmt::Str, Cond::Eq, "业务类型-字典", false, false},
            {"flowRuid", "FLOW_RUID", Fmt::Str, Cond::Eq, "流程实例ID", false, false},
            {"msgTitle", "MSG_TITLE", Fmt::Str, Cond::Eq, "标题", false, false},
            {"msgContext", "MSG_CONTEXT", Fmt::Str, Cond::Eq, "内容", false, false},
            {"msgType", "MSG_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"msgUrl", "MSG_URL", Fmt::Str, Cond::Eq, "处理的URL", false, false},
            {"pcOid", "PC_OID", Fmt::Str, Cond::Eq, "批次OID", false, false},
            {"applyName", "APPLY_NAME", Fmt::Str, Cond::Eq, "申请人", false, false},
            {"backCol1", "BACK_COL1", Fmt::Str, Cond::Eq, "备用字段1", false, false},
            {"backCol2", "BACK_COL2", Fmt::Str, Cond::Eq, "备用字段2", false, false},
            {"backCol3", "BACK_COL3", Fmt::Str, Cond::Eq, "备用字段3", false, false},
        };
        s.orderBy = "t.create_time desc,t.id";
        s.excelSheetName = "系统内部消息";
        Perms p;
        p.query = "flow:messageinfo:query";
        registerCrud(r, "/flow/messageinfo", s, p, "id");
        registerListVariant(r, "/flow/messageinfo/listyb", s, ListKind::Paged);
        registerListVariant(r, "/flow/messageinfo/listyj", s, ListKind::Paged);
        registerListVariant(r, "/flow/messageinfo/listxx", s, ListKind::Paged);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowName.java
        // ruoyi-system/src/main/resources/mapper/flow/FlowNameMapper.xml
        Spec s;
        s.table = "flow_name";
        s.alias = "t";
        s.fields = {
            {"flowKey", "FLOW_KEY", Fmt::Str, Cond::Eq, "流程KEY", false, false},
            {"flowTitle", "FLOW_TITLE", Fmt::Str, Cond::Eq, "流程名称", false, false},
            {"flowContext", "FLOW_CONTEXT", Fmt::Str, Cond::Eq, "内容", false, false},
            {"bussName", "BUSS_NAME", Fmt::Str, Cond::Eq, "业务名称", false, false},
            {"flowBusinessType", "flow_business_type", Fmt::Str, Cond::Eq, nullptr, false, false},
        };
        s.orderBy = "t.tenant_id,t.flow_key,t.id";
        s.excelSheetName = "流程名称";
        Perms p;
        p.list = "flow:flowname:list";
        p.query = "flow:flowname:query";
        registerCrud(r, "/flow/flowname", s, p, "id");
        registerListVariant(r, "/flow/flowname/listQuery", s, ListKind::Paged);
    }
    {
        // ruoyi-system/src/main/java/com/ruoyi/flow/domain/FlowTemplate.java
        // ruoyi-system/src/main/resources/mapper/flow/FlowTemplateMapper.xml
        Spec s;
        s.table = "flow_template";
        s.alias = "t";
        s.fields = {
            {"flowOid", "FLOW_OID", Fmt::Str, Cond::Eq, "流程OID", false, false},
            {"flowType", "FLOW_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"nodeOrder", "NODE_ORDER", Fmt::Int, Cond::Eq, "节点顺序", false, false},
            {"nodeKey", "NODE_KEY", Fmt::Str, Cond::Eq, "节点KEY", false, false},
            {"nodeName", "NODE_NAME", Fmt::Str, Cond::Eq, "节点名称", false, false},
            {"nextNodeOid", "NEXT_NODE_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"previousNodeOid", "PREVIOUS_NODE_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"returnNum", "RETURN_NUM", Fmt::Int, Cond::Eq, "驳回到第几步 0 是发起人", false, false},
            {"returnNodeOid", "RETURN_NODE_OID", Fmt::Str, Cond::Eq, "驳回节点OID", false, false},
            {"configCondtion", "CONFIG_CONDTION", Fmt::Str, Cond::Eq, "节点配置条件", false, false},
            {"configType", "CONFIG_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false},
            {"configId", "CONFIG_ID", Fmt::Str, Cond::Eq, "节点配置id", false, false},
            {"configName", "CONFIG_NAME", Fmt::Str, Cond::Eq, "节点配置名称", false, false},
        };
        s.orderBy = "t.NODE_ORDER ,t.id";
        s.excelSheetName = "流程节点";
        Perms p;
        p.list = "flow:flowtemplate:list";
        p.query = "flow:flowtemplate:query";
        registerCrud(r, "/flow/flowtemplate", s, p, "id");
    }
}

} // namespace cm::web::crud
