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
import com.ruoyi.manager.domain.CarInfo;
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
import com.ruoyi.manager.domain.CarRouteInfo;
import com.ruoyi.manager.service.ICarRouteInfoService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

import jakarta.servlet.http.HttpServletResponse;

/**
 * 常用路线Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@RestController
@RequestMapping("/manager/routeinfo")
public class CarRouteInfoController extends BaseController {

    @Autowired
    private ICarRouteInfoService carRouteInfoService;

    @Autowired
    private ISysDictDataService sysDictDataService;

    /**
     * 查询常用路线列表
     */
    @PreAuthorize("@ss.hasPermi('manager:routeinfo:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarRouteInfo carRouteInfo) {
        startPage();
        // carRouteInfo.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarRouteInfo> list = carRouteInfoService.selectCarRouteInfoList(carRouteInfo);
        return getDataTable(list);
    }

    /**
     * 导出常用路线列表
     */
    @PreAuthorize("@ss.hasPermi('manager:routeinfo:export')")
    @Log(title = "常用路线", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarRouteInfo carRouteInfo, HttpServletResponse response) {
        List<CarRouteInfo> list = carRouteInfoService.selectCarRouteInfoList(carRouteInfo);
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
            String url = "templates/export/carRouterInfo.xlsx";
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
     * 获取常用路线详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carRouteInfoService.selectCarRouteInfoById(id));
    }

    /**
     * 新增常用路线
     */
    @PreAuthorize("@ss.hasPermi('manager:routeinfo:add')")
    @Log(title = "常用路线", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarRouteInfo carRouteInfo) {
        return carRouteInfoService.saveCarRouteInfo(carRouteInfo);
    }

    /**
     * 修改常用路线
     */
    @PreAuthorize("@ss.hasPermi('manager:routeinfo:edit')")
    @Log(title = "常用路线", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarRouteInfo carRouteInfo) {
        return carRouteInfoService.saveCarRouteInfo(carRouteInfo);
    }

    /**
     * 删除常用路线
     */
    @PreAuthorize("@ss.hasPermi('manager:routeinfo:remove')")
    @Log(title = "常用路线", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carRouteInfoService.deleteCarRouteInfoByIds(ids);
    }

}
