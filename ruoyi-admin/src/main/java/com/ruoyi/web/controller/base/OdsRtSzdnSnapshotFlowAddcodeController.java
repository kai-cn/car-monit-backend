package com.ruoyi.web.controller.base;

import cn.afterturn.easypoi.excel.ExcelExportUtil;
import cn.afterturn.easypoi.excel.entity.TemplateExportParams;
import com.alibaba.fastjson2.JSON;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.service.forest.HttpOdsRtSzdnSnapshotFlowAddcodeService;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.constant.HttpStatus;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.domain.entity.SysUser;
import com.ruoyi.common.core.domain.model.LoginUser;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.query.domain.CarQueryLog;
import com.ruoyi.query.service.impl.CarQueryLogServiceImpl;
import com.ruoyi.system.service.ISysDictDataService;
import org.apache.poi.ss.usermodel.Workbook;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 门架抓拍流水Controller
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@RestController
@RequestMapping("/base/snapshotflow")
public class OdsRtSzdnSnapshotFlowAddcodeController extends BaseController {

    @Resource
    private HttpOdsRtSzdnSnapshotFlowAddcodeService httpOdsRtSzdnSnapshotFlowAddcodeService;
    @Autowired
    private ISysDictDataService sysDictDataService;
    @Autowired
    private CarQueryLogServiceImpl carQueryLogService;

    /**
     * 查询门架抓拍流水列表
     */
    @PreAuthorize("@ss.hasPermi('base:snapshotflow:list')")
    @GetMapping("/list")
    public TableDataInfo list(OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode) {
        // 查询日志
        carQueryLogService.queryLog(JSON.toJSONString(odsRtSzdnSnapshotFlowAddcode), "2", "1");
        // 当前页面
        if (null == odsRtSzdnSnapshotFlowAddcode.getPageNum()){
            odsRtSzdnSnapshotFlowAddcode.setPageNum(1);
        }
        // 分页大小
        if (null == odsRtSzdnSnapshotFlowAddcode.getPageSize()){
            odsRtSzdnSnapshotFlowAddcode.setPageSize(10);
        }

        //  路段
        String sectionCodeStr = CommonUtil.deleteEnd(odsRtSzdnSnapshotFlowAddcode.getSectionCodeStr());
        if (CommonUtil.isNotBlank(sectionCodeStr)){
            if (sectionCodeStr.indexOf(Constants.section_all) > -1) {
                odsRtSzdnSnapshotFlowAddcode.setSectionCodeStr("");
            }
        }

        TableDataInfo rspData = new TableDataInfo();
        List<OdsRtSzdnSnapshotFlowAddcode> list = new ArrayList<>();
        long total = 0L;

        // 时间段必填
        if (CommonUtil.isNotBlank(odsRtSzdnSnapshotFlowAddcode.getApplyTime1()) && CommonUtil.isNotBlank(odsRtSzdnSnapshotFlowAddcode.getApplyTime2())){
            TableDataInfo tableDataInfo =  httpOdsRtSzdnSnapshotFlowAddcodeService.getOdsRtSzdnSnapshotFlowAddcodePage(odsRtSzdnSnapshotFlowAddcode);
            if (null != tableDataInfo.getRows() && tableDataInfo.getRows().size() > 0) {
                String trackJosn = JSON.toJSONString(tableDataInfo.getRows());
                list = JSON.parseArray(trackJosn, OdsRtSzdnSnapshotFlowAddcode.class);
                total = tableDataInfo.getTotal();
            }
        }
        rspData.setCode(HttpStatus.SUCCESS);
        rspData.setMsg("查询成功");
        rspData.setRows(list);
        rspData.setTotal(total);
        return rspData;


    }

    
    
    @PreAuthorize("@ss.hasPermi('base:snapshotflow:list')")
    @GetMapping("/export")
    public AjaxResult export(OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode, HttpServletResponse response) {
        // 查询日志
        carQueryLogService.queryLog("", "2", "2");
        // 当前页面
        if (null == odsRtSzdnSnapshotFlowAddcode.getPageNum()){
            odsRtSzdnSnapshotFlowAddcode.setPageNum(1);
        }
        // 分页大小
        if (null == odsRtSzdnSnapshotFlowAddcode.getPageSize()){
            odsRtSzdnSnapshotFlowAddcode.setPageSize(10);
        }

        //  路段
        String sectionCodeStr = CommonUtil.deleteEnd(odsRtSzdnSnapshotFlowAddcode.getSectionCodeStr());
        if (CommonUtil.isNotBlank(sectionCodeStr)){
            if (sectionCodeStr.indexOf(Constants.section_all) > -1) {
                odsRtSzdnSnapshotFlowAddcode.setSectionCodeStr("");
            }
        }

        List<OdsRtSzdnSnapshotFlowAddcode> list = new ArrayList<>();

        // 时间段必填
        if (CommonUtil.isNotBlank(odsRtSzdnSnapshotFlowAddcode.getApplyTime1()) && CommonUtil.isNotBlank(odsRtSzdnSnapshotFlowAddcode.getApplyTime2())){
            list = httpOdsRtSzdnSnapshotFlowAddcodeService.getOdsRtSzdnSnapshotFlowAddcodeListToExport(odsRtSzdnSnapshotFlowAddcode);
        }


        // 方向
        Map<String,String> directionMap = sysDictDataService.selectDictDataMap("direction");

        list.stream().forEach(dp -> {
            dp.setDirectionStr(directionMap.get(dp.getDirection().toString()));
        });

        Map<String,Object> map = new HashMap<>();
        map.put("entitylist",list);
        try {
            String url = "templates/export/snapshotFlow.xlsx";
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



    /**
     * 获取门架抓拍流水详细信息
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") String bigId) {
        return AjaxResult.success(httpOdsRtSzdnSnapshotFlowAddcodeService.selectOdsRtSzdnSnapshotFlowAddcodeById(bigId));
    }



    /**
     * 导出门架抓拍流水列表
     */
//    @PreAuthorize("@ss.hasPermi('base:snapshotflow:export')")
//    @Log(title = "门架抓拍流水", businessType = BusinessType.EXPORT)
//    @GetMapping("/export")
//    public AjaxResult export(OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode) {
//        List<OdsRtSzdnSnapshotFlowAddcode> list = httpOdsRtSzdnSnapshotFlowAddcodeService.selectOdsRtSzdnSnapshotFlowAddcodeList(odsRtSzdnSnapshotFlowAddcode);
//        ExcelUtil<OdsRtSzdnSnapshotFlowAddcode> util = new ExcelUtil<OdsRtSzdnSnapshotFlowAddcode>(OdsRtSzdnSnapshotFlowAddcode.class);
//        return util.exportExcel(list, "门架抓拍流水数据");
//    }
}
