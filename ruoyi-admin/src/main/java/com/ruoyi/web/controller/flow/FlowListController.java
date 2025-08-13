package com.ruoyi.web.controller.flow;

import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.enums.FlowTypeEnum;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.flow.domain.FlowApplyInfo;
import com.ruoyi.flow.domain.FlowList;
import com.ruoyi.flow.service.IFlowApplyInfoService;
import com.ruoyi.flow.service.IFlowListService;
import com.ruoyi.web.util.CommonUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 审核历史记录Controller
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@RestController
@RequestMapping("/flow/flowlist")
public class FlowListController extends BaseController
{
    @Autowired
    private IFlowListService flowListService;


    @Autowired
    private IFlowApplyInfoService flowApplyInfoService;


    /**
     * 查询审核历史记录列表
     */
    // @PreAuthorize("@ss.hasPermi('flow:flowlist:list')")
    @GetMapping("/list")
    public TableDataInfo list(FlowList flowList)
    {
        startPage();
        List<FlowList> list = flowListService.selectFlowListList(flowList);
        return getDataTable(list);
    }


    /**
     * 根据单据查询
     */
    @GetMapping("/listnew")
    public AjaxResult listnew(FlowList flowList) {
        if (StringUtils.isEmpty(flowList.getBillOid())) {
            flowList.setBillOid("-1");
        }
        List<FlowList> list = flowListService.selectFlowListList(flowList);

        // 获取的我申请记录
        FlowApplyInfo flowApplyInfo = new FlowApplyInfo();
        flowApplyInfo.setBillOid(flowList.getBillOid());
        List<FlowApplyInfo> applyList = flowApplyInfoService.selectFlowApplyInfoList(flowApplyInfo);
        if (applyList.size() > 0){
            flowApplyInfo = applyList.get(0);
            String status = CommonUtil.isNull(flowApplyInfo.getFlowStatus());
            String auitEmpName = CommonUtil.isNull(flowApplyInfo.getBackCol1());
            if (status.equals(FlowTypeEnum.APPROVE.getCode() + "")){
                // 当前审核人
                if (!auitEmpName.equals("")){
                    FlowList addbo = new FlowList();
                    addbo.setShUser(auitEmpName);
                    addbo.setShValue("待审批");
                    list.add(addbo);
                }
            }else if (status.equals(FlowTypeEnum.END.getCode() + "")){
                FlowList addbo = new FlowList();
                addbo.setShValue("流程结束");
                list.add(addbo);
            }
        }


        return AjaxResult.success(list);
    }



    /**
     * 导出审核历史记录列表
     */
    // @PreAuthorize("@ss.hasPermi('flow:flowlist:export')")
    @Log(title = "审核历史记录", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(FlowList flowList)
    {
        List<FlowList> list = flowListService.selectFlowListList(flowList);
        ExcelUtil<FlowList> util = new ExcelUtil<FlowList>(FlowList.class);
        return util.exportExcel(list, "审核历史记录数据");
    }

    /**
     * 获取审核历史记录详细信息
     */
    // @PreAuthorize("@ss.hasPermi('flow:flowlist:query')")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id)
    {
        return AjaxResult.success(flowListService.selectFlowListById(id));
    }

    /**
     * 新增审核历史记录
     */
   //  @PreAuthorize("@ss.hasPermi('flow:flowlist:add')")
    @Log(title = "审核历史记录", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody FlowList flowList)
    {
        return flowListService.saveFlowList(flowList);
    }

    /**
     * 修改审核历史记录
     */
    // @PreAuthorize("@ss.hasPermi('flow:flowlist:edit')")
    @Log(title = "审核历史记录", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody FlowList flowList)
    {
        return flowListService.saveFlowList(flowList);
    }

    /**
     * 删除审核历史记录
     */
    // @PreAuthorize("@ss.hasPermi('flow:flowlist:remove')")
    @Log(title = "审核历史记录", businessType = BusinessType.DELETE)
	@DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids)
    {
        return flowListService.deleteFlowListByIds(ids);
    }
}
