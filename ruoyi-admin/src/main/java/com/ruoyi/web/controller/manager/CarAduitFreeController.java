package com.ruoyi.web.controller.manager;

import java.io.OutputStream;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import cn.afterturn.easypoi.excel.ExcelExportUtil;
import cn.afterturn.easypoi.excel.entity.TemplateExportParams;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.domain.CarConfimFree;
import com.ruoyi.manager.domain.vo.CarConfimFreeQueryRo;
import com.ruoyi.manager.domain.vo.PCIncomeStaticsVO;
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
import com.ruoyi.manager.domain.CarAduitFree;
import com.ruoyi.manager.service.ICarAduitFreeService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

import javax.servlet.http.HttpServletResponse;

/**
 * 补缴处理Controller
 *
 * @author ruoyi
 * @date 2025-08-28
 */
@RestController
@RequestMapping("/manager/aduitfree")
public class CarAduitFreeController extends BaseController {

    @Autowired
    private ICarAduitFreeService carAduitFreeService;

    /**
     * 查询补缴处理列表
     */
    @GetMapping("/list")
    public TableDataInfo list(CarAduitFree carAduitFree) {
        startPage();
        // carAduitFree.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarAduitFree> list = carAduitFreeService.selectCarAduitFreeList(carAduitFree);
        return getDataTable(list);
    }




    /**
     * 导出补缴处理列表
     */
    @Log(title = "补缴处理", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarAduitFree carAduitFree) {
        List<CarAduitFree> list = carAduitFreeService.selectCarAduitFreeList(carAduitFree);
        ExcelUtil<CarAduitFree> util = new ExcelUtil<CarAduitFree>(CarAduitFree.class);
        return util.exportExcel(list, "补缴处理数据");
    }

    /**
     * 获取补缴处理详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carAduitFreeService.selectCarAduitFreeById(id));
    }

    /**
     * 新增补缴处理
     */
    @Log(title = "补缴处理", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarAduitFree carAduitFree) {
        return carAduitFreeService.saveCarAduitFree(carAduitFree);
    }

    /**
     * 修改补缴处理
     */
    @Log(title = "补缴处理", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarAduitFree carAduitFree) {
        return carAduitFreeService.saveCarAduitFree(carAduitFree);
    }

    /**
     * 删除补缴处理
     */
    @Log(title = "补缴处理", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carAduitFreeService.deleteCarAduitFreeByIds(ids);
    }

    /**
     * pc统计：堵漏增收
     */
    @GetMapping(value = "/incomeStatics")
    public TableDataInfo incomeStatics(CarConfimFreeQueryRo queryRo) {
        startPage();
        List<PCIncomeStaticsVO> list = carAduitFreeService.getPCIncomeStatics(queryRo);
        return getDataTable(list);
    }

    /**
     * pc统计导出：堵漏增收
     */
    @GetMapping(value = "/exportIncomeStatics")
    public AjaxResult exportIncomeStatics(CarConfimFreeQueryRo queryRo, HttpServletResponse response) {
        List<PCIncomeStaticsVO> list = carAduitFreeService.getPCIncomeStatics(queryRo);
        Map<String,Object> map = new HashMap<>();
        map.put("entitylist",list);
        try {
            String url = "templates/export/incomeStatics.xlsx";
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
     * 明细-----------------
     * @param carConfimFree
     * @return
     */
    @GetMapping("/incomeDetailList")
    public TableDataInfo incomeDetailList(CarConfimFree carConfimFree) {
        startPage();
        if (CommonUtil.isBlank(carConfimFree.getOrgId())){
            carConfimFree.setOrgId("-1");
        }
        List<CarConfimFree> list = carAduitFreeService.incomeDetailList(carConfimFree);
        return getDataTable(list);
    }




}
