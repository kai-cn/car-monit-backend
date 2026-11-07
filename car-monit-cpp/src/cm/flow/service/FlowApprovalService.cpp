// 对应 Java: com.ruoyi.flow.service.impl.FlowCurrentNodeServiceImpl
//            #saveFlowAuit / #submitReturn / #submitEntrustFlow
//            以及依赖的 Flow{MessageInfo,ApplyInfo,List,MessageDispose}ServiceImpl 落库套路
//
// 实现取向：流程实体一律用 Json 表示（键 = Java 属性名），落库交给 CRUD 引擎的
// buildInsert/buildUpdate —— 它们已按 MyBatis 的"非 null 才写"以及各 XML
// insertXxx/updateXxx 的列集合实现，比在这里手写 40 列 INSERT 更不容易抄错。
// 三个入口都用 cm::db::Transaction 包住，对应 Java 的
// @Transactional(rollbackFor = Exception.class)：中途抛异常整笔回滚。
#include "cm/flow/service/FlowApprovalService.hpp"

#include <chrono>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

#include "cm/common/constant/Constants.hpp"
#include "cm/common/exception/Exceptions.hpp"
#include "cm/common/utils/DateUtils.hpp"
#include "cm/common/utils/IdUtils.hpp"
#include "cm/common/utils/JsonUtils.hpp"
#include "cm/common/utils/StringUtils.hpp"
#include "cm/framework/db/Db.hpp"
#include "cm/framework/security/SecurityUtils.hpp"
#include "cm/framework/web/crud/CrudSpec.hpp"
#include "cm/system/service/SysDeptService.hpp"
#include "cm/web/specs/FlowCrudSpecs.hpp"

namespace cm::flow::service {
namespace {

using cm::constant::Constants;
using cm::core::domain::AjaxResult;
using cm::db::Db;
using cm::security::SecurityUtils;
using cm::utils::StringUtils;
using cm::web::crud::Spec;
using Json = cm::Json;

Json obj() { return Json::object(); }

/** Java 的 MyBatis 写语句失败会抛异常，进而被 @Transactional 回滚；
 *  这里绝不能把失败吞成"继续往下走"，否则半笔审批会被提交。 */
void mustExec(const std::string& sql) {
    if (!Db::instance().execute(sql))
        throw std::runtime_error("SQL 执行失败（事务回滚）: " + sql);
}
void mustExec(const std::string& sql, const cm::db::Params& params) {
    if (!Db::instance().execute(sql, params))
        throw std::runtime_error("SQL 执行失败（事务回滚）: " + sql);
}

/** Java 的 isEmpty(String)：null 与 "" 同等 */
bool isEmpty(const Json& j, const std::string& key) {
    auto it = j.find(key);
    if (it == j.end() || it->is_null()) return true;
    if (it->is_string()) return it->get<std::string>().empty();
    return false;
}

std::string sOf(const Json& j, const std::string& key) { return cm::jstr(j, key.c_str(), ""); }

/** Java: DateUtils.getTimestamp()，最终由 MyBatis 落成 'yyyy-MM-dd HH:mm:ss' */
std::string nowStamp() {
    const auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                        std::chrono::system_clock::now().time_since_epoch())
                        .count();
    return cm::utils::DateUtils::formatJsonDate(ms);
}

/** 对应 <include refid="selectXxxVo"/> + from <table> t + 调用方给的 where/order */
std::vector<Json> selectRows(const Spec& sp, const std::string& where, const cm::db::Params& params,
                             const std::string& order) {
    std::string sql = "SELECT " + sp.selectColumns() + " FROM " + sp.table + " " + sp.alias;
    if (!where.empty()) sql += " " + where;
    if (!order.empty()) sql += " ORDER BY " + order;
    cm::db::Result res;
    std::vector<Json> out;
    if (Db::instance().query(sql, params, res))
        for (const auto& row : res.rows) out.push_back(cm::web::crud::rowToJson(sp, row));
    return out;
}

std::optional<Json> selectOne(const Spec& sp, const std::string& where, const cm::db::Params& params,
                              const std::string& order) {
    auto rows = selectRows(sp, where, params, order);
    if (rows.empty()) return std::nullopt;
    return rows.front();
}

/** 对应 selectXxxById：where t.ID = ? —— Java 的 by-id 语句不过滤 del_flag */
std::optional<Json> byId(const Spec& sp, const std::string& id) {
    cm::db::Params params;
    return selectOne(sp, "WHERE " + sp.alias + ".ID = " + cm::db::bind(params, id), params, std::string());
}

/** 对应 selectXxxList：del_flag 过滤在 spec.extraWhere，动态条件在 <if> */
std::vector<Json> listBy(const Spec& sp, const Json& query) {
    cm::db::Params params;
    const std::string where = cm::web::crud::buildWhere(sp, query, params);
    return selectRows(sp, where, params, sp.orderBy);
}

/** 对应各 ServiceImpl 的 save-or-update：id 有值走 update，否则补主键与审计列后 insert。
 *  返回落库使用的主键（这些 service 都把 id 回传给调用方）。 */
std::string saveEntity(const Spec& sp, Json body) {
    const long long userId = SecurityUtils::getUserId();
    const std::string ts = nowStamp();
    if (!isEmpty(body, "id")) {
        body["updateBy"] = userId;
        body["updateTime"] = ts;
        cm::db::Params params;
        mustExec(cm::web::crud::buildUpdate(sp, body, params), params);
    } else {
        body["id"] = cm::utils::simpleUuid();  // Java: StringUtils.getUUID() —— 32 位无横线
        body["delFlag"] = "0";
        body["epsId"] = SecurityUtils::getEpsId();
        body["createBy"] = userId;
        body["createTime"] = ts;
        body["updateBy"] = userId;
        body["updateTime"] = ts;
        cm::db::Params params;
        mustExec(cm::web::crud::buildInsert(sp, body, params), params);
    }
    return sOf(body, "id");
}

/** FlowMessageInfoServiceImpl.saveFlowMessageInfo：先按 billOid+msgType+bussType 找已有消息 */
std::string saveMessageInfo(Json body) {
    Json probe = obj();
    probe["billOid"] = sOf(body, "billOid");
    probe["msgType"] = sOf(body, "msgType");
    if (!isEmpty(body, "bussType")) probe["bussType"] = body["bussType"];
    auto found = listBy(cm::web::crud::specFlowMessageInfo(), probe);
    if (!found.empty()) body["id"] = found[0]["id"];
    return saveEntity(cm::web::crud::specFlowMessageInfo(), body);
}

/** FlowApplyInfoServiceImpl.saveFlowApplyInfoNew：先按 billOid 找已有申请 */
std::string saveApplyInfoNew(Json body) {
    Json probe = obj();
    probe["billOid"] = sOf(body, "billOid");
    auto found = listBy(cm::web::crud::specFlowApplyInfo(), probe);
    if (!found.empty()) body["id"] = found[0]["id"];
    return saveEntity(cm::web::crud::specFlowApplyInfo(), body);
}

/** 对应 flowCurrentNodeMapper.deleteByBillId */
void deleteNodesByBillId(const std::string& billOid) {
    mustExec("delete from flow_current_node where BILL_OID = " + cm::db::bind(billOid));
}

/** 对应 removeFlowMessage(mid, bussId)：bussId 为空时删该消息的全部处理人 */
void removeFlowMessage(const std::string& mid, const std::string& bussId) {
    std::string sql = "delete from flow_message_dispose where MID = " + cm::db::bind(mid);
    if (!bussId.empty()) sql += " and BUSS_ID = " + cm::db::bind(bussId);
    mustExec(sql);
}

/** 对应 saveSzzdFlowMessageAll：把该消息所有未处理待办置已读并归到某人 */
void saveSzzdFlowMessageAll(const std::string& mid, const std::string& bussId) {
    mustExec("update flow_message_dispose set MSG_STATUS = '1', BUSS_ID = " +
                           cm::db::bind(bussId) + " where del_flag = '0' and MID = " + cm::db::bind(mid) +
                           " and MSG_STATUS = '2'");
}

/** 对应 FlowMessageDisposeServiceImpl.saveFlowList(mid, userIds)：先删后插，状态 2 = 未处理 */
void saveDisposeList(const std::string& mid, const std::vector<std::string>& userIds) {
    for (const auto& uid : userIds) {
        removeFlowMessage(mid, uid);
        Json bo = obj();
        bo["mid"] = mid;
        bo["msgStatus"] = "2";
        bo["bussId"] = uid;
        saveEntity(cm::web::crud::specFlowMessageDispose(), bo);
    }
}

/** 对应 FlowCurrentNodeServiceImpl.saveFlowList(template, billOid, flowKey, auitResult, ctx) */
void saveFlowListRecord(const Json& tp, const std::string& billOid, const std::string& flowKey,
                        const std::string& auitResult, const std::string& auitContext) {
    Json bo = obj();
    bo["billOid"] = billOid;
    bo["bussType"] = flowKey;
    bo["flowRuid"] = sOf(tp, "flowOid");
    bo["currentOid"] = sOf(tp, "id");
    bo["shUser"] = SecurityUtils::getUserRealName();
    bo["shKey"] = auitResult;
    std::string shValue;
    if (auitResult == "S") shValue = "提交";
    else if (auitResult == "T") shValue = "同意";
    else if (auitResult == "F") shValue = "拒绝";
    else if (auitResult == "R") shValue = "退回";
    else if (auitResult == Constants::FLOW_RESULT_ENTRUST_KEY) shValue = Constants::FLOW_ENTRUST_NAME;
    if (!shValue.empty()) bo["shValue"] = shValue;
    if (!auitContext.empty()) bo["shContext"] = auitContext;
    saveEntity(cm::web::crud::specFlowList(), bo);
}

/** 表名来自 flow_name.BUSS_NAME，Java 用 ${} 直接拼进 SQL；这里挡掉非法标识符，
 *  真出现非法值时抛异常（Java 那边是 MySQL 报错 -> 500，可观测结果同为 500） */
void requireTableName(const std::string& table) {
    if (table.empty()) throw std::runtime_error("java.lang.NullPointerException: tableName");
    for (unsigned char c : table) {
        if (!std::isalnum(c) && c != '_') throw std::runtime_error("bad table name: " + table);
    }
}

/** 对应 flowCurrentNodeMapper.updateFlowTable —— 只写非 null 的几个流程字段 */
void updateFlowTable(const std::string& tableName, const std::string& billOid,
                     const std::string& flowStatus) {
    requireTableName(tableName);
    std::string set = "flow_status = " + cm::db::bind(flowStatus) + ", ";
    if (flowStatus == "3")  // Java: <if test="flowStatus != null and flowStatus == 3">sh_time = now(),</if>
        set = "flow_status = " + cm::db::bind(flowStatus) + ", sh_time = now(), ";
    mustExec("update " + tableName + " set " + set + "update_time = now() where id = " +
                           cm::db::bind(billOid));
}

/** 对应 flowNameMapper.selectFlowNameById 之后的三处取键，null 会让 Java NPE */
std::string requireText(const Json& j, const std::string& key) {
    auto it = j.find(key);
    if (it == j.end() || it->is_null()) throw cm::exception::NullPointerException();
    return it->is_string() ? it->get<std::string>() : it->dump();
}

/** 对应 sysRoleMapper.selectRoleById(Long)：configId 非数字时 Java 抛 NumberFormatException */
std::optional<Json> selectRole(const std::string& configId) {
    if (!StringUtils::isNumeric(configId))
        throw std::runtime_error("java.lang.NumberFormatException: For input string: \"" + configId + "\"");
    cm::db::Result res;
    const std::string sql = "select r.role_id, r.role_key from sys_role r where r.role_id = " +
                            cm::db::bind(static_cast<long long>(std::stoll(configId)));
    if (!Db::instance().query(sql, res) || res.rows.empty()) return std::nullopt;
    Json j = obj();
    j["roleId"] = res.rows[0].i64("role_id");
    j["roleKey"] = res.rows[0].str("role_key");
    return j;
}

/** 对应 flowCurrentNodeMapper.selectEmpInfoList —— 按 flag 分支决定"部门领导/分管领导/值班人/角色" */
std::vector<Json> selectEmpInfoList(const Json& q) {
    std::string sql = "select t.user_id AUIT_EMP_OID, t.nick_name AUIT_EMP_NAME from sys_user t"
                      " where t.del_flag = '0' and t.status = '0'";
    const std::string roleId = sOf(q, "roleId");
    const std::string flag = sOf(q, "flag");
    const std::string backCol1 = sOf(q, "backCol1");
    const std::string billOid = sOf(q, "billOid");

    if (!roleId.empty())
        sql += " and exists (select 1 from sys_user_role t1 where t1.user_id = t.user_id and t1.role_id = " +
               cm::db::bind(roleId) + ")";
    if (!isEmpty(q, "tenantId"))
        sql += " and exists (select 1 from sys_dept td where td.del_flag = '0' and td.dept_id = t.dept_id"
               " and td.tenant_id = " + cm::db::bind(cm::jlong(q, "tenantId")) + ")";
    if (!isEmpty(q, "deptId"))
        sql += " and t.dept_id = " + cm::db::bind(cm::jlong(q, "deptId"));

    if (flag == "dutyAudit") {
        requireTableName(backCol1);  // 这里 backCol1 装的是业务表名
        sql += " and t.dept_id in (select tp.borrow_dept_id from " + backCol1 +
               " tp where tp.id = " + cm::db::bind(billOid) + ")";
    } else if (flag == "bmjlAudit") {
        sql += " AND EXISTS (SELECT 1 FROM sys_dept ds WHERE ds.del_flag = '0' AND ds.dept_id ="
               " (SELECT tt.dept_id FROM sys_user tt WHERE tt.user_id = " + cm::db::bind(backCol1) +
               ") AND ds.leader_id = t.user_id)";
    } else if (flag == "fgldAudit") {
        sql += " AND EXISTS (SELECT 1 FROM sys_dept ds WHERE ds.del_flag = '0' AND ds.dept_id ="
               " (SELECT tt.dept_id FROM sys_user tt WHERE tt.user_id = " + cm::db::bind(backCol1) +
               ") AND ds.fgld_id = t.user_id)";
    }

    cm::db::Result res;
    std::vector<Json> out;
    if (!Db::instance().query(sql, res)) return out;
    for (const auto& row : res.rows) {
        Json bo = obj();
        bo["auitEmpOid"] = row.str("AUIT_EMP_OID");
        bo["auitEmpName"] = row.get("AUIT_EMP_NAME") ? Json(row.str("AUIT_EMP_NAME")) : Json(nullptr);
        out.push_back(std::move(bo));
    }
    return out;
}

/** 对应 getEmpInfoList：configType 1=指定人，其余按角色找 */
std::vector<Json> getEmpInfoList(const std::string& bussTableName, const Json& tp,
                                 const std::string& billOid) {
    std::vector<Json> list;
    const std::string configType = StringUtils::trim(sOf(tp, "configType"));
    const std::string configId = StringUtils::trim(sOf(tp, "configId"));
    if (configId.empty()) return list;

    if (configType == "1") {
        Json bo = obj();
        bo["auitEmpOid"] = configId;
        bo["auitEmpName"] = tp.contains("configName") ? tp["configName"] : Json(nullptr);
        list.push_back(std::move(bo));
        return list;
    }

    Json q = obj();
    q["roleId"] = configId;
    q["billOid"] = billOid;

    auto role = selectRole(configId);
    if (role && !isEmpty(*role, "roleId")) {
        const std::string roleKey = sOf(*role, "roleKey");
        const std::string userId = std::to_string(SecurityUtils::getUserId());
        if (roleKey == Constants::dept_manager_role) {
            q["flag"] = "bmjlAudit";
            q["roleId"] = "";
            q["backCol1"] = userId;
        } else if (roleKey == Constants::dept_fg_manager_role) {
            q["flag"] = "fgldAudit";
            q["roleId"] = "";
            q["backCol1"] = userId;
        } else if (roleKey == Constants::dept_duty_emp_role) {
            q["flag"] = "dutyAudit";
            q["backCol1"] = bussTableName;  // 值班人按业务表里的借用部门定位
        }
        list = selectEmpInfoList(q);
    }
    return list;
}

/** 对应 getEmpInfoListReturn：退回时把审批人找回上一节点的实际审批人 */
std::vector<Json> getEmpInfoListReturn(const Json& tp, const std::string& billOid) {
    std::vector<Json> list;
    Json q = obj();
    q["billOid"] = billOid;
    q["currentOid"] = sOf(tp, "id");
    cm::db::Params params;
    auto rows = selectRows(cm::web::crud::specFlowList(),
                           cm::web::crud::buildWhere(cm::web::crud::specFlowList(), q, params), params,
                           "t.create_time desc ,t.id");  // selectFlowListListNew 的排序
    if (rows.empty()) return list;
    const Json& src = rows.front();
    Json bo = obj();
    // Java: empFlowCurrentNode.setAuitEmpOid(tlistvo.getCreateBy() + "") —— null 会拼成 "null"
    bo["auitEmpOid"] = isEmpty(src, "createBy") ? "null" : src["createBy"].dump();
    bo["auitEmpName"] = src.contains("shUser") ? src["shUser"] : Json(nullptr);
    list.push_back(std::move(bo));
    return list;
}

/** 对应 saveFlowNode：给下一节点的每个审批人插一条 flow_current_node */
void saveFlowNode(const Json& tp, const std::vector<Json>& empList, const std::string& billOid,
                  const std::string& projectId) {
    for (const auto& emp : empList) {
        Json node = obj();
        node["billOid"] = billOid;
        for (const char* k : {"flowOid", "nodeOrder", "nodeKey", "nodeName", "configType", "configId",
                              "configName"}) {
            if (tp.contains(k) && !tp[k].is_null()) node[k] = tp[k];
        }
        node["currentOid"] = sOf(tp, "id");
        if (emp.contains("auitEmpOid") && !emp["auitEmpOid"].is_null())
            node["auitEmpOid"] = emp["auitEmpOid"];
        if (emp.contains("auitEmpName") && !emp["auitEmpName"].is_null())
            node["auitEmpName"] = emp["auitEmpName"];
        if (!projectId.empty()) node["backCol1"] = projectId;  // 项目权限字段
        saveEntity(cm::web::crud::specFlowCurrentNode(), node);
    }
}

/** 拼审批人名（Java 是逐个 += name + "," 再截掉尾逗号，因此 null 会变成 "null,"） */
std::string joinAuitNames(const std::vector<Json>& empList) {
    std::string out;
    for (const auto& e : empList) out += sOf(e, "auitEmpName") + ",";
    if (StringUtils::endsWith(out, ",")) out = out.substr(0, out.size() - 1);
    return out;
}

std::vector<std::string> collectIds(const std::vector<Json>& empList) {
    std::vector<std::string> ids;
    for (const auto& e : empList) ids.push_back(sOf(e, "auitEmpOid"));
    return ids;
}

} // namespace

AjaxResult saveFlowAuit(const Json& body) {
    cm::db::Transaction tx;
    std::string shValue = sOf(body, "shValue");
    const std::string billOid = sOf(body, "billOid");
    std::string projectId;
    std::string flowStatus = "2";  // FlowTypeEnum.APPROVE

    // Java: StringUtils.isNotNull(shValue) 才做映射，"1"同意 "2"拒绝 "3"退回
    if (!body.contains("shValue") || body["shValue"].is_null()) shValue.clear();
    if (!shValue.empty()) {
        if (shValue == "1") shValue = "T";
        else if (shValue == "2") {
            shValue = "F";
            flowStatus = "5";  // FlowTypeEnum.STOP
        } else if (shValue == "3") shValue = "R";
    }
    if (shValue.empty()) return AjaxResult::error("请填写审核结论！");
    if (billOid.empty()) return AjaxResult::error("业务不存在！");

    Json query = obj();
    query["billOid"] = billOid;
    query["auitEmpOid"] = std::to_string(SecurityUtils::getUserId());
    auto currentList = listBy(cm::web::crud::specFlowCurrentNode(), query);
    if (currentList.empty()) return AjaxResult::error("对不起，该单据已审核，请确定！");
    const Json current = currentList.front();
    if (!isEmpty(current, "backCol1")) projectId = sOf(current, "backCol1");

    auto curTp = byId(cm::web::crud::specFlowTemplate(), sOf(current, "currentOid"));
    if (!curTp) throw cm::exception::NullPointerException();
    const std::string nextNodeOid = requireText(*curTp, "nextNodeOid");
    const std::string previousNodeOid = requireText(*curTp, "previousNodeOid");

    auto flowName = byId(cm::web::crud::specFlowName(), sOf(*curTp, "flowOid"));
    if (!flowName) throw cm::exception::NullPointerException();

    Json nextTp = obj();
    std::vector<Json> empList;
    if (nextNodeOid != "-1" && shValue == "T") {
        auto nt = byId(cm::web::crud::specFlowTemplate(), nextNodeOid);
        if (nt && !isEmpty(*nt, "id")) {
            nextTp = *nt;
            empList = getEmpInfoList(sOf(*flowName, "bussName"), nextTp, billOid);
            if (empList.empty()) return AjaxResult::error("该业务找不到下一审批人，请与管理员联系！");
        } else {
            return AjaxResult::error("下一个节点不存在，请与管理员联系！");
        }
    } else if (previousNodeOid != "0" && shValue == "R") {
        auto nt = byId(cm::web::crud::specFlowTemplate(), previousNodeOid);
        if (nt && !isEmpty(*nt, "id")) {
            nextTp = *nt;
            empList = getEmpInfoListReturn(nextTp, billOid);
            if (empList.empty()) return AjaxResult::error("该业务找不到下一审批人，请与管理员联系！");
        } else {
            return AjaxResult::error("退回节点不存在，请与管理员联系！");
        }
    }

    const std::string auitNames = joinAuitNames(empList);
    const std::vector<std::string> useIds = collectIds(empList);

    if (nextNodeOid == "-1" && shValue == "T") flowStatus = "3";        // END
    if (previousNodeOid == "0" && shValue == "R") flowStatus = "4";     // RETURN

    const std::string bussTypeName = sOf(*flowName, "flowTitle");
    const std::string tableName = sOf(*flowName, "bussName");
    const std::string flowKey = sOf(*flowName, "flowKey");
    const std::string flowRuid = sOf(*flowName, "id");

    // 先删当前节点，再改写消息主体、把待办全部归到自己
    deleteNodesByBillId(billOid);
    Json msgBo = obj();
    msgBo["billOid"] = billOid;
    msgBo["msgType"] = "2";
    const std::string mid = saveMessageInfo(msgBo);
    saveSzzdFlowMessageAll(mid, std::to_string(SecurityUtils::getUserId()));

    Json applyBo = obj();
    applyBo["billOid"] = billOid;
    applyBo["flowStatus"] = flowStatus;
    if (!auitNames.empty()) applyBo["backCol1"] = auitNames;
    const std::string flowApplyOid = saveApplyInfoNew(applyBo);

    auto apply = byId(cm::web::crud::specFlowApplyInfo(), flowApplyOid);
    if (!apply) throw cm::exception::NullPointerException();
    const std::string applyId =
        isEmpty(*apply, "createBy") ? "null" : (*apply)["createBy"].dump();

    updateFlowTable(tableName, billOid, flowStatus);
    saveFlowListRecord(*curTp, billOid, flowKey, shValue, sOf(body, "shContext"));
    saveFlowNode(nextTp, empList, billOid, projectId);
    saveDisposeList(mid, useIds);

    std::string msgTitle;
    if (flowStatus == "3") msgTitle = "你提交的" + bussTypeName + "业务已通过，请查看！";
    else if (flowStatus == "5") msgTitle = "你提交的" + bussTypeName + "业务已拒绝，请查看！";
    else if (flowStatus == "4") msgTitle = "你提交的" + bussTypeName + "业务已退回，请查看！";
    // Java 的三个业务回调分支（专家/设备/资源申请）在源码里是注释掉的空实现，这里同样不做事

    if (!msgTitle.empty()) {
        Json gr = obj();
        gr["billOid"] = billOid;
        gr["bussType"] = flowKey;
        gr["flowRuid"] = flowRuid;
        gr["msgType"] = "1";
        gr["msgTitle"] = msgTitle;
        const std::string grmid = saveMessageInfo(gr);
        saveDisposeList(grmid, {applyId});
    }

    tx.commit();
    return AjaxResult::success("审核成功！");
}

AjaxResult submitReturn(const Json& body) {
    cm::db::Transaction tx;
    const std::string billOid = sOf(body, "billOid");
    if (billOid.empty()) return AjaxResult::error("业务不存在！");

    Json query = obj();
    query["billOid"] = billOid;
    auto currentList = listBy(cm::web::crud::specFlowCurrentNode(), query);
    if (currentList.empty()) return AjaxResult::error("撤销失败，该单据已撤销，请确定！");
    const Json current = currentList.front();

    auto curTp = byId(cm::web::crud::specFlowTemplate(), sOf(current, "currentOid"));
    if (!curTp) throw cm::exception::NullPointerException();
    const std::string previousNodeOid = requireText(*curTp, "previousNodeOid");
    if (previousNodeOid != "0") return AjaxResult::error("撤销失败，该单据已审核，请确定！");

    auto flowName = byId(cm::web::crud::specFlowName(), sOf(*curTp, "flowOid"));
    if (!flowName) throw cm::exception::NullPointerException();

    deleteNodesByBillId(billOid);

    Json msgQuery = obj();
    msgQuery["billOid"] = billOid;
    msgQuery["msgType"] = "2";
    auto msgs = listBy(cm::web::crud::specFlowMessageInfo(), msgQuery);
    if (!msgs.empty()) {
        const std::string mid = sOf(msgs.front(), "id");
        // deleteFlowMessageInfoById 是逻辑删除：update ... set del_flag = '1'
        mustExec("update flow_message_info set del_flag = '1' where ID = " + cm::db::bind(mid));
        removeFlowMessage(mid, "");  // bussId 为空 -> 删该消息的全部处理人
    }

    // Java 传的是 flowCurrentNode.getId()（不是申请单 id）—— 照抄这个取值，别自作聪明改成 billOid
    mustExec("update flow_apply_info set del_flag = '1' where ID = " +
                           cm::db::bind(sOf(current, "id")));

    updateFlowTable(sOf(*flowName, "bussName"), billOid, "1");  // FlowTypeEnum.SUBMIT = 草稿

    tx.commit();
    return AjaxResult::success("撤销成功！");
}

AjaxResult submitEntrustFlow(const Json& body) {
    cm::db::Transaction tx;
    const std::string entrustUserId = sOf(body, "entrustUserId");
    const std::string entrustUserName = sOf(body, "entrustUserName");
    const std::string billOid = sOf(body, "billOid");
    if (StringUtils::isBlank(entrustUserId) || StringUtils::isBlank(entrustUserName) ||
        StringUtils::isBlank(billOid))
        return AjaxResult::error("缺少参数!");

    const long long userId = SecurityUtils::getUserId();
    Json query = obj();
    query["billOid"] = billOid;
    query["auitEmpOid"] = std::to_string(userId);
    auto nodes = listBy(cm::web::crud::specFlowCurrentNode(), query);
    if (nodes.empty()) return AjaxResult::error("当前流程节点不存在!");
    Json node = nodes.front();

    auto tp = byId(cm::web::crud::specFlowTemplate(), sOf(node, "currentOid"));
    if (!tp) return AjaxResult::error("找不到对应的流程节点模板信息!");
    auto flowName = byId(cm::web::crud::specFlowName(), sOf(*tp, "flowOid"));
    if (!flowName) return AjaxResult::error("找不到对应的流程信息!");

    auto apply = selectOne(cm::web::crud::specFlowApplyInfo(),
                           "WHERE t.del_flag = 0 AND t.bill_oid = " + cm::db::bind(billOid),
                           cm::db::Params{}, std::string());
    if (!apply) return AjaxResult::error("找不到对应的流程申请信息!");

    /** 当前节点改成被委托人，并记下委托前的审核人 */
    node["auitEmpOid"] = entrustUserId;
    node["auitEmpName"] = entrustUserName;
    node["backCol2"] = std::to_string(userId);
    node["backCol3"] = SecurityUtils::getUserRealName();
    saveEntity(cm::web::crud::specFlowCurrentNode(), node);

    const std::string flowResult = Constants::FLOW_RESULT_ENTRUST_KEY;
    const std::string flowResultContext =
        std::string(Constants::FLOW_RESULT_CONTEXT_PREFIX) + entrustUserName +
        Constants::FLOW_RESULT_CONTEXT_SUFFIX;
    saveFlowListRecord(*tp, billOid, sOf(*flowName, "flowKey"), flowResult, flowResultContext);

    Json msgBo = obj();
    msgBo["billOid"] = billOid;
    msgBo["msgType"] = "2";
    const std::string mid = saveMessageInfo(msgBo);
    saveSzzdFlowMessageAll(mid, std::to_string(userId));
    saveDisposeList(mid, {entrustUserId});

    /** 委托历史追加进 flow_apply_info.entrust_info（JSON 数组） */
    Json entrust = obj();
    entrust["operatorUserId"] = std::to_string(userId);
    entrust["operatorUserName"] = SecurityUtils::getUserRealName();
    entrust["entrustUserId"] = entrustUserId;
    entrust["entrustUserName"] = entrustUserName;
    entrust["flowId"] = sOf(*flowName, "id");
    entrust["flowKey"] = sOf(*flowName, "flowKey");
    entrust["flowTemplateId"] = sOf(*tp, "id");
    entrust["operationTime"] = nowStamp();

    const std::string old = sOf(*apply, "entrustInfo");
    Json list = Json::array();
    if (!old.empty()) {
        try {
            list = Json::parse(old);
            if (!list.is_array()) list = Json::array();
        } catch (const std::exception&) {
            // Java: JSON.parseArray 抛异常 -> 整个请求 500
            throw std::runtime_error("com.alibaba.fastjson2.JSONException: entrust_info 不是数组: " + old);
        }
        if (list.empty()) list = Json::array();  // Java: 空数组时写 singletonList(新记录)，等价于只留这条
        list.push_back(entrust);
    } else {
        list.push_back(entrust);
    }

    Json update = obj();
    update["id"] = sOf(*apply, "id");
    update["backCol1"] = entrustUserName;
    update["entrustInfo"] = list.dump();
    saveEntity(cm::web::crud::specFlowApplyInfo(), update);

    tx.commit();
    return AjaxResult::success();
}

namespace {

/** 对应 FlowTemplateServiceImpl.saveFlow(flowOid)：按 NODE_ORDER,id 重排每个节点的前后与退回指针。
 *  注意 Java 复用同一个 queryBo —— 它既有 flowOid 又逐步被 setNodeOrder(returnNum)，
 *  所以"退回节点"的查找始终限定在同一条流程内。 */
void reorderFlowNodes(const std::string& flowOid) {
    if (flowOid.empty()) return;
    Json q = obj();
    q["flowOid"] = flowOid;
    const auto list = listBy(cm::web::crud::specFlowTemplate(), q);
    std::string firstId = "-1";
    for (size_t i = 0; i < list.size(); ++i) {
        Json v = list[i];
        std::string pre;
        std::string next;
        std::string ret;
        if (i == 0) {
            pre = "0";
            ret = "0";
            firstId = sOf(v, "id");
        } else {
            pre = sOf(list[i - 1], "id");
            Json rq = obj();
            rq["flowOid"] = flowOid;
            rq["nodeOrder"] = v.contains("returnNum") ? v["returnNum"] : Json(nullptr);
            const auto rl = listBy(cm::web::crud::specFlowTemplate(), rq);
            ret = rl.empty() ? firstId : sOf(rl[0], "id");
        }
        next = (i + 1 == list.size()) ? "-1" : sOf(list[i + 1], "id");
        v["previousNodeOid"] = Json(pre);
        v["nextNodeOid"] = Json(next);
        v["returnNodeOid"] = Json(ret);
        cm::db::Params params;
        mustExec(cm::web::crud::buildUpdate(cm::web::crud::specFlowTemplate(), v, params), params);
    }
}

} // namespace

AjaxResult tbFlow() {
    // Java 的入参 flowName 从头到尾没被读过，所以这里不接任何参数
    cm::db::Transaction tx;
    const long long userId = SecurityUtils::getUserId();
    const long long epsId = SecurityUtils::getEpsId();
    const std::string ts = nowStamp();

    // 模板流程：create_by = -1 的那批
    Json probe = obj();
    probe["createBy"] = Json(-1);
    const auto templates = listBy(cm::web::crud::specFlowName(), probe);
    // 要同步的单位：is_unit = '1'
    cm::domain::SysDept dq;
    dq.isUint = "1";
    const auto depts = cm::system::service::SysDeptService::selectDeptList(dq);

    for (const Json& tpl : templates) {
        Json nq = obj();
        nq["flowOid"] = tpl.contains("id") ? tpl["id"] : Json(nullptr);
        const auto nodes = listBy(cm::web::crud::specFlowTemplate(), nq);
        for (const auto& dept : depts) {
            if (!dept.deptId) continue;
            Json exist = obj();
            exist["tenantId"] = Json(static_cast<long long>(*dept.deptId));
            exist["flowKey"] = tpl.contains("flowKey") ? tpl["flowKey"] : Json(nullptr);
            // 已经给这个单位建过同 flowKey 的流程就跳过（幂等，重复调用不会再插一遍）
            if (!listBy(cm::web::crud::specFlowName(), exist).empty()) continue;

            Json add = obj();
            for (const char* k : {"flowKey", "flowTitle", "flowContext", "bussName", "sort"}) {
                if (tpl.contains(k) && !tpl[k].is_null()) add[k] = tpl[k];
            }
            add["tenantId"] = Json(static_cast<long long>(*dept.deptId));
            add["flowBusinessType"] = Json("1");
            // saveEntity 负责 Java 在 insert 前手动补的那 6 个字段：UUID、del_flag=0、
            // eps_id=当前人部门、create_by/update_by=当前人、create_time=update_time=同一个时间戳
            const std::string newId = saveEntity(cm::web::crud::specFlowName(), add);

            for (const Json& n : nodes) {
                Json c = n;  // 整行照搬：buildInsert 会跳过 null，与 XML 的 <if test="x != null"> 一致
                c["id"] = Json(cm::utils::simpleUuid());  // Java: setId("") 走新增分支，再换成新 UUID
                c["flowOid"] = Json(newId);
                c["nextNodeOid"] = Json("");              // 显式置空串（不是 null，所以照样落库）
                c["previousNodeOid"] = Json("");
                c["delFlag"] = Json("0");
                c["epsId"] = Json(epsId);
                c["createBy"] = Json(-2);  // Java 在这里硬编码 -2，而不是当前用户
                c["createTime"] = Json(ts);
                c["updateBy"] = Json(userId);
                c["updateTime"] = Json(ts);
                cm::db::Params params;
                mustExec(cm::web::crud::buildInsert(cm::web::crud::specFlowTemplate(), c, params), params);
            }
            reorderFlowNodes(newId);
        }
    }
    tx.commit();
    return AjaxResult::success(std::string("同步成功！"));
}

} // namespace cm::flow::service
