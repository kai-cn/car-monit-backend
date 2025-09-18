package com.ruoyi.web.controller.base;

import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowProvcaptureAddcode;
import com.ruoyi.base.service.IOdsRtSzdnSnapshotFlowProvcaptureAddcodeService;
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
 * 省界抓拍Controller
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@RestController
@RequestMapping("/base/provcapture")
public class OdsRtSzdnSnapshotFlowProvcaptureAddcodeController extends BaseController {

    @Autowired
    private IOdsRtSzdnSnapshotFlowProvcaptureAddcodeService odsRtSzdnSnapshotFlowProvcaptureAddcodeService;

    /**
     * 查询省界抓拍列表
     */
    @GetMapping("/list")
    public TableDataInfo list(OdsRtSzdnSnapshotFlowProvcaptureAddcode odsRtSzdnSnapshotFlowProvcaptureAddcode) {
        startPage();
        // odsRtSzdnSnapshotFlowProvcaptureAddcode.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<OdsRtSzdnSnapshotFlowProvcaptureAddcode> list = odsRtSzdnSnapshotFlowProvcaptureAddcodeService.selectOdsRtSzdnSnapshotFlowProvcaptureAddcodeList(odsRtSzdnSnapshotFlowProvcaptureAddcode);
        return getDataTable(list);
    }


    /**
     * 获取省界抓拍详细信息
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") Long bigId) {
        return AjaxResult.success(odsRtSzdnSnapshotFlowProvcaptureAddcodeService.selectOdsRtSzdnSnapshotFlowProvcaptureAddcodeById(bigId));
    }


}
