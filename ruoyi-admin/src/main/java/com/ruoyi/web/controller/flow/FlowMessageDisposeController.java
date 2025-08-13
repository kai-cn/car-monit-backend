package com.ruoyi.web.controller.flow;

import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.flow.domain.FlowMessageDispose;
import com.ruoyi.flow.service.IFlowMessageDisposeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 系统消息处理人Controller
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@RestController
@RequestMapping("/flow/messagedispose")
public class FlowMessageDisposeController extends BaseController
{
    @Autowired
    private IFlowMessageDisposeService flowMessageDisposeService;

    /**
     * 查询系统消息处理人列表
     */
    // @PreAuthorize("@ss.hasPermi('flow:messagedispose:list')")
    @GetMapping("/list")
    public TableDataInfo list(FlowMessageDispose flowMessageDispose)
    {
        startPage();
        List<FlowMessageDispose> list = flowMessageDisposeService.selectFlowMessageDisposeList(flowMessageDispose);
        return getDataTable(list);
    }

    /**
     * 导出系统消息处理人列表
     */
    // @PreAuthorize("@ss.hasPermi('flow:messagedispose:export')")
    @Log(title = "系统消息处理人", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(FlowMessageDispose flowMessageDispose)
    {
        List<FlowMessageDispose> list = flowMessageDisposeService.selectFlowMessageDisposeList(flowMessageDispose);
        ExcelUtil<FlowMessageDispose> util = new ExcelUtil<FlowMessageDispose>(FlowMessageDispose.class);
        return util.exportExcel(list, "系统消息处理人数据");
    }

    /**
     * 获取系统消息处理人详细信息
     */
    // @PreAuthorize("@ss.hasPermi('flow:messagedispose:query')")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id)
    {
        return AjaxResult.success(flowMessageDisposeService.selectFlowMessageDisposeById(id));
    }

    /**
     * 新增系统消息处理人
     */
    // @PreAuthorize("@ss.hasPermi('flow:messagedispose:add')")
    @Log(title = "系统消息处理人", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody FlowMessageDispose flowMessageDispose)
    {
        return flowMessageDisposeService.saveFlowMessageDispose(flowMessageDispose);
    }

    /**
     * 修改系统消息处理人
     */
    // @PreAuthorize("@ss.hasPermi('flow:messagedispose:edit')")
    @Log(title = "系统消息处理人", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody FlowMessageDispose flowMessageDispose)
    {
        return flowMessageDisposeService.saveFlowMessageDispose(flowMessageDispose);
    }

    /**
     * 删除系统消息处理人
     */
    // @PreAuthorize("@ss.hasPermi('flow:messagedispose:remove')")
    @Log(title = "系统消息处理人", businessType = BusinessType.DELETE)
	@DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids)
    {
        return flowMessageDisposeService.deleteFlowMessageDisposeByIds(ids);
    }


    /**
     * 删除消息 -- 自己
     * @param mid
     * @return
     */
    @DeleteMapping("/delmes/{mid}")
    public AjaxResult removeFlowMessage(@PathVariable("mid") String mid)
    {
        return flowMessageDisposeService.removeFlowMessage(mid, SecurityUtils.getUserId()+"");
    }

    /**
     * 设置已读 -自己
     * @param mid
     * @return
     */
    @DeleteMapping("/szzdmes/{mid}")
    public AjaxResult szzdFlowMessage(@PathVariable("mid") String mid)
    {
        return flowMessageDisposeService.saveSzzdFlowMessage(mid, SecurityUtils.getUserId()+"");
    }



}
