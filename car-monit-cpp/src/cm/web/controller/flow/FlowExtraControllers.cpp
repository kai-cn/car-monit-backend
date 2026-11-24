// 对应 Java:
//   com.ruoyi.web.controller.flow.FlowListController#listnew
//   com.ruoyi.web.controller.flow.FlowTemplateController#flowlist
//   com.ruoyi.web.controller.flow.FlowMessageInfoController#exportShrz
//   com.ruoyi.web.controller.flow.FlowMessageDisposeController#removeFlowMessage / #szzdFlowMessage
//   com.ruoyi.web.controller.flow.FlowCurrentNodeController#getInfoByBillId
//
// 这里的实体都是 MyBatis-Plus + BaseUuidEntity 那一套，JSON 键序 = 父类声明序 + 子类声明序，
// 且 resultMap 没映射的属性（deptSubCode/flag/searchValue/params/roleId/...）照样输出 null，
// 所以下面的 spec 与 scripts/gen_crud_spec.py 生成的 FlowCrudSpecs.cpp 保持一致。
#include "cm/web/controller/flow/FlowExtraControllers.hpp"

#include <string>
#include <vector>

#include "cm/common/core/domain/AjaxResult.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/flow/service/FlowApprovalService.hpp"
#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/Router.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"
#include "cm/web/BaseController.hpp"

namespace cm::web {
namespace {

using cm::core::domain::AjaxResult;
using cm::db::Db;
using cm::security::SecurityUtils;
using cm::utils::StringUtils;
using namespace cm::web::crud;

/** BaseUuidEntity 的字段声明序（Jackson 先输出父类） */
const std::vector<Field> kBaseUuid = {
    {"id", "ID", Fmt::Str, Cond::None, nullptr, true, false, false, false},
    {"epsId", "eps_id", Fmt::Long, Cond::None, nullptr, false, false, false, false},
    {"delFlag", "del_flag", Fmt::Str, Cond::None, nullptr, false, false, false, false},
    {"createBy", "create_by", Fmt::Long, Cond::None, nullptr, false, false, false, false},
    {"createTime", "create_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false},
    {"updateBy", "update_by", Fmt::Long, Cond::None, nullptr, false, false, false, false},
    {"updateTime", "update_time", Fmt::DateYmdHms, Cond::None, nullptr, false, false, false, false},
    {"sort", "sort", Fmt::Int, Cond::None, nullptr, false, false, false, false},
    {"remark", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
    {"tenantId", nullptr, Fmt::Long, Cond::None, nullptr, false, false, false, false},
    {"deptSubCode", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
    {"flag", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
    {"searchValue", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
    {"params", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
};

Spec makeSpec(const char* table, std::vector<Field> own, std::string orderBy) {
    Spec s;
    s.table = table;
    s.alias = "t";
    s.fields = kBaseUuid;
    for (auto& f : own) s.fields.push_back(f);
    s.orderBy = std::move(orderBy);
    s.extraWhere = " and t.del_flag = '0'";  // XML 里写死的 where t.del_flag = '0'
    return s;
}

const Spec& flowListSpec() {
    static const Spec s = makeSpec("flow_list",
                                   {
                                       {"billOid", "BILL_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"bussType", "BUSS_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"taskId", "TASK_ID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"flowRuid", "flow_ruid", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"currentOid", "CURRENT_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"shUser", "SH_USER", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"shKey", "SH_KEY", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"shValue", "SH_VALUE", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"shContext", "SH_CONTEXT", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"backCol1", "BACK_COL1", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"backCol2", "BACK_COL2", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"backCol3", "BACK_COL3", Fmt::Str, Cond::Eq, nullptr, false, false},
                                   },
                                   "t.create_time ASC ,t.id");
    return s;
}

const Spec& flowApplyInfoSpec() {
    static const Spec s = makeSpec("flow_apply_info",
                                   {
                                       {"billOid", "BILL_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"bussType", "BUSS_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"flowRuid", "FLOW_RUID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"msgTitle", "MSG_TITLE", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"msgContext", "MSG_CONTEXT", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"msgType", "MSG_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"msgUrl", "MSG_URL", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"applyName", "APPLY_NAME", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"currentOid", "CURRENT_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"pcOid", "PC_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"backCol1", "BACK_COL1", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"backCol2", "BACK_COL2", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"backCol3", "BACK_COL3", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"flowStatus", "FLOW_STATUS", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       // selectFlowApplyInfoList 里额外投影了 t.BACK_COL1 auitEmpName，
                                       // 但 resultMap 没映射 -> Java 侧永远是 null
                                       {"auitEmpName", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
                                       {"entrustInfo", "entrust_info", Fmt::Str, Cond::Eq, nullptr, false, false},
                                   },
                                   "t.create_time desc,t.id");
    return s;
}

const Spec& flowTemplateSpec() {
    static const Spec s = makeSpec("flow_template",
                                   {
                                       {"flowOid", "FLOW_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"flowType", "FLOW_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"nodeOrder", "NODE_ORDER", Fmt::Int, Cond::Eq, nullptr, false, false},
                                       {"nodeKey", "NODE_KEY", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"nodeName", "NODE_NAME", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"nextNodeOid", "NEXT_NODE_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"previousNodeOid", "PREVIOUS_NODE_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"returnNum", "RETURN_NUM", Fmt::Int, Cond::Eq, nullptr, false, false},
                                       {"returnNodeOid", "RETURN_NODE_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"configCondtion", "CONFIG_CONDTION", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"configType", "CONFIG_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"configId", "CONFIG_ID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"configName", "CONFIG_NAME", Fmt::Str, Cond::Eq, nullptr, false, false},
                                   },
                                   "t.NODE_ORDER ,t.id");
    return s;
}

const Spec& flowCurrentNodeSpec() {
    static const Spec s = makeSpec("flow_current_node",
                                   {
                                       {"flowOid", "FLOW_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"currentOid", "CURRENT_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"nodeOrder", "NODE_ORDER", Fmt::Int, Cond::Eq, nullptr, false, false},
                                       {"nodeKey", "NODE_KEY", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"nodeName", "NODE_NAME", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"configType", "CONFIG_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"configId", "CONFIG_ID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"configName", "CONFIG_NAME", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"billOid", "BILL_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"auitEmpOid", "AUIT_EMP_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"auitEmpName", "AUIT_EMP_NAME", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"backCol1", "BACK_COL1", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"backCol2", "BACK_COL2", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"backCol3", "BACK_COL3", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       // 以下都是实体上的查询辅助字段，不是表列
                                       {"roleId", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
                                       {"tableName", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
                                       {"projectId", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
                                       {"flowKey", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
                                       {"flowRuid", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
                                       {"flowApplyOid", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
                                       {"flowStatus", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
                                       {"shValue", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
                                       {"shContext", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
                                       {"entrustUserId", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
                                       {"entrustUserName", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
                                       {"roleKey", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
                                       {"deptId", nullptr, Fmt::Long, Cond::None, nullptr, false, false, false, false},
                                   },
                                   "t.create_time desc,t.id");
    return s;
}

const Spec& flowMessageInfoSpec() {
    static const Spec s = makeSpec("flow_message_info",
                                   {
                                       {"messageNo", "message_no", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"billOid", "BILL_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"bussType", "BUSS_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"flowRuid", "FLOW_RUID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"msgTitle", "MSG_TITLE", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"msgContext", "MSG_CONTEXT", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"msgType", "MSG_TYPE", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"msgUrl", "MSG_URL", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"pcOid", "PC_OID", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"applyName", "APPLY_NAME", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"backCol1", "BACK_COL1", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"backCol2", "BACK_COL2", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"backCol3", "BACK_COL3", Fmt::Str, Cond::Eq, nullptr, false, false},
                                       {"userId", nullptr, Fmt::Long, Cond::None, nullptr, false, false, false, false},
                                       {"msgStatus", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
                                       {"flowStatus", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
                                       {"curEmpNames", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
                                       {"disposeList", nullptr, Fmt::Str, Cond::None, nullptr, false, false, false, false},
                                   },
                                   "t.create_time desc,t.id");
    return s;
}

/** new XxxEntity() 的 JSON 形态：全部键都在、值为 null */
Json skeleton(const Spec& spec) {
    Json j = Json::object();
    for (const auto& f : spec.fields) j[f.json] = nullptr;
    return j;
}

cm::db::Result selectAll(const std::string& sql) {
    cm::db::Result res;
    Db::instance().query(sql, res);
    return res;
}

std::string selectAllSql(const Spec& spec, const std::string& where) {
    return "SELECT " + spec.selectColumns() + " FROM " + spec.table + " " + spec.alias + " " + where +
           (spec.orderBy.empty() ? std::string() : (" ORDER BY " + spec.orderBy));
}

/** 对应 CommonUtil.isNull(Object)：null -> ""，否则 toString().trim() */
std::string trimOrNull(const std::optional<std::string>& v) {
    if (!v) return std::string();
    return StringUtils::trim(*v);
}

} // namespace

void registerFlowExtraControllers(Router& r) {
    // GET /flow/flowlist/listnew —— 审批历史 + 依据我的申请状态补一个伪行
    r.get("/flow/flowlist/listnew", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string billOid = ctx.optParam("billOid").value_or("");
        if (billOid.empty()) billOid = "-1";  // Java: setBillOid("-1")，保证查不到而不是查全表

        Json arr = Json::array();
        const auto& ls = flowListSpec();
        auto rows = selectAll(selectAllSql(ls, "WHERE t.BILL_OID = " + cm::db::bind(billOid)));
        for (const auto& row : rows.rows) arr.push_back(rowToJson(ls, row));

        const auto& as = flowApplyInfoSpec();
        auto applyRows = selectAll(selectAllSql(as, "WHERE t.BILL_OID = " + cm::db::bind(billOid)));
        if (!applyRows.rows.empty()) {
            const auto& apply = applyRows.rows[0];
            const std::string status = trimOrNull(apply.get("FLOW_STATUS"));
            const std::string auitEmpName = trimOrNull(apply.get("BACK_COL1"));
            if (status == "2") {  // FlowTypeEnum.APPROVE
                if (!auitEmpName.empty()) {
                    Json add = skeleton(ls);
                    add["shUser"] = auitEmpName;
                    add["shValue"] = "待审批";
                    arr.push_back(std::move(add));
                }
            } else if (status == "3") {  // FlowTypeEnum.END
                Json add = skeleton(ls);
                add["shValue"] = "流程结束";
                arr.push_back(std::move(add));
            }
        }
        return BaseController::ok(AjaxResult::success(arr));
    });

    // GET /flow/flowtemplate/flowlist —— 未传 flowOid 时返回空数组（Java 的 if 包住整段查询）
    r.get("/flow/flowtemplate/flowlist", [](RequestContext& ctx) -> cm::http::ApiResponse {
        Json rtn = Json::array();
        Json query = bindQuery(flowTemplateSpec(), ctx);
        const std::string flowOid = query.contains("flowOid") && query["flowOid"].is_string()
                                        ? query["flowOid"].get<std::string>()
                                        : std::string();
        if (!StringUtils::isBlank(flowOid)) {
            const auto& ts = flowTemplateSpec();
            auto rows = selectAll(selectAllSql(ts, buildWhere(ts, query)));
            // 首元素是 new FlowTemplate() 手工填的“申请人提交”节点
            Json first = skeleton(ts);
            first["id"] = "-1";
            first["nodeOrder"] = -1;
            first["nodeKey"] = "tj";
            first["nodeName"] = "申请人提交";
            rtn.push_back(std::move(first));
            for (const auto& row : rows.rows) rtn.push_back(rowToJson(ts, row));
        }
        return BaseController::ok(AjaxResult::success(rtn));
    });

    // GET /flow/currentnode/getInfoByBillId/{billOid}
    // 注意：查不到时 Java 返回的是那个只带 billOid 的查询对象（其余字段全 null），不是 null
    r.get("/flow/currentnode/getInfoByBillId/{billOid}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const auto& ns = flowCurrentNodeSpec();
        Json query = Json::object();
        query["billOid"] = ctx.pathVar("billOid");
        auto rows = selectAll(selectAllSql(ns, buildWhere(ns, query)));
        Json node = rows.rows.empty() ? skeleton(ns) : rowToJson(ns, rows.rows[0]);
        if (rows.rows.empty()) node["billOid"] = ctx.pathVar("billOid");
        return BaseController::ok(AjaxResult::success(node));
    });

    // DELETE /flow/messagedispose/delmes/{mid} —— 删除“自己”的那条处理记录
    r.del("/flow/messagedispose/delmes/{mid}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string mid = ctx.pathVar("mid");
        if (mid.empty()) mid = "-1";
        std::string sql = "delete from flow_message_dispose where MID = " + cm::db::bind(mid);
        const std::string bussId = std::to_string(SecurityUtils::getUserId());
        if (!bussId.empty()) sql += " and BUSS_ID = " + cm::db::bind(bussId);
        long long affected = 0;
        Db::instance().execute(sql, &affected);
        return BaseController::ok(AjaxResult::success(Json(affected)));
    });

    // DELETE /flow/messagedispose/szzdmes/{mid} —— 把“自己”的待办置为已读
    r.del("/flow/messagedispose/szzdmes/{mid}", [](RequestContext& ctx) -> cm::http::ApiResponse {
        std::string mid = ctx.pathVar("mid");
        if (mid.empty()) mid = "-1";
        std::string sql = "update flow_message_dispose set MSG_STATUS = '1' where del_flag = '0' and MID = " +
                          cm::db::bind(mid);
        const std::string bussId = std::to_string(SecurityUtils::getUserId());
        if (!bussId.empty()) sql += " and BUSS_ID = " + cm::db::bind(bussId);
        long long affected = 0;
        Db::instance().execute(sql, &affected);
        return BaseController::ok(AjaxResult::success(Json(affected)));
    });

    // GET /flow/messageinfo/exportShrz —— 模板 export/exportShrz.xlsx 在 Java 仓库里并不存在，    // ExcelExportUtil 抛异常被 catch 后 printStackTrace，方法 `return null` => 200 + 空 body。
    // 这里保持同样的可观测行为：照常执行两条查询（查不到消息体会 NPE -> 500），然后回空。
    r.get("/flow/messageinfo/exportShrz", [](RequestContext& ctx) -> cm::http::ApiResponse {
        const auto& ms = flowMessageInfoSpec();
        const std::string id = ctx.optParam("id").value_or("");
        auto infoRows = selectAll("SELECT " + ms.selectColumns() + " FROM flow_message_info t WHERE t.ID = " +
                                  cm::db::bind(id));
        if (infoRows.rows.empty()) {
            // Java: messageInfo.getApplyName() 对 null 调用 -> NullPointerException -> 500
            throw cm::exception::NullPointerException();
        }
        const auto& msg = infoRows.rows[0];
        Json map = Json::object();
        map["applyName"] = Json(msg.get("APPLY_NAME").value_or(""));
        if (auto ct = msg.get("create_time")) {
            auto ms2 = utils::DateUtils::parseDbDateTime(*ct);
            map["createTime"] = ms2 ? Json(utils::DateUtils::formatMillis(*ms2, utils::DateUtils::YYYY_MM_DD))
                                    : Json(*ct);
        } else {
            map["createTime"] = nullptr;
        }
        map["msgTitle"] = Json(msg.get("MSG_TITLE").value_or(""));

        const auto& ls = flowListSpec();
        Json query = bindQuery(ls, ctx);
        auto listRows = selectAll(selectAllSql(ls, buildWhere(ls, query)));
        Json entitylist = Json::array();
        int i = 0;
        for (const auto& row : listRows.rows) {
            Json j = rowToJson(ls, row);
            j["sort"] = ++i;  // Java: fl.setSort(i + 1)
            entitylist.push_back(std::move(j));
        }
        map["entitylist"] = std::move(entitylist);

        // ⚠️ 与 Java 唯一可见差异：Spring 此时不写 Content-Type，这里只能留一个空值
        cm::http::ApiResponse empty = cm::http::ApiResponse::text("", "");
        (void)map;
        return empty;
    });

    // ---- 审批三件套：实现在 src/cm/flow/service/FlowApprovalService.cpp ----
    // Java 侧这三个方法都没有 @PreAuthorize，靠全局 authenticated 兜底

    // PUT /flow/currentnode/saveFlowAuit
    r.put("/flow/currentnode/saveFlowAuit", [](RequestContext& ctx) -> cm::http::ApiResponse {
        return BaseController::ok(cm::flow::service::saveFlowAuit(ctx.body()));
    });

    // POST /flow/currentnode/submitReturn
    r.post("/flow/currentnode/submitReturn", [](RequestContext& ctx) -> cm::http::ApiResponse {
        return BaseController::ok(cm::flow::service::submitReturn(ctx.body()));
    });

    // POST /flow/currentnode/submitEntrustFlow
    r.post("/flow/currentnode/submitEntrustFlow", [](RequestContext& ctx) -> cm::http::ApiResponse {
        return BaseController::ok(cm::flow::service::submitEntrustFlow(ctx.body()));
    });

    // POST /flow/flowname/tbFlow —— 同步其他单位的工作流（有 @PreAuthorize + @Log）
    r.post("/flow/flowname/tbFlow", [](RequestContext& ctx) -> cm::http::ApiResponse {
        // Java 是 @RequestBody FlowName：请求体必须是合法 JSON（内容不参与逻辑），
        // 所以这里照样先解析一次，缺体/坏体才能与 Java 一样报错。
        const Json body = ctx.body();
        (void)body;
        return BaseController::ok(cm::flow::service::tbFlow());
    }).permi("flow:flowname:edit");
}

} // namespace cm::web
