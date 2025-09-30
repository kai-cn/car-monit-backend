package com.ruoyi.web.controller.manager;

import cn.afterturn.easypoi.excel.ExcelExportUtil;
import cn.afterturn.easypoi.excel.entity.TemplateExportParams;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.manager.domain.CarWarningInfo;
import com.ruoyi.manager.service.ICarWarningInfoService;
import com.ruoyi.system.service.ISysDictDataService;
import org.apache.poi.ss.usermodel.Workbook;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletResponse;
import java.io.OutputStream;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 预警车辆Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@RestController
@RequestMapping("/manager/carwarning")
public class CarWarningInfoController extends BaseController {

    @Autowired
    private ICarWarningInfoService carWarningInfoService;

    @Autowired
    private ISysDictDataService sysDictDataService;

    /**
     * 查询预警车辆列表
     */
    // @PreAuthorize("@ss.hasPermi('manager:carwarning:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarWarningInfo carWarningInfo) {
        startPage();
        // carWarningInfo.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarWarningInfo> list = carWarningInfoService.selectCarWarningInfoList(carWarningInfo);
        return getDataTable(list);
    }

    /**
     * 导出预警车辆列表
     */
    @PreAuthorize("@ss.hasPermi('manager:carwarning:export')")
    @Log(title = "预警车辆", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarWarningInfo carWarningInfo, HttpServletResponse response) {
        List<CarWarningInfo> list = carWarningInfoService.selectCarWarningInfoList(carWarningInfo);
        // 车型
        Map<String,String> carTypeMap = sysDictDataService.selectDictDataMap("car_type");
        // 车种
        Map<String,String> carVehicleMap = sysDictDataService.selectDictDataMap("car_vehicle");
        // 逃费类型
        Map<String,String> escapedTypeMap = sysDictDataService.selectDictDataMap("escaped_type");


        list.stream().forEach(dp -> {
            if (null != dp.getGantryTime()){
                dp.setGantryTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getGantryTime()));
            }
            if (null != dp.getCreateTime()){
                dp.setCreateTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getCreateTime()));
            }
            dp.setCarType(CommonUtil.isNull(carTypeMap.get(dp.getCarType())));
            dp.setCarVehicle(CommonUtil.isNull(carVehicleMap.get(dp.getCarVehicle())));
            dp.setEscapedType(CommonUtil.isNull(escapedTypeMap.get(dp.getEscapedType())));
        });

        Map<String,Object> map = new HashMap<>();
        map.put("entitylist",list);
        try {
            String url = "templates/export/carWarningInfo.xlsx";
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
     * 获取预警车辆详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carWarningInfoService.selectCarWarningInfoById(id));
    }

    /**
     * 新增预警车辆
     */
    @PreAuthorize("@ss.hasPermi('manager:carwarning:add')")
    @Log(title = "预警车辆", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarWarningInfo carWarningInfo) {
        return carWarningInfoService.saveCarWarningInfo(carWarningInfo);
    }

    /**
     * 修改预警车辆
     */
    @PreAuthorize("@ss.hasPermi('manager:carwarning:edit')")
    @Log(title = "预警车辆", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarWarningInfo carWarningInfo) {
        return carWarningInfoService.saveCarWarningInfo(carWarningInfo);
    }

    /**
     * 删除预警车辆
     */
    @PreAuthorize("@ss.hasPermi('manager:carwarning:remove')")
    @Log(title = "预警车辆", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carWarningInfoService.deleteCarWarningInfoByIds(ids);
    }


}
