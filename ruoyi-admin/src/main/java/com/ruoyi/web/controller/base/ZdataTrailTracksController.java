package com.ruoyi.web.controller.base;

import com.ruoyi.base.domain.ZdataTrailTracks;
import com.ruoyi.base.service.IZdataTrailTracksService;
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
 * 轨迹数据Controller
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@RestController
@RequestMapping("/base/trailtracks")
public class ZdataTrailTracksController extends BaseController {

    @Autowired
    private IZdataTrailTracksService zdataTrailTracksService;

    /**
     * 查询轨迹数据列表
     */
    @GetMapping("/list")
    public TableDataInfo list(ZdataTrailTracks zdataTrailTracks) {
        startPage();
        // zdataTrailTracks.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<ZdataTrailTracks> list = zdataTrailTracksService.selectZdataTrailTracksList(zdataTrailTracks);
        return getDataTable(list);
    }


    /**
     * 获取轨迹数据详细信息
     */
    @GetMapping(value = "/{uuid}")
    public AjaxResult getInfo(@PathVariable("uuid") String uuid) {
        return AjaxResult.success(zdataTrailTracksService.selectZdataTrailTracksById(uuid));
    }

}
