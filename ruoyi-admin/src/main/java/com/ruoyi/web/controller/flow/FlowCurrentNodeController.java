package com.ruoyi.web.controller.flow;

import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.flow.domain.FlowCurrentNode;
import com.ruoyi.flow.service.IFlowCurrentNodeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 流程_当前节点Controller
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@RestController
@RequestMapping("/flow/currentnode")
public class FlowCurrentNodeController extends BaseController
{
    @Autowired
    private IFlowCurrentNodeService flowCurrentNodeService;

    /**
     * 查询流程_当前节点列表
     */
    // @PreAuthorize("@ss.hasPermi('flow:currentnode:list')")
    @GetMapping("/list")
    public TableDataInfo list(FlowCurrentNode flowCurrentNode)
    {
        startPage();
        List<FlowCurrentNode> list = flowCurrentNodeService.selectFlowCurrentNodeList(flowCurrentNode);
        return getDataTable(list);
    }

    /**
     * 导出流程_当前节点列表
     */
    // @PreAuthorize("@ss.hasPermi('flow:currentnode:export')")
    @Log(title = "流程_当前节点", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(FlowCurrentNode flowCurrentNode)
    {
        List<FlowCurrentNode> list = flowCurrentNodeService.selectFlowCurrentNodeList(flowCurrentNode);
        ExcelUtil<FlowCurrentNode> util = new ExcelUtil<FlowCurrentNode>(FlowCurrentNode.class);
        return util.exportExcel(list, "流程_当前节点数据");
    }

    /**
     * 获取流程_当前节点详细信息
     */
    // @PreAuthorize("@ss.hasPermi('flow:currentnode:query')")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id)
    {
        return AjaxResult.success(flowCurrentNodeService.selectFlowCurrentNodeById(id));
    }


    /**
     * 根据单据ID获取当前节点
     */
    // @PreAuthorize("@ss.hasPermi('flow:currentnode:query')")
    @GetMapping(value = "/getInfoByBillId/{billOid}")
    public AjaxResult getInfoByBillId(@PathVariable("billOid") String billOid)
    {
        FlowCurrentNode flowCurrentNode = new FlowCurrentNode();
        flowCurrentNode.setBillOid(billOid);
        List<FlowCurrentNode> list = flowCurrentNodeService.selectFlowCurrentNodeList(flowCurrentNode);
        if (list.size() > 0){
            flowCurrentNode = list.get(0);
        }
        return AjaxResult.success(flowCurrentNode);
    }



    /**
     * 新增流程_当前节点
     */
    // @PreAuthorize("@ss.hasPermi('flow:currentnode:add')")
    @Log(title = "流程_当前节点", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody FlowCurrentNode flowCurrentNode)
    {
        return flowCurrentNodeService.saveFlowCurrentNode(flowCurrentNode);
    }

    /**
     * 修改流程_当前节点
     */
    // @PreAuthorize("@ss.hasPermi('flow:currentnode:edit')")
    @Log(title = "流程_当前节点", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody FlowCurrentNode flowCurrentNode)
    {
        return flowCurrentNodeService.saveFlowCurrentNode(flowCurrentNode);
    }

    /**
     * 删除流程_当前节点
     */
    // @PreAuthorize("@ss.hasPermi('flow:currentnode:remove')")
    @Log(title = "流程_当前节点", businessType = BusinessType.DELETE)
	@DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids)
    {
        return flowCurrentNodeService.deleteFlowCurrentNodeByIds(ids);
    }

    /**
     * 流程审核
     * @param flowCurrentNode
     * @return
     */
    @PutMapping("/saveFlowAuit")
    public AjaxResult saveFlowAuit(@RequestBody FlowCurrentNode flowCurrentNode)
    {
        return flowCurrentNodeService.saveFlowAuit(flowCurrentNode);
    }

    /**
     * 撤销流程
     * @param flowCurrentNode
     * @return
     */
    @PostMapping("/submitReturn")
    public AjaxResult submitReturn(@RequestBody FlowCurrentNode flowCurrentNode)
    {
        return flowCurrentNodeService.submitReturn(flowCurrentNode);
    }

    /**
     * 委托-办理流程
     * @param flowCurrentNode
     * @return
     */
    @PostMapping("/submitEntrustFlow")
    public AjaxResult submitEntrustFlow(@RequestBody FlowCurrentNode flowCurrentNode) {
        return flowCurrentNodeService.submitEntrustFlow(flowCurrentNode);
    }

}
