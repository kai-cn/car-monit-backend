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
import com.ruoyi.manager.domain.CarExceptRecord;
import com.ruoyi.manager.service.ICarExceptRecordService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

import javax.servlet.http.HttpServletResponse;

/**
 * 异常车辆流水Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@RestController
@RequestMapping("/manager/exceptrecord")
public class CarExceptRecordController extends BaseController {

    @Autowired
    private ICarExceptRecordService carExceptRecordService;
    @Autowired
    private ISysDictDataService sysDictDataService;

    /**
     * 查询异常车辆流水列表
     */
    @PreAuthorize("@ss.hasPermi('manager:exceptrecord:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarExceptRecord carExceptRecord) {
        startPage();
        // carExceptRecord.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarExceptRecord> list = carExceptRecordService.selectCarExceptRecordList(carExceptRecord);
        return getDataTable(list);
    }


    /**
     * 根据车牌号查询: 根据车牌号查询
     * @param carExceptRecord
     * @return
     */
    @GetMapping("/listCarNo")
    public TableDataInfo listCarNo(CarExceptRecord carExceptRecord) {
        startPage();
        if (CommonUtil.isBlank(carExceptRecord.getCarNo())){
            carExceptRecord.setCarNo("-1");
        }
        List<CarExceptRecord> list = carExceptRecordService.selectCarExceptRecordList(carExceptRecord);
        return getDataTable(list);
    }

    /**
     * 根据车牌号查询统计
     */
    @GetMapping(value = "/exceptRecordCount")
    public AjaxResult exceptRecordCount(CarExceptRecord carExceptRecord) {
        if (CommonUtil.isBlank(carExceptRecord.getCarNo())){
            carExceptRecord.setCarNo("-1");
        }
        return AjaxResult.success(carExceptRecordService.exceptRecordCount(carExceptRecord));
    }



    /**
     * 导出异常车辆流水列表
     */
    @Log(title = "异常车辆流水", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarExceptRecord carExceptRecord, HttpServletResponse response) {
        List<CarExceptRecord> list = carExceptRecordService.selectCarExceptRecordList(carExceptRecord);
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

        Map<String,Object> map = new HashMap<>();
        map.put("entitylist",list);
        try {
            String url = "templates/export/carExceptRecord.xlsx";
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
     * 获取异常车辆流水详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carExceptRecordService.selectCarExceptRecordById(id));
    }

    /**
     * 新增异常车辆流水
     */
    @Log(title = "异常车辆流水", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarExceptRecord carExceptRecord) {
        return carExceptRecordService.saveCarExceptRecord(carExceptRecord);
    }

    /**
     * 修改异常车辆流水
     */
    @Log(title = "异常车辆流水", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarExceptRecord carExceptRecord) {
        return carExceptRecordService.saveCarExceptRecord(carExceptRecord);
    }

    /**
     * 删除异常车辆流水
     */
    @Log(title = "异常车辆流水", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carExceptRecordService.deleteCarExceptRecordByIds(ids);
    }

}
