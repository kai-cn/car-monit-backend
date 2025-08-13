package com.ruoyi.web.controller.manager;

import java.util.Arrays;
import java.util.List;
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
import com.ruoyi.manager.domain.BussTest;
import com.ruoyi.manager.service.IBussTestService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 业务测试Controller
 *
 * @author ruoyi
 * @date 2024-09-06
 */
@RestController
@RequestMapping("/manager/busstest")
public class BussTestController extends BaseController {

    @Autowired
    private IBussTestService bussTestService;

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

}
