package com.ruoyi.web.controller.manager;

import java.util.Arrays;
import java.util.List;

import com.ruoyi.common.utils.CommonUtil;
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
import com.ruoyi.manager.domain.CarConfimFree;
import com.ruoyi.manager.service.ICarConfimFreeService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 确认补缴Controller
 *
 * @author ruoyi
 * @date 2025-08-28
 */
@RestController
@RequestMapping("/manager/confimfree")
public class CarConfimFreeController extends BaseController {

    @Autowired
    private ICarConfimFreeService carConfimFreeService;

    /**
     * 查询确认补缴列表
     */
    @PreAuthorize("@ss.hasPermi('manager:confimfree:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarConfimFree carConfimFree) {
        startPage();
        // carConfimFree.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarConfimFree> list = carConfimFreeService.selectCarConfimFreeList(carConfimFree);
        return getDataTable(list);
    }


    /**
     * 查询确认补缴列表:根据车牌号查询
     */
    @GetMapping("/listCarNo")
    public TableDataInfo listCarNo(CarConfimFree carConfimFree) {
        startPage();
        if (CommonUtil.isBlank(carConfimFree.getCarNo())){
            carConfimFree.setCarNo("-1");
        }
        List<CarConfimFree> list = carConfimFreeService.selectCarConfimFreeList(carConfimFree);
        return getDataTable(list);
    }


    /**
     * 导出确认补缴列表
     */
    @PreAuthorize("@ss.hasPermi('manager:confimfree:export')")
    @Log(title = "确认补缴", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarConfimFree carConfimFree) {
        List<CarConfimFree> list = carConfimFreeService.selectCarConfimFreeList(carConfimFree);
        ExcelUtil<CarConfimFree> util = new ExcelUtil<CarConfimFree>(CarConfimFree.class);
        return util.exportExcel(list, "确认补缴数据");
    }

    /**
     * 获取确认补缴详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carConfimFreeService.selectCarConfimFreeById(id));
    }

    /**
     * 新增确认补缴
     */
    @Log(title = "确认补缴", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarConfimFree carConfimFree) {
        return carConfimFreeService.saveCarConfimFree(carConfimFree);
    }

    /**
     * 修改确认补缴
     */
    @Log(title = "确认补缴", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarConfimFree carConfimFree) {
        return carConfimFreeService.saveCarConfimFree(carConfimFree);
    }

    /**
     * 删除确认补缴
     */
    @Log(title = "确认补缴", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carConfimFreeService.deleteCarConfimFreeByIds(ids);
    }


    /**
     * 查询确认追缴:选择异常查询
     */
    @GetMapping(value = "/except/{exceptIds}")
    public AjaxResult getExceptIds(@PathVariable("exceptIds") String exceptIds) {
        return carConfimFreeService.selectCarConfimFreeByExceptIds(exceptIds);
    }

}
