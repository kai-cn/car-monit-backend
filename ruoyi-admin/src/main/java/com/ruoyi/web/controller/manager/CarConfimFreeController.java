package com.ruoyi.web.controller.manager;

import java.io.OutputStream;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import cn.afterturn.easypoi.excel.ExcelExportUtil;
import cn.afterturn.easypoi.excel.entity.TemplateExportParams;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.domain.vo.CarConfimFreeQueryRo;
import com.ruoyi.manager.domain.vo.PCCarStatisticsVO;
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
import com.ruoyi.manager.domain.CarConfimFree;
import com.ruoyi.manager.service.ICarConfimFreeService;
import com.ruoyi.common.core.page.TableDataInfo;

import javax.servlet.http.HttpServletResponse;

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
    @Autowired
    private ISysDictDataService sysDictDataService;

    /**
     * 查询确认补缴列表
     */
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
     * 查询确认补缴列表:根据车牌号查询
     */
    @GetMapping("/listCount")
    public AjaxResult listCount(CarConfimFree carConfimFree) {
        if (CommonUtil.isBlank(carConfimFree.getCarNo())) {
            carConfimFree.setCarNo("-1");
        }
        CarConfimFree rtn = carConfimFreeService.listCount(carConfimFree);
        return AjaxResult.success(rtn);
    }


    /**
     * 导出确认补缴列表
     */
    @Log(title = "确认补缴", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarConfimFree carConfimFree, HttpServletResponse response) {
        List<CarConfimFree> list = carConfimFreeService.selectCarConfimFreeList(carConfimFree);
        // 车型
        Map<String,String> carTypeMap = sysDictDataService.selectDictDataMap("car_type");
        // 车种
        Map<String,String> carVehicleMap = sysDictDataService.selectDictDataMap("car_vehicle");


        list.stream().forEach(dp -> {
            dp.setCarType(CommonUtil.isNull(carTypeMap.get(dp.getCarType())));
            dp.setCarVehicle(CommonUtil.isNull(carVehicleMap.get(dp.getCarVehicle())));
        });

        Map<String,Object> map = new HashMap<>();
        map.put("entitylist",list);
        try {
            String url = "templates/export/carConfirm.xlsx";
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

    /**
     * 待关注车辆
     */
    @GetMapping("/concernedList")
    public TableDataInfo concernedList(CarConfimFree carConfimFree) {
        startPage();
        List<CarConfimFree> list = carConfimFreeService.selectConcernedList(carConfimFree);
        return getDataTable(list);
    }

    /**
     * 待关注车辆导出
     */
    @GetMapping(value = "/exportConcernedList")
    public AjaxResult exportConcernedList(CarConfimFree carConfimFree, HttpServletResponse response) {
        List<CarConfimFree> list = carConfimFreeService.selectConcernedList(carConfimFree);
        // 车型
        Map<String,String> carTypeMap = sysDictDataService.selectDictDataMap("car_type");
        // 车种
        Map<String,String> carVehicleMap = sysDictDataService.selectDictDataMap("car_vehicle");
        // 逃费类型
        Map<String,String> escapedTypeMap = sysDictDataService.selectDictDataMap("escaped_type");


        list.stream().forEach(dp -> {
            dp.setCarType(CommonUtil.isNull(carTypeMap.get(dp.getCarType())));
            dp.setCarVehicle(CommonUtil.isNull(carVehicleMap.get(dp.getCarVehicle())));
            // 需要循环 : 逃费类型
            String bussName = "";
            String bussType = CommonUtil.deleteEnd(dp.getEscapedType());
            if (CommonUtil.isNotBlank(bussType)) {
                String[] bussTypeStr = bussType.split(",");
                for (int i = 0; i < bussTypeStr.length; i++) {
                    if (escapedTypeMap.containsKey(bussTypeStr[i])) {
                        bussName = bussName + escapedTypeMap.get(bussTypeStr[i]) + ",";
                    }
                }
            }
            dp.setEscapedType(CommonUtil.deleteEnd(bussName));
        });

        Map<String,Object> map = new HashMap<>();
        map.put("entitylist",list);
        try {
            String url = "templates/export/carConfirm.xlsx";
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
     * pc统计
     */
    @GetMapping(value = "/carStatics")
    public TableDataInfo getCarStatics(CarConfimFreeQueryRo queryRo) {
        startPage();
        List<PCCarStatisticsVO> list = carConfimFreeService.getPCCarStatistics(queryRo);
        return getDataTable(list);
    }

    /**
     * pc统计导出
     */
    @GetMapping(value = "/exportCarStatics")
    public AjaxResult exportCarStatics(CarConfimFreeQueryRo queryRo, HttpServletResponse response) {
        List<PCCarStatisticsVO> list = carConfimFreeService.getPCCarStatistics(queryRo);
        Map<String,Object> map = new HashMap<>();
        map.put("entitylist",list);
        try {
            String url = "templates/export/carStatistics.xlsx";
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

}
