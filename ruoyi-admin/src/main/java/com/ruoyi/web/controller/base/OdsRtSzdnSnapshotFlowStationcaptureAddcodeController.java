package com.ruoyi.web.controller.base;

import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowStationcaptureAddcode;
import com.ruoyi.base.service.IOdsRtSzdnSnapshotFlowStationcaptureAddcodeService;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 收费站抓拍Controller
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@RestController
@RequestMapping("/base/stationcapture")
public class OdsRtSzdnSnapshotFlowStationcaptureAddcodeController extends BaseController {

    @Autowired
    private IOdsRtSzdnSnapshotFlowStationcaptureAddcodeService odsRtSzdnSnapshotFlowStationcaptureAddcodeService;

    /**
     * 查询收费站抓拍列表
     */
    @GetMapping("/list")
    public TableDataInfo list(OdsRtSzdnSnapshotFlowStationcaptureAddcode odsRtSzdnSnapshotFlowStationcaptureAddcode) {
        startPage();
        // odsRtSzdnSnapshotFlowStationcaptureAddcode.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<OdsRtSzdnSnapshotFlowStationcaptureAddcode> list = odsRtSzdnSnapshotFlowStationcaptureAddcodeService.selectOdsRtSzdnSnapshotFlowStationcaptureAddcodeList(odsRtSzdnSnapshotFlowStationcaptureAddcode);
        return getDataTable(list);
    }


    /**
     * 获取收费站抓拍详细信息
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") Long bigId) {
        return AjaxResult.success(odsRtSzdnSnapshotFlowStationcaptureAddcodeService.selectOdsRtSzdnSnapshotFlowStationcaptureAddcodeById(bigId));
    }


}
