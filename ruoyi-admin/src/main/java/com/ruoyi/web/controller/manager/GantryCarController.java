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
import com.ruoyi.manager.domain.GantryCar;
import com.ruoyi.manager.service.IGantryCarService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

import jakarta.servlet.http.HttpServletResponse;

/**
 * 门架拍识查询Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@RestController
@RequestMapping("/manager/gantrycar")
public class GantryCarController extends BaseController {

    @Autowired
    private IGantryCarService gantryCarService;
    @Autowired
    private ISysDictDataService sysDictDataService;
    /**
     * 查询门架拍识查询列表
     */
    @PreAuthorize("@ss.hasPermi('manager:gantrycar:list')")
    @GetMapping("/list")
    public TableDataInfo list(GantryCar gantryCar) {
        startPage();
        // gantryCar.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<GantryCar> list = gantryCarService.selectGantryCarList(gantryCar);
        return getDataTable(list);
    }

    /**
     * 导出门架拍识查询列表
     */
    @PreAuthorize("@ss.hasPermi('manager:gantrycar:export')")
    @Log(title = "门架拍识查询", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(GantryCar gantryCar, HttpServletResponse response) {
        List<GantryCar> list = gantryCarService.selectGantryCarList(gantryCar);
        // 车型
        Map<String,String> carTypeMap = sysDictDataService.selectDictDataMap("car_type");
        // 车种
        Map<String,String> carVehicleMap = sysDictDataService.selectDictDataMap("car_vehicle");

        list.stream().forEach(dp -> {
            if (null != dp.getCreateTime()){
                dp.setCreateTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getCreateTime()));
            }
            dp.setCarType(CommonUtil.isNull(carTypeMap.get(dp.getCarType())));
            dp.setCarVehicle(CommonUtil.isNull(carVehicleMap.get(dp.getCarVehicle())));
        });

        Map<String,Object> map = new HashMap<>();
        map.put("entitylist",list);
        try {
            String url = "templates/export/gantryCar.xlsx";
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
     * 获取门架拍识查询详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(gantryCarService.selectGantryCarById(id));
    }

    /**
     * 新增门架拍识查询
     */
    @PreAuthorize("@ss.hasPermi('manager:gantrycar:add')")
    @Log(title = "门架拍识查询", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody GantryCar gantryCar) {
        return gantryCarService.saveGantryCar(gantryCar);
    }

    /**
     * 修改门架拍识查询
     */
    @PreAuthorize("@ss.hasPermi('manager:gantrycar:edit')")
    @Log(title = "门架拍识查询", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody GantryCar gantryCar) {
        return gantryCarService.saveGantryCar(gantryCar);
    }

    /**
     * 删除门架拍识查询
     */
    @PreAuthorize("@ss.hasPermi('manager:gantrycar:remove')")
    @Log(title = "门架拍识查询", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return gantryCarService.deleteGantryCarByIds(ids);
    }

}
