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
import com.ruoyi.manager.domain.CarInfo;
import com.ruoyi.manager.service.ICarInfoService;
import com.ruoyi.system.service.ISysDictDataService;
import com.ruoyi.web.util.ImportEntity;
import com.ruoyi.web.util.ImportErrorEntity;
import com.ruoyi.web.util.ImportSysUtil;
import com.ruoyi.web.util.ImportUtil;
import org.apache.poi.ss.usermodel.Workbook;
import org.apache.poi.xssf.usermodel.XSSFSheet;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import javax.servlet.http.HttpServletResponse;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

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
     * 查询车辆信息列表：菜单
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
     * 查询车辆信息列表：弹出窗口选择
     */
    @GetMapping("/listAll")
    public TableDataInfo listAll(CarInfo carInfo) {
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

        // 车牌颜色
        Map<String,String> plateColorMap = sysDictDataService.selectDictDataMap("plate_color");

        // 车型
        Map<String,String> carTypeMap = sysDictDataService.selectDictDataMap("car_type");

         // 车种
        Map<String,String> carVehicleMap = sysDictDataService.selectDictDataMap("car_vehicle");

        // 逃费类型
        Map<String,String> escapedTypeMap = sysDictDataService.selectDictDataMap("escaped_type");

        // 车辆实时状态
        Map<String,String> statusMap = sysDictDataService.selectDictDataMap("car_run_status");


        list.stream().forEach(dp -> {
            if (null != dp.getCreateTime()){
                dp.setCreateTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getCreateTime()));
            }
            dp.setPlateColor(CommonUtil.isNull(plateColorMap.get(dp.getPlateColor())));
            dp.setCarType(CommonUtil.isNull(carTypeMap.get(dp.getCarType())));
            dp.setCarVehicle(CommonUtil.isNull(carVehicleMap.get(dp.getCarVehicle())));
            dp.setStatus(CommonUtil.isNull(statusMap.get(dp.getStatus())));


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

    @Log(title = "车辆信息", businessType = BusinessType.IMPORT)
    @PostMapping("/import")
    public AjaxResult doImport(@RequestParam("file") MultipartFile file) throws Exception {
        // 校验文件格式
        String fileName = file.getOriginalFilename();
        if (fileName.lastIndexOf(".xlsx") == -1) {
            return AjaxResult.error("请上传Excel文件(.xlsx)");
        }
        ImportSysUtil importUtil = new ImportSysUtil();
        XSSFSheet sheet = importUtil.getXSSFSheet(file.getInputStream(), 0); // 得到sheet页
        List<ImportEntity> gzList = initList(); // 初始化导入头部、属性、校验规则

        // 获取头部
        String[] colsName =  new String[gzList.size()];
        for (int i = 0; i < gzList.size(); i++) {
            colsName[i] = gzList.get(i).getColName();
        }
        // 校验头部
        if (!importUtil.colVdaExcel07(sheet, colsName)) {
            return AjaxResult.error("导入失败,模板不正确,请下载对应的模板！");
        }
        // 校验数据
        List<String[]> sheetList = importUtil.dataRtnExcel07(sheet, colsName); // 返回结果集
        if (sheetList.size() == 0) {
            return AjaxResult.error("导入失败,模板excel没有数据可以导入，请确定！");
        }
        // 校验数据格式
        List<ImportErrorEntity> errorList = new ArrayList<ImportErrorEntity>(); // 错误列表
        List<CarInfo> importList = new ArrayList<CarInfo>(); // 导入的数据
        for (int i = 0; i < sheetList.size(); i++) {
            String[] strs = sheetList.get(i);
            Object rtnObj = ImportUtil.importExcel(errorList, gzList, i, strs, CarInfo.class); // 结果集转对象
            if (errorList.size() == 0 && null != rtnObj) {
                CarInfo importbo = (CarInfo) rtnObj;
                importList.add(importbo);
            }

            if (errorList.size() > 100){
                break;
            }
        }

        // 校验数据
        if (errorList.size() == 0) {

            //字典

            // 车牌颜色
            Map<String,String> plateColorMap = sysDictDataService.selectDictDataLaleMap("plate_color");

            // 车型
            Map<String,String> carTypeMap = sysDictDataService.selectDictDataLaleMap("car_type");

            // 车种
            Map<String,String> carVehicleMap = sysDictDataService.selectDictDataLaleMap("car_vehicle");

            // 逃费类型
            Map<String,String> escapedTypeMap = sysDictDataService.selectDictDataLaleMap("escaped_type");



            for (int i = 0; i < importList.size(); i++) {
                CarInfo addbo = importList.get(i);

                // 车牌颜色
                String plateColor =  CommonUtil.isNull(addbo.getPlateColor());
                if (CommonUtil.isNotBlank(plateColor)){
                    if (plateColorMap.containsKey(plateColor)) {
                        addbo.setPlateColor(CommonUtil.isNull(plateColorMap.get(plateColor)));
                    } else {
                        errorList.add(importUtil.getErrorBO(i + 1, "车牌颜色", plateColor + " 车牌颜色不存在,请在字典菜单维护！"));
                    }
                }

                // 车型
                String carType =  CommonUtil.isNull(addbo.getCarType());
                if (CommonUtil.isNotBlank(carType)){
                    if (carTypeMap.containsKey(carType)) {
                        addbo.setCarType(CommonUtil.isNull(carTypeMap.get(carType)));
                    } else {
                        errorList.add(importUtil.getErrorBO(i + 1, "车型", carType + " 车型不存在,请在字典菜单维护！"));
                    }
                }


                // 车种
                String carVehicle =  CommonUtil.isNull(addbo.getCarVehicle());
                if (CommonUtil.isNotBlank(carVehicle)){
                    if (carVehicleMap.containsKey(carVehicle)) {
                        addbo.setCarType(CommonUtil.isNull(carVehicleMap.get(carVehicle)));
                    } else {
                        errorList.add(importUtil.getErrorBO(i + 1, "车种", carVehicle + " 车种不存在,请在字典菜单维护！"));
                    }
                }

                // 逃费类型
                String escapedType = CommonUtil.deleteEnd(addbo.getEscapedType());
                escapedType = escapedType.replace("，", ",");
                String escapedTypeValue = "";
                if (!escapedType.equals("")){
                    String[] bussTypeStr = escapedType.split(",");
                    for (int zz = 0; zz < bussTypeStr.length; zz++) {
                        if (escapedTypeMap.containsKey(bussTypeStr[zz])) {
                            escapedTypeValue = escapedTypeValue + CommonUtil.isNull(escapedTypeMap.get(bussTypeStr[zz])) + ",";
                        }
                        else {
                            errorList.add(importUtil.getErrorBO(i + 1, "逃费类型", bussTypeStr[zz] + " 逃费类型不存在,请在字典菜单维护！"));
                        }
                    }
                }
                addbo.setEscapedType(CommonUtil.deleteEnd(escapedTypeValue));

                if (errorList.size() > 100){
                    break;
                }
            }

        }

        // 插入数据库
        if (errorList.size() == 0) {
            for (int i = 0; i < importList.size(); i++) {
                CarInfo addbo = importList.get(i);
                addbo.setCarNo(CommonUtil.isNull(addbo.getCarNo())); //去掉空格
                // 根据车牌号
                CarInfo querybo = new CarInfo();
                querybo.setCarNo(CommonUtil.isNull(addbo.getCarNo()));
                List<CarInfo> queryList = carInfoService.selectCarInfoList(querybo);
                if (queryList.size() > 0) {
                    addbo.setId(queryList.get(0).getId());
                }
            }
            carInfoService.doImport(importList);
        }

        // 错误提示
        if (errorList.size() > 0) {
            return AjaxResult.error("error",errorList);
        }

        return AjaxResult.success("数据导入成功",importList);
    }

    /**
     * 初始化导入头部、属性、校验规则
     */
    public List<ImportEntity> initList() {
        List<ImportEntity> boList = new ArrayList<ImportEntity>();
        // 校验规则 1 必填 2小数 3整数 4日期 5身份证 6年月 多个逗号分隔例如：1,2
        boList.add(new ImportEntity("车牌颜色","plateColor","1"));
        boList.add(new ImportEntity("车牌号","carNo","1"));
        boList.add(new ImportEntity("车型","carType","1"));
        boList.add(new ImportEntity("车种","carVehicle",""));
        boList.add(new ImportEntity("轴数","carNum","3"));
        boList.add(new ImportEntity("逃费类型","escapedType","1"));
        boList.add(new ImportEntity("逃费金额（元）","escapedAmount","2"));
        boList.add(new ImportEntity("备注","remark",""));
        return boList;
    }

}
