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
import com.ruoyi.manager.domain.CarSuspicious;
import com.ruoyi.manager.service.ICarSuspiciousService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

import javax.servlet.http.HttpServletResponse;

/**
 * 可疑车辆Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@RestController
@RequestMapping("/manager/suspicious")
public class CarSuspiciousController extends BaseController {

    @Autowired
    private ICarSuspiciousService carSuspiciousService;

    @Autowired
    private ISysDictDataService sysDictDataService;

    /**
     * 查询可疑车辆列表：菜单列表
     */
    @PreAuthorize("@ss.hasPermi('manager:suspicious:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarSuspicious carSuspicious) {
        startPage();
        // carSuspicious.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarSuspicious> list = carSuspiciousService.selectCarSuspiciousList(carSuspicious);
        return getDataTable(list);
    }

    /**
     * 查询可疑车辆列表：异常流水弹窗
     */
    @GetMapping("/listAll")
    public TableDataInfo listAll(CarSuspicious carSuspicious) {
        startPage();
        List<CarSuspicious> list = carSuspiciousService.selectCarSuspiciousList(carSuspicious);
        return getDataTable(list);
    }

    /**
     * 导出可疑车辆列表
     */
    @PreAuthorize("@ss.hasPermi('manager:suspicious:export')")
    @Log(title = "可疑车辆", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarSuspicious carSuspicious, HttpServletResponse response) {
        List<CarSuspicious> list = carSuspiciousService.selectCarSuspiciousList(carSuspicious);
        // 车型
        Map<String,String> carTypeMap = sysDictDataService.selectDictDataMap("car_type");

        // 车种
        Map<String,String> carVehicleMap = sysDictDataService.selectDictDataMap("car_vehicle");

        // 逃费类型
        Map<String,String> escapedTypeMap = sysDictDataService.selectDictDataMap("escaped_type");

        Map<String,String> isExceptMap = sysDictDataService.selectDictDataMap("is_except");


        list.stream().forEach(dp -> {
            if (null != dp.getCreateTime()){
                dp.setCreateTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getCreateTime()));
            }
            dp.setCarType(CommonUtil.isNull(carTypeMap.get(dp.getCarType())));
            dp.setCarVehicle(CommonUtil.isNull(carVehicleMap.get(dp.getCarVehicle())));
            dp.setEscapedType(CommonUtil.isNull(escapedTypeMap.get(dp.getEscapedType())));
            dp.setIsExcept(CommonUtil.isNull(isExceptMap.get(dp.getIsExcept())));
        });

        Map<String,Object> map = new HashMap<>();
        map.put("entitylist",list);
        try {
            String url = "templates/export/carSuspicious.xlsx";
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
     * 获取可疑车辆详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carSuspiciousService.selectCarSuspiciousById(id));
    }

    /**
     * 新增可疑车辆
     */
    @PreAuthorize("@ss.hasPermi('manager:suspicious:add')")
    @Log(title = "可疑车辆", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarSuspicious carSuspicious) {
        return carSuspiciousService.saveCarSuspicious(carSuspicious);
    }

    /**
     * 修改可疑车辆
     */
    @PreAuthorize("@ss.hasPermi('manager:suspicious:edit')")
    @Log(title = "可疑车辆", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarSuspicious carSuspicious) {
        return carSuspiciousService.saveCarSuspicious(carSuspicious);
    }

    /**
     * 删除可疑车辆
     */
    @PreAuthorize("@ss.hasPermi('manager:suspicious:remove')")
    @Log(title = "可疑车辆", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carSuspiciousService.deleteCarSuspiciousByIds(ids);
    }




}
