package com.ruoyi.flow.service.impl;

import com.alibaba.fastjson2.JSON;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.domain.entity.SysRole;
import com.ruoyi.common.enums.FlowTypeEnum;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.flow.domain.*;
import com.ruoyi.flow.mapper.FlowCurrentNodeMapper;
import com.ruoyi.flow.mapper.FlowNameMapper;
import com.ruoyi.flow.mapper.FlowTemplateMapper;
import com.ruoyi.flow.service.*;
import com.ruoyi.flow.util.FlowConstant;
import com.ruoyi.system.mapper.SysRoleMapper;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * 流程_当前节点Service业务层处理
 *
 * @author ruoyi
 * @date 2021-05-07
 */
@Service
public class FlowCurrentNodeServiceImpl implements IFlowCurrentNodeService {

    @Autowired
    private FlowCurrentNodeMapper flowCurrentNodeMapper;

    @Autowired
    private FlowNameMapper flowNameMapper;

    @Autowired
    private FlowTemplateMapper flowTemplateMapper;

    @Resource
    private SysRoleMapper roleMapper;

    @Autowired
    private IFlowApplyInfoService flowApplyInfoService;

    @Autowired
    private IFlowMessageInfoService flowMessageInfoService;

    @Autowired
    private IFlowMessageDisposeService flowMessageDisposeService;

    @Autowired
    private IFlowListService flowListService;


    /**
     * 查询流程_当前节点
     *
     * @param id 流程_当前节点ID
     * @return 流程_当前节点
     */
    @Override
    public FlowCurrentNode selectFlowCurrentNodeById(String id) {
        return flowCurrentNodeMapper.selectFlowCurrentNodeById(id);
    }

    /**
     * 查询流程_当前节点列表
     *
     * @param flowCurrentNode 流程_当前节点
     * @return 流程_当前节点
     */
    @Override
    public List<FlowCurrentNode> selectFlowCurrentNodeList(FlowCurrentNode flowCurrentNode) {
        return flowCurrentNodeMapper.selectFlowCurrentNodeList(flowCurrentNode);
    }

    /**
     * 新增或者修改流程_当前节点
     *
     * @param flowCurrentNode 流程_当前节点
     * @return 结果
     */
    @Override
    public AjaxResult saveFlowCurrentNode(FlowCurrentNode flowCurrentNode) {
        Long userId = SecurityUtils.getUserId();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();
        if (StringUtils.isNotEmpty(flowCurrentNode.getId())) {
            // 修改
            flowCurrentNode.setUpdateBy(userId); // 更新人
            flowCurrentNode.setUpdateTime(curDate); // 更新时间
            flowCurrentNodeMapper.updateFlowCurrentNode(flowCurrentNode);
        } else {
            // 新增
            flowCurrentNode.setId(StringUtils.getUUID()); // 主键
            flowCurrentNode.setDelFlag("0");
            flowCurrentNode.setEpsId(SecurityUtils.getEpsId()); // 当前人所在的部门
            flowCurrentNode.setCreateBy(userId); // 创建人
            flowCurrentNode.setCreateTime(curDate); // 创建时间
            flowCurrentNode.setUpdateBy(userId); // 更新人
            flowCurrentNode.setUpdateTime(curDate); // 更新时间
            flowCurrentNodeMapper.insertFlowCurrentNode(flowCurrentNode);
        }
        return AjaxResult.success("操作成功！", flowCurrentNode.getId());
    }


    /**
     * 批量删除流程_当前节点
     *
     * @param ids 需要删除的流程_当前节点ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteFlowCurrentNodeByIds(String[] ids) {
        int count = flowCurrentNodeMapper.deleteFlowCurrentNodeByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除流程_当前节点信息
     *
     * @param id 流程_当前节点ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteFlowCurrentNodeById(String id) {
        int count = flowCurrentNodeMapper.deleteFlowCurrentNodeById(id);
        return AjaxResult.success(count);
    }


    /**
     * 根据单据id : 删除流程_当前节点信息
     *
     * @param billOid
     * @return 结果
     */
    @Override
    public AjaxResult deleteByBillId(String billOid) {
        flowCurrentNodeMapper.deleteByBillId(billOid);
        return AjaxResult.success("操作成功！");
    }

    /**
     * 保存当前节点
     *
     * @param
     * @return 结果
     */
    public void saveFlowNode(FlowTemplate template, List<FlowCurrentNode> empList, String billOid, String projectId) {
        for (int i = 0; i < empList.size(); i++) {
            FlowCurrentNode node = new FlowCurrentNode();
            node.setBillOid(billOid); // 单据id
            node.setFlowOid(template.getFlowOid());
            node.setCurrentOid(template.getId());
            node.setNodeOrder(template.getNodeOrder());
            node.setNodeKey(template.getNodeKey());
            node.setNodeName(template.getNodeName());
            node.setConfigType(template.getConfigType());
            node.setConfigId(template.getConfigId());
            node.setConfigName(template.getConfigName());

            node.setAuitEmpOid(empList.get(i).getAuitEmpOid());
            node.setAuitEmpName(empList.get(i).getAuitEmpName());

            node.setBackCol1(projectId); // 项目权限字段

            saveFlowCurrentNode(node);
        }
    }

    /**
     * 插入流程审批记录
     *
     * @param auitResult
     * @return
     */
    public void saveFlowList(FlowTemplate template, String billOid, String flowKey, String auitResult, String auitContext) {
        FlowList flowList = new FlowList();
        flowList.setBillOid(billOid);
        flowList.setBussType(flowKey);
        flowList.setFlowRuid(template.getFlowOid());
        flowList.setCurrentOid(template.getId());
        flowList.setShUser(SecurityUtils.getUserRealName());
        flowList.setShKey(auitResult);
        if (auitResult.equals("S")) {
            flowList.setShValue("提交");
        } else if (auitResult.equals("T")) {
            flowList.setShValue("同意");
        } else if (auitResult.equals("F")) {
            flowList.setShValue("拒绝");
        } else if (auitResult.equals("R")) {
            flowList.setShValue("退回");
        } else if (Constants.FLOW_RESULT_ENTRUST_KEY.equals(auitResult)) {
            flowList.setShValue(Constants.FLOW_ENTRUST_NAME);
        }
        flowList.setShContext(auitContext);
        flowListService.saveFlowList(flowList);
    }


    /**
     * 查询退回人员--------------
     * @param flowKey
     */
    public List<FlowCurrentNode> getEmpInfoListReturn(String flowKey,FlowTemplate flowTemplate, String billOid, String projectId) {
        List<FlowCurrentNode> list = new ArrayList<FlowCurrentNode>();
        FlowList flowList = new FlowList();
        flowList.setBillOid(billOid);
        flowList.setCurrentOid(flowTemplate.getId()); // 上一个节点
        List<FlowList> templist = flowListService.selectFlowListListNew(flowList);
        if (templist.size() > 0){
            FlowList tlistvo = templist.get(0);
            FlowCurrentNode empFlowCurrentNode = new FlowCurrentNode();
            empFlowCurrentNode.setAuitEmpOid(tlistvo.getCreateBy()+"");
            empFlowCurrentNode.setAuitEmpName(tlistvo.getShUser());
            list.add(empFlowCurrentNode);
        }

      /*  // 1人员
        FlowCurrentNode empFlowCurrentNode = new FlowCurrentNode();
        empFlowCurrentNode.setAuitEmpOid(configId);
        empFlowCurrentNode.setAuitEmpName(flowTemplate.getConfigName());
        list.add(empFlowCurrentNode);*/

        return list;
    }


    /**
     * 查询审核人
     *
     * @param flowTemplate
     * @param billOid
     * @return
     */
    public List<FlowCurrentNode> getEmpInfoList(String flowKey,String tableName,FlowTemplate flowTemplate, String billOid, String projectId) {
        List<FlowCurrentNode> list = new ArrayList<FlowCurrentNode>();
        // 判断是人还是角色  1人员2角色3其他
        String configType = StringUtils.trim(flowTemplate.getConfigType());
        // 人员或者角色id
        String configId = StringUtils.trim(flowTemplate.getConfigId());

        // 租户单位ID （根据角色查询有用） --后面来修改
       /* Long tenantId = SecurityUtils.getTenantId();*/

        // 租户单位ID （根据角色查询有用） --后面来修改
        Long userId = SecurityUtils.getUserId();

        if (StringUtils.isNotEmpty(configId)) {
            if (configType.equals("1")) {
                // 1人员
                FlowCurrentNode empFlowCurrentNode = new FlowCurrentNode();
                empFlowCurrentNode.setAuitEmpOid(configId);
                empFlowCurrentNode.setAuitEmpName(flowTemplate.getConfigName());
                list.add(empFlowCurrentNode);
            } else {
                // 角色
                FlowCurrentNode querybo = new FlowCurrentNode();
                querybo.setRoleId(configId);
                querybo.setBillOid(billOid);

               /* querybo.setTenantId(tenantId); // 租户*/

                // 获取角色对象
                SysRole role = roleMapper.selectRoleById(Long.parseLong(flowTemplate.getConfigId()));
                if (null != role && StringUtils.isNotNull(role.getRoleId())) {

                    if (role.getRoleKey().equals(Constants.dept_manager_role)) {
                        // 部门领导审核 : 根据部门设置
                        querybo.setFlag("bmjlAudit");
                        querybo.setRoleId("");
                        querybo.setTenantId(null);
                        querybo.setBackCol1(userId.toString());

                       /* // 根据部门查询角色
                        querybo.setDeptId(SecurityUtils.getEpsId());*/

                    } else if (role.getRoleKey().equals("fg_manager")) {
                        // 分管领导审核
                        querybo.setFlag("fgldAudit");
                        querybo.setRoleId("");
                        querybo.setTenantId(null);
                        querybo.setBackCol1(userId.toString());
                    } else if (role.getRoleKey().equals(Constants.dept_duty_emp_role)) {
                        // 科室值班人审核 ： 找到归属部门的
                        querybo.setFlag("dutyAudit");
                        querybo.setTenantId(null);
                        querybo.setBackCol1(tableName); // 表名称
                    }
                    list = flowCurrentNodeMapper.selectEmpInfoList(querybo);
                }
            }
        }
        return list;
    }

    /**
     * 提交流程申请
     *
     * @param flowKey：业务key
     * @param billOid: 业务单据ID
     * @param params
     * @return
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult saveFlowApply(String flowKey, String billOid, String projectId, Map<String, Object> params) {

        // 根据流程flowKey 查询流程节点id
        FlowName flowName = new FlowName();
        flowName.setFlowKey(flowKey);

        // 租户单位ID （根据角色查询有用）
       /* Long tenantId = SecurityUtils.getTenantId();
        flowName.setTenantId(tenantId);*/

        List<FlowName> flowNameList = flowNameMapper.selectFlowNameList(flowName);
        if (flowNameList.size() > 0) {
            flowName = flowNameList.get(0);
        } else {
            return AjaxResult.error("流程不存在，请与管理员联系！");
        }

        // 根据流程查找第一个节点
        FlowTemplate flowTemplate = new FlowTemplate();
        flowTemplate.setFlowOid(flowName.getId());
        flowTemplate.setPreviousNodeOid("0");
        List<FlowTemplate> flowTemplateList = flowTemplateMapper.selectFlowTemplateList(flowTemplate);
        if (flowTemplateList.size() > 0) {
            flowTemplate = flowTemplateList.get(0);
        } else {
            return AjaxResult.error("节点不存在，请与管理员联系！");
        }

        // 根据节点查询审核人
        List<FlowCurrentNode> empList = getEmpInfoList(flowKey,flowName.getBussName(),flowTemplate, billOid, projectId);
        if (empList.size() == 0) {
            return AjaxResult.error("该业务找不到下一审批人，请与管理员联系！");
        }

        String auitNames = ""; // 处理人名称
        String[] useIds = new String[empList.size()];
        for (int i = 0; i < empList.size(); i++) {
            useIds[i] = empList.get(i).getAuitEmpOid();
            auitNames += empList.get(i).getAuitEmpName() +",";
        }

        if(auitNames.endsWith(",")){
            auitNames = auitNames.substring(0,auitNames.length()-1);
        }



        String flowStatus = FlowTypeEnum.APPROVE.getCode() + "";  // 流程状态
        String flowRuid = flowName.getId(); // 流程实例ID
        String flowApplyOid = "-1";  // 流程申请ID
        String realName = SecurityUtils.getUserRealName(); // 提交人
        String bussTypeName = flowName.getFlowTitle(); // 业务名称
        String tableName = flowName.getBussName(); // 表名

        // 提交的业务名称
        String bussTitle = bussTypeName;
        if (null != params){
            if (null != params.get("bussTitle")){
                bussTitle = params.get("bussTitle").toString();
            }
        }

        String msgTitle1 = "【" + bussTypeName + "】你提交关于" + bussTitle + "的申请！";
        String msgTitle2 = "【" + bussTypeName + "】" + realName + "提交关于" + bussTitle + "的申请！";

        // 我的申请插入一条记录
        FlowApplyInfo flowApplyInfo = new FlowApplyInfo();
        flowApplyInfo.setBillOid(billOid);
        flowApplyInfo.setBussType(flowKey);
        flowApplyInfo.setFlowRuid(flowRuid);
        flowApplyInfo.setMsgType("1");
        flowApplyInfo.setFlowStatus(flowStatus);
        flowApplyInfo.setApplyName(realName);
        flowApplyInfo.setMsgTitle(msgTitle1);
        flowApplyInfo.setBackCol1(auitNames); // 当前处理人

        flowApplyOid = flowApplyInfoService.saveFlowApplyInfoNew(flowApplyInfo);



        // 插入下一个节点
        saveFlowNode(flowTemplate, empList, billOid, projectId);

        // 发送消息主体
        FlowMessageInfo flowMessageInfo = new FlowMessageInfo();
        flowMessageInfo.setBillOid(billOid);
        flowMessageInfo.setBussType(flowKey);
        flowMessageInfo.setFlowRuid(flowRuid);
        flowMessageInfo.setMsgType("2");
        flowMessageInfo.setApplyName(realName);
        flowMessageInfo.setMsgTitle(msgTitle2);
        String mid = flowMessageInfoService.saveFlowMessageInfo(flowMessageInfo);
        // 发送消息明细
        flowMessageDisposeService.saveFlowList(mid, useIds);

        // 插入审核历史记录
        saveFlowList(flowTemplate, billOid, flowKey, "S", "");


        // 反该业务状态
        FlowCurrentNode bo = new FlowCurrentNode();
        bo.setTableName(tableName);
        bo.setBillOid(billOid);
        bo.setFlowKey(flowKey);
        bo.setFlowRuid(flowRuid);
        bo.setFlowApplyOid(flowApplyOid);
        bo.setFlowStatus(flowStatus);
        flowCurrentNodeMapper.updateFlowTable(bo);

        return AjaxResult.success("流程提交成功！");
    }


    /**
     * 业务审核
     *
     * @param flowCurrentNode 流程当前节点
     * @return 结果
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult saveFlowAuit(FlowCurrentNode flowCurrentNode) {
        String shValue = flowCurrentNode.getShValue();
        String billOid = flowCurrentNode.getBillOid();
        String projectId = "";
        String flowStatus = FlowTypeEnum.APPROVE.getCode() + "";  // 流程状态
        if (StringUtils.isNotNull(shValue)) {
            if (shValue.equals("1")) {
                shValue = "T";
            } else if (shValue.equals("2")) {
                shValue = "F";
                flowStatus = FlowTypeEnum.STOP.getCode() + "";
            } else if (shValue.equals("3")) {
                shValue = "R";
            }
        }

        if (StringUtils.isEmpty(shValue)) {
            return AjaxResult.error("请填写审核结论！");
        }


        if (StringUtils.isEmpty(billOid)) {
            return AjaxResult.error("业务不存在！");
        }

        // 获取当前节点
        FlowCurrentNode queryBo = new FlowCurrentNode();
        queryBo.setBillOid(billOid);
        queryBo.setAuitEmpOid(SecurityUtils.getUserId() + "");
        List<FlowCurrentNode> currentList = this.selectFlowCurrentNodeList(queryBo);
        FlowCurrentNode newCurrent = null;
        if (currentList.size() > 0) {
            newCurrent = currentList.get(0);
            if (StringUtils.isNotEmpty(newCurrent.getBackCol1())) {
                projectId = newCurrent.getBackCol1();
            }
        } else {
            return AjaxResult.error("对不起，该单据已审核，请确定！");
        }

        FlowTemplate curflowTemplate = flowTemplateMapper.selectFlowTemplateById(newCurrent.getCurrentOid());  // 当前节点
        String nextNodeOid = curflowTemplate.getNextNodeOid(); // 等于-1 最后一个节点不需要 查找
        // String returnNodeOid = curflowTemplate.getReturnNodeOid(); // 退回节点 或者 上一个节点
        String returnNodeOid = curflowTemplate.getPreviousNodeOid(); // 上一个节点
        // 当前审核节点
        FlowName flowName = flowNameMapper.selectFlowNameById(curflowTemplate.getFlowOid());

        FlowTemplate nextFlowTemplate = new FlowTemplate(); // 下一个节点信息
        // 根据节点查询审核人
        List<FlowCurrentNode> empList = new ArrayList<FlowCurrentNode>();
        // 不是下一个节点
        if (!nextNodeOid.equals("-1") && shValue.equals("T")) {
            // 同意查询下一个人
            nextFlowTemplate = flowTemplateMapper.selectFlowTemplateById(nextNodeOid);
            if (null != nextFlowTemplate && StringUtils.isNotEmpty(nextFlowTemplate.getId())) {
                empList = getEmpInfoList(flowName.getFlowKey(),flowName.getBussName(),nextFlowTemplate, billOid, projectId);
                if (empList.size() == 0) {
                    return AjaxResult.error("该业务找不到下一审批人，请与管理员联系！");
                }
            } else {
                return AjaxResult.error("下一个节点不存在，请与管理员联系！");
            }

        } else if (!returnNodeOid.equals("0") && shValue.equals("R")) {
            // 退回查询下一个审核人
            nextFlowTemplate = flowTemplateMapper.selectFlowTemplateById(returnNodeOid);
            if (null != nextFlowTemplate && StringUtils.isNotEmpty(nextFlowTemplate.getId())) {
                empList = getEmpInfoListReturn(flowName.getFlowKey(),nextFlowTemplate, billOid, projectId);
                if (empList.size() == 0) {
                    return AjaxResult.error("该业务找不到下一审批人，请与管理员联系！");
                }
            } else {
                return AjaxResult.error("退回节点不存在，请与管理员联系！");
            }
        }

        // 处理人名称
        String auitNames = "";
        String[] useIds = new String[empList.size()];
        for (int i = 0; i < empList.size(); i++) {
            useIds[i] = empList.get(i).getAuitEmpOid();
            auitNames += empList.get(i).getAuitEmpName() +",";
        }

        if(auitNames.endsWith(",")){
            auitNames = auitNames.substring(0,auitNames.length()-1);
        }

        // 审核通过
        if (nextNodeOid.equals("-1") && shValue.equals("T")) {
            flowStatus = FlowTypeEnum.END.getCode() + "";
        }

        // 审核退回
        if (returnNodeOid.equals("0") && shValue.equals("R")) {
            flowStatus = FlowTypeEnum.RETURN.getCode() + "";
        }


        String bussTypeName = flowName.getFlowTitle(); // 业务名称
        String tableName = flowName.getBussName(); // 表名
        String flowKey = flowName.getFlowKey(); // 流程key
        String flowRuid = flowName.getId(); // 流程实例ID
        String flowApplyOid = "-1";  // 流程申请ID

        // 先删除下当前节点
        flowCurrentNodeMapper.deleteByBillId(billOid);
        // 修改消息主体
        FlowMessageInfo flowMessageInfo = new FlowMessageInfo();
        flowMessageInfo.setBillOid(billOid);
        flowMessageInfo.setMsgType("2");
        String mid = flowMessageInfoService.saveFlowMessageInfo(flowMessageInfo);

        // 消息的待办全部设置为自己
        flowMessageDisposeService.saveSzzdFlowMessageAll(mid, SecurityUtils.getUserId() + "");

        // 修改我的我的申请

        FlowApplyInfo flowApplyInfo = new FlowApplyInfo();
        flowApplyInfo.setBillOid(billOid);
        flowApplyInfo.setFlowStatus(flowStatus);
        flowApplyInfo.setBackCol1(auitNames);
        flowApplyOid = flowApplyInfoService.saveFlowApplyInfoNew(flowApplyInfo);

        // 申请人ID
        Long applyId = flowApplyInfoService.selectFlowApplyInfoById(flowApplyOid).getCreateBy();

        // 修改业务状态
        FlowCurrentNode bo = new FlowCurrentNode();
        bo.setTableName(tableName);
        bo.setBillOid(billOid);
        bo.setFlowStatus(flowStatus);

        flowCurrentNodeMapper.updateFlowTable(bo);

        // 插入审核意见
        saveFlowList(curflowTemplate, billOid, flowKey, shValue, flowCurrentNode.getShContext());

        // 插入下一个节点
        saveFlowNode(nextFlowTemplate, empList, billOid, projectId);
        // 发送消息明细
        flowMessageDisposeService.saveFlowList(mid, useIds);

        String msgTitle1 = "";
        /*------------业务反该区域----------------------------*/
        if (flowStatus.equals(FlowTypeEnum.END.getCode() + "")) {
            // 审核通过。。。
            msgTitle1 += "你提交的" + bussTypeName + "业务已通过，请查看！";

        } else if (flowStatus.equals(FlowTypeEnum.STOP.getCode() + "")) {
            // 审核拒绝。。。
            msgTitle1 += "你提交的" + bussTypeName + "业务已拒绝，请查看！";

        } else if (flowStatus.equals(FlowTypeEnum.RETURN.getCode() + "")) {
            // 审核退回。。。
            msgTitle1 += "你提交的" + bussTypeName + "业务已退回，请查看！";

        }

        /** 流程结束回调 */
        if (flowKey.equals(FlowConstant.expert_apply_key) && !flowStatus.equals(FlowTypeEnum.APPROVE.getCode() + "")) {
            // 专家申请
            // expertApplyInfoService.callbackMethod(billOid, flowStatus);
        } else if (flowKey.equals(FlowConstant.dev_apply_key) && !flowStatus.equals(FlowTypeEnum.APPROVE.getCode() + "")) {
            // 设备申请
            // devApplyInfoService.callbackMethod(billOid, flowStatus);
        } else if (flowKey.equals(FlowConstant.res_info_key) && !flowStatus.equals(FlowTypeEnum.APPROVE.getCode() + "")) {
        }


        // 发送消息给申请人
        if (!msgTitle1.equals("")) {
            // 发送消息主体
            FlowMessageInfo grflowMessageInfo = new FlowMessageInfo();
            grflowMessageInfo.setBillOid(billOid);
            grflowMessageInfo.setBussType(flowKey);
            grflowMessageInfo.setFlowRuid(flowRuid);
            grflowMessageInfo.setMsgType("1");
            // grflowMessageInfo.setApplyName(realName);
            grflowMessageInfo.setMsgTitle(msgTitle1);
            String grmid = flowMessageInfoService.saveFlowMessageInfo(grflowMessageInfo);
            String[] grUseIds = new String[1];
            grUseIds[0] = applyId + "";
            // 发送消息明细
            flowMessageDisposeService.saveFlowList(grmid, grUseIds);
        }

        return AjaxResult.success("审核成功！");
    }

    /**
     * 业务审核  -- 撤销流程
     *
     * @param flowCurrentNode 流程_当前节点
     * @return 结果
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult submitReturn(FlowCurrentNode flowCurrentNode){

        // 根据当前业务ID查询是否是第一个节点
        String billOid = flowCurrentNode.getBillOid();
        if (StringUtils.isEmpty(billOid)) {
            return AjaxResult.error("业务不存在！");
        }

        // 根据当前业务查询节点
        FlowCurrentNode querybo = new FlowCurrentNode();
        querybo.setBillOid(billOid);
        List<FlowCurrentNode> currentList = this.selectFlowCurrentNodeList(querybo);
        FlowCurrentNode newCurrent = null;
        if (currentList.size() > 0) {
            newCurrent = currentList.get(0);
        } else {
            return AjaxResult.error("撤销失败，该单据已撤销，请确定！");
        }
        FlowTemplate curflowTemplate = flowTemplateMapper.selectFlowTemplateById(newCurrent.getCurrentOid());  // 当前节点
        String previousNodeOid = curflowTemplate.getPreviousNodeOid(); // 等于-1 最后一个节点不需要 查找
        if (previousNodeOid.equals("0")){

            // 当前审核节点
            FlowName flowName = flowNameMapper.selectFlowNameById(curflowTemplate.getFlowOid());

            // 删除当前节点数据
            flowCurrentNodeMapper.deleteByBillId(billOid);

            // 修改消息
            FlowMessageInfo flowMessageInfo = new FlowMessageInfo();
            flowMessageInfo.setBillOid(billOid);
            flowMessageInfo.setMsgType("2");
            List<FlowMessageInfo>  msglist = flowMessageInfoService.selectFlowMessageInfoList(flowMessageInfo);
            if (msglist.size() > 0){
                String  mid = msglist.get(0).getId();
                flowMessageInfoService.deleteFlowMessageInfoById(mid);
                // 消息的待办全部设置为自己
                flowMessageDisposeService.removeFlowMessage(mid,"");
            }

            // 删除我的申请
            flowApplyInfoService.deleteFlowApplyInfoById(flowCurrentNode.getId());


            // 单据状态修改成草稿
            String tableName = flowName.getBussName(); // 表名
            FlowCurrentNode bo = new FlowCurrentNode();
            bo.setTableName(tableName);
            bo.setBillOid(billOid);
            bo.setFlowStatus( FlowTypeEnum.SUBMIT.getCode()+"");
            flowCurrentNodeMapper.updateFlowTable(bo);


        }else {
            return AjaxResult.error("撤销失败，该单据已审核，请确定！");
        }



        return AjaxResult.success("撤销成功！");
    }

    /**
     * 委托-办理流程
     * @param flowCurrentNode
     * @return
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult submitEntrustFlow(FlowCurrentNode flowCurrentNode) {
        if (StringUtils.isAnyBlank(flowCurrentNode.getEntrustUserId(), flowCurrentNode.getEntrustUserName(), flowCurrentNode.getBillOid())) {
            return AjaxResult.error("缺少参数!");
        }
        String billOid = flowCurrentNode.getBillOid();
        Long userId = SecurityUtils.getUserId();

        // 流程结果(委托)
        String flowResult = Constants.FLOW_RESULT_ENTRUST_KEY;
        // 流程结果内容
        String flowResultContext = Constants.FLOW_RESULT_CONTEXT_PREFIX + flowCurrentNode.getEntrustUserName() + Constants.FLOW_RESULT_CONTEXT_SUFFIX;

        // 获取当前流程节点
        FlowCurrentNode queryBo = new FlowCurrentNode();
        queryBo.setBillOid(billOid);
        queryBo.setAuitEmpOid(String.valueOf(userId));
        List<FlowCurrentNode> currentNodeList = this.selectFlowCurrentNodeList(queryBo);
        if (CollectionUtils.isEmpty(currentNodeList)) {
            return AjaxResult.error("当前流程节点不存在!");
        }
        FlowCurrentNode currentNode = currentNodeList.get(0);

        // 查询当前流程节点对应的流程模板
        FlowTemplate flowTemplate = flowTemplateMapper.selectFlowTemplateById(currentNode.getCurrentOid());
        if (flowTemplate == null) {
            return AjaxResult.error("找不到对应的流程节点模板信息!");
        }

        // 查询当前流程信息
        FlowName flowName = flowNameMapper.selectFlowNameById(flowTemplate.getFlowOid());
        if (flowName == null) {
            return AjaxResult.error("找不到对应的流程信息!");
        }

        // 查询流程申请信息
        FlowApplyInfo flowApplyInfo = flowApplyInfoService.selectByBillId(billOid);
        if (flowApplyInfo == null) {
            return AjaxResult.error("找不到对应的流程申请信息!");
        }

        /** 更新当前流程节点数据 */
        // 设置委托审核人id
        currentNode.setAuitEmpOid(flowCurrentNode.getEntrustUserId());
        // 设置委托审核人名称
        currentNode.setAuitEmpName(flowCurrentNode.getEntrustUserName());
        // 设置委托之前的审核人id
        currentNode.setBackCol2(String.valueOf(SecurityUtils.getUserId()));
        // 设置委托之前的审核人名称
        currentNode.setBackCol3(SecurityUtils.getUserRealName());
        this.saveFlowCurrentNode(currentNode);

        /** 保存流程委托信息 */
        this.saveFlowList(flowTemplate, billOid, flowName.getFlowKey(), flowResult, flowResultContext);

        /** 设置流程信息 */
        // 将流程信息设置为已办理
        FlowMessageInfo flowMessageInfoQueryBo = new FlowMessageInfo();
        flowMessageInfoQueryBo.setBillOid(billOid);
        flowMessageInfoQueryBo.setMsgType("2");
        String messageInfoId = flowMessageInfoService.saveFlowMessageInfo(flowMessageInfoQueryBo);

        // 设置当前流程节点的流程消息的处理人全部为当前操作人, 并设置为已处理
        flowMessageDisposeService.saveSzzdFlowMessageAll(messageInfoId, String.valueOf(SecurityUtils.getUserId()));

        // 发送消息给委派的人员
        flowMessageDisposeService.saveFlowList(messageInfoId, new String[]{flowCurrentNode.getEntrustUserId()});

        /** 保存委派的信息记录 */
        String entrustInfoJsonStr = flowApplyInfo.getEntrustInfo();

        EntrustInfo entrustInfo = new EntrustInfo();
        // 操作人id
        entrustInfo.setOperatorUserId(String.valueOf(SecurityUtils.getUserId()));
        // 操作人
        entrustInfo.setOperatorUserName(SecurityUtils.getUserRealName());
        // 委托人id
        entrustInfo.setEntrustUserId(flowCurrentNode.getEntrustUserId());
        // 委托人
        entrustInfo.setEntrustUserName(flowCurrentNode.getEntrustUserName());
        // 操作时间
        entrustInfo.setOperationTime(LocalDateTime.now());
        // 流程id
        entrustInfo.setFlowId(flowName.getId());
        // 流程key
        entrustInfo.setFlowKey(flowName.getFlowKey());
        // 流程模板节点id
        entrustInfo.setFlowTemplateId(flowTemplate.getId());

        // 更新数据
        FlowApplyInfo updateBo = new FlowApplyInfo();
        updateBo.setId(flowApplyInfo.getId());
        // 设置当前审核人信息
        updateBo.setBackCol1(flowCurrentNode.getEntrustUserName());
        if (StringUtils.isNotBlank(entrustInfoJsonStr)) {
            // 更新委托数据
            List<EntrustInfo> entrustInfoList = JSON.parseArray(entrustInfoJsonStr, EntrustInfo.class);
            if (CollectionUtils.isNotEmpty(entrustInfoList)) {
                entrustInfoList.add(entrustInfo);
                String entrustJson = JSON.toJSONString(entrustInfoList);
                updateBo.setEntrustInfo(entrustJson);
            } else {
                // 新增委托数据
                String entrustJson = JSON.toJSONString(Collections.singletonList(entrustInfo));
                updateBo.setEntrustInfo(entrustJson);
            }
        } else {
            // 新增委托数据
            String entrustJson = JSON.toJSONString(Collections.singletonList(entrustInfo));
            updateBo.setEntrustInfo(entrustJson);
        }
        // 更新流程申请信息, 添加委派信息
        flowApplyInfoService.saveFlowApplyInfo(updateBo);

        return AjaxResult.success();
    }

    /**
     * 根据角色查询用户信息
     *
     * @param flowCurrentNode 流程_当前节点
     * @return 流程_当前节点集合
     */
    public  List<FlowCurrentNode> selectUserListByRole(FlowCurrentNode flowCurrentNode){

        List<FlowCurrentNode> list = new ArrayList<FlowCurrentNode>();
        if (flowCurrentNode.getRoleKey().equals(Constants.dept_manager_role)){
            //  根据部门设置的分管领导
           list = flowCurrentNodeMapper.selectUserListByDept(flowCurrentNode);
        }else{
            // 根据角色和部门查询人员
            list = flowCurrentNodeMapper.selectUserListByRole(flowCurrentNode);
        }

        return  list;
    }


    /**
     * 发送待办消息
     * @param flowKey：流程key
     * @param billOid：单据ID
     * @param msgType: 消息类型(1:通知业务，2:办理业务)
     * @param empList：处理人集合
     * @param msgTitle：发送消息
     * @param params 其他参数
     * @return
     */
    public AjaxResult sendDbMessage(String flowKey, String billOid, String msgType, List<FlowCurrentNode> empList,
                                    String msgTitle, Map<String, Object> params) {

        if (null !=empList && empList.size() >0){
        }else{
            return AjaxResult.error("该业务找不到下一审批人，请与管理员联系！");
        }
        String realName = SecurityUtils.getUserRealName(); // 提交人

        // 发送消息主体
        FlowMessageInfo flowMessageInfo = new FlowMessageInfo();
        flowMessageInfo.setBussType(flowKey);
        flowMessageInfo.setBillOid(billOid);
        flowMessageInfo.setFlowRuid(FlowConstant.zdy_flow); //自定义流程
        flowMessageInfo.setMsgType(msgType);

        flowMessageInfo.setApplyName(realName);
        flowMessageInfo.setMsgTitle(msgTitle);
        String mid = flowMessageInfoService.saveFlowMessageInfo(flowMessageInfo);


        // String auitNames = ""; // 处理人名称
        String[] useIds = new String[empList.size()];
        for (int i = 0; i < empList.size(); i++) {
            useIds[i] = empList.get(i).getAuitEmpOid();
            // auitNames += empList.get(i).getAuitEmpName() +",";
        }

       /* if(auitNames.endsWith(",")){
            auitNames = auitNames.substring(0,auitNames.length()-1);
        }*/
        // 发送消息明细
        flowMessageDisposeService.saveFlowList(mid, useIds);

        return AjaxResult.success("流程提交成功！");
    }

    /**
     * 处理待办消息
     * @param flowKey：流程key
     * @param billOid：单据ID
     * @param msgType: 消息类型(1:通知业务，2:办理业务)
     * @param params 其他参数
     * @return
     */
    public  AjaxResult auitDbMessage(String flowKey, String billOid, String msgType, Map<String, Object> params){
        // 修改消息主体
        FlowMessageInfo flowMessageInfo = new FlowMessageInfo();
        flowMessageInfo.setBussType(flowKey);
        flowMessageInfo.setBillOid(billOid);
        flowMessageInfo.setMsgType(msgType);
        flowMessageInfo.setFlowRuid(FlowConstant.zdy_flow); //自定义流程
        List<FlowMessageInfo> list = flowMessageInfoService.selectFlowMessageInfoList(flowMessageInfo);
        if (null !=list && list.size() >0){
            // 消息的待办全部设置为自己
            flowMessageDisposeService.saveSzzdFlowMessageAll(list.get(0).getId(), SecurityUtils.getUserId() + "");
        }else{
            return AjaxResult.error("该业务找不到下一审批人，请与管理员联系！");
        }
        return AjaxResult.success("流程处理成功！");
    }


}
