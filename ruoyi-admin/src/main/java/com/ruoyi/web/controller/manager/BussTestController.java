package com.ruoyi.web.controller.manager;

import com.ruoyi.base.service.IGeometryService;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.manager.domain.BussTest;
import com.ruoyi.manager.service.IBussTestService;
import com.ruoyi.manager.service.ICarSuspiciousService;
import com.ruoyi.manager.service.ICarTrackInfoService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.Date;
import java.util.List;

/**
 * 业务测试Controller
 *
 * @author ruoyi
 * @date 2024-09-06
 */
@Slf4j
@RestController
@RequestMapping("/manager/busstest")
public class BussTestController extends BaseController {

    @Autowired
    private IBussTestService bussTestService;

    @Autowired
    private ICarTrackInfoService carTrackInfoService;

    @Autowired
    private ICarSuspiciousService carSuspiciousService;


    @Autowired
    private IGeometryService geometryService;

    /**
     * 查询业务测试列表
     */
    @PreAuthorize("@ss.hasPermi('manager:busstest:list')")
    @GetMapping("/list")
    public TableDataInfo list(BussTest bussTest) {
        startPage();
        // bussTest.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<BussTest> list = bussTestService.selectBussTestList(bussTest);
        return getDataTable(list);
    }

    /**
     * 导出业务测试列表
     */
    @PreAuthorize("@ss.hasPermi('manager:busstest:export')")
    @Log(title = "业务测试", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(BussTest bussTest) {
        List<BussTest> list = bussTestService.selectBussTestList(bussTest);
        ExcelUtil<BussTest> util = new ExcelUtil<BussTest>(BussTest.class);
        return util.exportExcel(list, "业务测试数据");
    }

    /**
     * 获取业务测试详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(bussTestService.selectBussTestById(id));
    }

    /**
     * 新增业务测试
     */
    @PreAuthorize("@ss.hasPermi('manager:busstest:add')")
    @Log(title = "业务测试", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody BussTest bussTest) {
        return bussTestService.saveBussTest(bussTest);
    }

    /**
     * 修改业务测试
     */
    @PreAuthorize("@ss.hasPermi('manager:busstest:edit')")
    @Log(title = "业务测试", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody BussTest bussTest) {
        return bussTestService.saveBussTest(bussTest);
    }

    /**
     * 删除业务测试
     */
    @PreAuthorize("@ss.hasPermi('manager:busstest:remove')")
    @Log(title = "业务测试", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return bussTestService.deleteBussTestByIds(ids);
    }


    /**
     * 可疑车俩
     */
    @PreAuthorize("@ss.hasPermi('manager:busstest:syncTest')")
    @PostMapping("/syncCurrentTrack")
    public void syncCurrentTrack() {
        log.info("车俩实时轨迹同步开始同步！"+new Date());
        carTrackInfoService.syncCurrentTrack();
        log.info("车俩实时轨迹同步结束同步！"+new Date());
    }






}
