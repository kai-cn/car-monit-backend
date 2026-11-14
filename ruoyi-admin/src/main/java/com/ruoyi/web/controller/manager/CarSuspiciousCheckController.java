package com.ruoyi.web.controller.manager;

import java.io.OutputStream;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import cn.afterturn.easypoi.excel.ExcelExportUtil;
import cn.afterturn.easypoi.excel.entity.TemplateExportParams;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.system.service.ISysDictDataService;
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
import com.ruoyi.manager.domain.CarSuspiciousCheck;
import com.ruoyi.manager.service.ICarSuspiciousCheckService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

import jakarta.servlet.http.HttpServletResponse;

/**
 * 可疑车辆人工核实Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@RestController
@RequestMapping("/manager/suspiciouscheck")
public class CarSuspiciousCheckController extends BaseController {

    @Autowired
    private ICarSuspiciousCheckService carSuspiciousCheckService;
    @Autowired
    private ISysDictDataService sysDictDataService;

    /**
     * 查询可疑车辆人工核实列表
     */
    @PreAuthorize("@ss.hasPermi('manager:suspiciouscheck:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarSuspiciousCheck carSuspiciousCheck) {
        startPage();
        // carSuspiciousCheck.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarSuspiciousCheck> list = carSuspiciousCheckService.selectCarSuspiciousCheckList(carSuspiciousCheck);
        return getDataTable(list);
    }

    /**
     * 导出可疑车辆人工核实列表
     */
    @PreAuthorize("@ss.hasPermi('manager:suspiciouscheck:export')")
    @Log(title = "可疑车辆人工核实", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarSuspiciousCheck carSuspiciousCheck, HttpServletResponse response) {
        List<CarSuspiciousCheck> list = carSuspiciousCheckService.selectCarSuspiciousCheckList(carSuspiciousCheck);

        list.stream().forEach(dp -> {
            if (null != dp.getCreateTime()){
                dp.setCreateTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getCreateTime()));
            }
        });

        Map<String,Object> map = new HashMap<>();
        map.put("entitylist",list);
        try {
            String url = "templates/export/carSuspiciousCheck.xlsx";
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
     * 获取可疑车辆人工核实详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carSuspiciousCheckService.selectCarSuspiciousCheckById(id));
    }

    /**
     * 新增可疑车辆人工核实
     */
    @PreAuthorize("@ss.hasPermi('manager:suspiciouscheck:add')")
    @Log(title = "可疑车辆人工核实", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarSuspiciousCheck carSuspiciousCheck) {
        return carSuspiciousCheckService.saveCarSuspiciousCheck(carSuspiciousCheck);
    }

    /**
     * 修改可疑车辆人工核实
     */
    @PreAuthorize("@ss.hasPermi('manager:suspiciouscheck:edit')")
    @Log(title = "可疑车辆人工核实", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarSuspiciousCheck carSuspiciousCheck) {
        return carSuspiciousCheckService.saveCarSuspiciousCheck(carSuspiciousCheck);
    }

    /**
     * 删除可疑车辆人工核实
     */
    @PreAuthorize("@ss.hasPermi('manager:suspiciouscheck:remove')")
    @Log(title = "可疑车辆人工核实", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carSuspiciousCheckService.deleteCarSuspiciousCheckByIds(ids);
    }

}
