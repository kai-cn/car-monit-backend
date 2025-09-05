package com.ruoyi.web.controller.base;

import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.service.forest.HttpOdsRtSzdnSnapshotFlowAddcodeService;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.exception.ServiceException;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;

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

    /**
     * 查询门架抓拍流水列表
     */
    @PreAuthorize("@ss.hasPermi('base:snapshotflow:list')")
    @GetMapping("/list")
    public TableDataInfo list(OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode) {

        // 当前页面
        if (null == odsRtSzdnSnapshotFlowAddcode.getPageNum()){
            odsRtSzdnSnapshotFlowAddcode.setPageNum(1);
        }
        // 分页大小
        if (null == odsRtSzdnSnapshotFlowAddcode.getPageSize()){
            odsRtSzdnSnapshotFlowAddcode.setPageSize(10);
        }

        JSONObject jsonObject = httpOdsRtSzdnSnapshotFlowAddcodeService.getOdsRtSzdnSnapshotFlowAddcodePage(odsRtSzdnSnapshotFlowAddcode);
        if(null == jsonObject || 200 != jsonObject.getInt("code")){
            logger.error("门架抓拍流水数据获取异常：" + jsonObject);
            throw new ServiceException("获取数据异常,请联系管理员");
        }
        return JSONUtil.toBean(jsonObject, TableDataInfo.class);
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
