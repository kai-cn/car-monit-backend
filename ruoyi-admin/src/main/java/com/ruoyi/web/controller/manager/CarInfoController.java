package com.ruoyi.web.controller.manager;

import java.io.OutputStream;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import cn.afterturn.easypoi.excel.ExcelExportUtil;
import cn.afterturn.easypoi.excel.entity.TemplateExportParams;
import com.ruoyi.common.core.domain.entity.SysDictData;
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
import com.ruoyi.manager.domain.CarInfo;
import com.ruoyi.manager.service.ICarInfoService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

import javax.servlet.http.HttpServletResponse;

/**
 * 车辆信息Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@RestController
@RequestMapping("/manager/carinfo")
public class CarInfoController extends BaseController {

    @Autowired
    private ICarInfoService carInfoService;

    @Autowired
    private ISysDictDataService sysDictDataService;

    /**
     * 查询车辆信息列表
     */
    @PreAuthorize("@ss.hasPermi('manager:carinfo:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarInfo carInfo) {
        startPage();
        // carInfo.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarInfo> list = carInfoService.selectCarInfoList(carInfo);
        return getDataTable(list);
    }

    /**
     * 导出车辆信息列表
     */
    @PreAuthorize("@ss.hasPermi('manager:carinfo:export')")
    @Log(title = "车辆信息", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarInfo carInfo, HttpServletResponse response) {
        List<CarInfo> list = carInfoService.selectCarInfoList(carInfo);

        // 车型
        Map<String,String> carTypeMap = sysDictDataService.selectDictDataMap("car_type");

         // 车种
        Map<String,String> carVehicleMap = sysDictDataService.selectDictDataMap("car_vehicle");

        // 逃费类型
        Map<String,String> escapedTypeMap = sysDictDataService.selectDictDataMap("escaped_type");


        list.stream().forEach(dp -> {
            if (null != dp.getCreateTime()){
                dp.setCreateTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getCreateTime()));
            }
            dp.setCarType(CommonUtil.isNull(carTypeMap.get(dp.getCarType())));
            dp.setCarVehicle(CommonUtil.isNull(carVehicleMap.get(dp.getCarVehicle())));
            dp.setEscapedType(CommonUtil.isNull(escapedTypeMap.get(dp.getEscapedType())));
        });

        Map<String,Object> map = new HashMap<String,Object>();
        map.put("entitylist",list);
        try {
            String url = "templates/export/carInfo.xlsx";
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
     * 获取车辆信息详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carInfoService.selectCarInfoById(id));
    }

    /**
     * 新增车辆信息
     */
    @PreAuthorize("@ss.hasPermi('manager:carinfo:add')")
    @Log(title = "车辆信息", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarInfo carInfo) {
        return carInfoService.saveCarInfo(carInfo);
    }

    /**
     * 修改车辆信息
     */
    @PreAuthorize("@ss.hasPermi('manager:carinfo:edit')")
    @Log(title = "车辆信息", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarInfo carInfo) {
        return carInfoService.saveCarInfo(carInfo);
    }

    /**
     * 删除车辆信息
     */
    @PreAuthorize("@ss.hasPermi('manager:carinfo:remove')")
    @Log(title = "车辆信息", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carInfoService.deleteCarInfoByIds(ids);
    }

}
