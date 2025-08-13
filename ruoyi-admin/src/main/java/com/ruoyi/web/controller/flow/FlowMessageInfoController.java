package com.ruoyi.web.controller.flow;

import java.io.OutputStream;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import cn.afterturn.easypoi.excel.ExcelExportUtil;
import cn.afterturn.easypoi.excel.entity.TemplateExportParams;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.flow.domain.FlowList;
import com.ruoyi.flow.service.IFlowListService;
import org.apache.poi.ss.usermodel.Workbook;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.flow.domain.FlowMessageInfo;
import com.ruoyi.flow.service.IFlowMessageInfoService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

import javax.servlet.http.HttpServletResponse;

/**
 * 系统内部消息Controller
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@RestController
@RequestMapping("/flow/messageinfo")
public class FlowMessageInfoController extends BaseController
{
    @Autowired
    private IFlowMessageInfoService flowMessageInfoService;
    @Autowired
    private IFlowListService flowListService;
    /**
     * 查询系统内部消息列表 -- 我的待办
     */
    @GetMapping("/list")
    public TableDataInfo list(FlowMessageInfo flowMessageInfo)
    {
        startPage();
        flowMessageInfo.setFlag("mydb"); // 我的待办
        flowMessageInfo.setUserId(SecurityUtils.getUserId());
        List<FlowMessageInfo> list = flowMessageInfoService.selectFlowMessageInfoList(flowMessageInfo);
        return getDataTable(list);
    }


    /**
     * 查询系统内部消息列表 -- 我的已办
     */
    @GetMapping("/listyb")
    public TableDataInfo listyb(FlowMessageInfo flowMessageInfo)
    {
        startPage();
        flowMessageInfo.setFlag("myyb"); // 我的已办
        flowMessageInfo.setUserId(SecurityUtils.getUserId());
        List<FlowMessageInfo> list = flowMessageInfoService.selectFlowMessageInfoList(flowMessageInfo);
        return getDataTable(list);
    }

    /**
     * 查询系统内部消息列表 -- 我的已结
     */
    @GetMapping("/listyj")
    public TableDataInfo listyj(FlowMessageInfo flowMessageInfo)
    {
        startPage();
        flowMessageInfo.setFlag("myyj"); // 我的已结
        flowMessageInfo.setUserId(SecurityUtils.getUserId());
        List<FlowMessageInfo> list = flowMessageInfoService.selectFlowMessageInfoList(flowMessageInfo);
        return getDataTable(list);
    }


    /**
     * 查询系统内部消息列表 -- 我的消息
     */
    @GetMapping("/listxx")
    public TableDataInfo listxx(FlowMessageInfo flowMessageInfo)
    {
        startPage();
        flowMessageInfo.setFlag("myxx"); // 我的已办
        flowMessageInfo.setUserId(SecurityUtils.getUserId());
        List<FlowMessageInfo> list = flowMessageInfoService.selectFlowMessageInfoList(flowMessageInfo);
        return getDataTable(list);
    }


    /**
     * 导出系统内部消息列表
     */
    // @PreAuthorize("@ss.hasPermi('flow:messageinfo:export')")
    @Log(title = "系统内部消息", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(FlowMessageInfo flowMessageInfo)
    {
        List<FlowMessageInfo> list = flowMessageInfoService.selectFlowMessageInfoList(flowMessageInfo);
        ExcelUtil<FlowMessageInfo> util = new ExcelUtil<FlowMessageInfo>(FlowMessageInfo.class);
        return util.exportExcel(list, "系统内部消息数据");
    }

    /**
     * 获取系统内部消息详细信息
     */
    // @PreAuthorize("@ss.hasPermi('flow:messageinfo:query')")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id)
    {
        return AjaxResult.success(flowMessageInfoService.selectFlowMessageInfoById(id));
    }

    /**
     * 新增系统内部消息
     */
    // @PreAuthorize("@ss.hasPermi('flow:messageinfo:add')")
   /* @Log(title = "系统内部消息", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody FlowMessageInfo flowMessageInfo)
    {
        return flowMessageInfoService.saveFlowMessageInfo(flowMessageInfo);
    }

    *//**
     * 修改系统内部消息
     *//*
    // @PreAuthorize("@ss.hasPermi('flow:messageinfo:edit')")
    @Log(title = "系统内部消息", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody FlowMessageInfo flowMessageInfo)
    {
        return flowMessageInfoService.saveFlowMessageInfo(flowMessageInfo);
    }*/

    /**
     * 删除系统内部消息
     */
    // @PreAuthorize("@ss.hasPermi('flow:messageinfo:remove')")
    @Log(title = "系统内部消息", businessType = BusinessType.DELETE)
	@DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids)
    {
        return flowMessageInfoService.deleteFlowMessageInfoByIds(ids);
    }

    @Log(title = "导出审核日志", businessType = BusinessType.EXPORT)
    @GetMapping("/exportShrz")
    public AjaxResult exportShrz(FlowMessageInfo flowMessageInfo, HttpServletResponse response) {
        Map<String, Object> map = new HashMap<String, Object>();
        FlowMessageInfo messageInfo = flowMessageInfoService.selectFlowMessageInfoById(flowMessageInfo.getId());
        map.put("applyName",messageInfo.getApplyName());
        map.put("createTime", DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD,messageInfo.getCreateTime()));
        map.put("msgTitle",messageInfo.getMsgTitle());
        FlowList flowList = new FlowList();
        flowList.setBillOid(flowMessageInfo.getBillOid());
        List<FlowList> list = flowListService.selectFlowListList(flowList);
        for(int i=0;i<list.size();i++){
            FlowList fl = list.get(i);
            fl.setSort(i+1);
        }
        map.put("entitylist", list);
        try {
            String url = "templates/export/exportShrz.xlsx";
            TemplateExportParams params = new TemplateExportParams(url);
            Workbook workbook = ExcelExportUtil.exportExcel(params, map);
            response.setContentType("application/octet-stream;charset=UTF-8");
            response.setHeader("Content-Disposition", "attachment");
            OutputStream outs = response.getOutputStream();
            workbook.write(outs);
            outs.flush();
            outs.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }
}
