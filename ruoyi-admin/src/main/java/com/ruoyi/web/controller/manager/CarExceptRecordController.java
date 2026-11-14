package com.ruoyi.web.controller.manager;

import cn.afterturn.easypoi.excel.ExcelExportUtil;
import cn.afterturn.easypoi.excel.entity.TemplateExportParams;
import com.ruoyi.base.domain.OdsSzdnToll;
import com.ruoyi.base.service.IOdsSzdnTollService;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.manager.domain.CarExceptRecord;
import com.ruoyi.manager.domain.CarInfo;
import com.ruoyi.manager.service.ICarExceptRecordService;
import com.ruoyi.manager.service.ICarInfoService;
import com.ruoyi.system.service.ISysDictDataService;
import com.ruoyi.web.util.ImportEntity;
import com.ruoyi.web.util.ImportErrorEntity;
import com.ruoyi.web.util.ImportSysUtil;
import com.ruoyi.web.util.ImportUtil;
import org.apache.poi.ss.usermodel.Workbook;
import org.apache.poi.xssf.usermodel.XSSFSheet;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import jakarta.servlet.http.HttpServletResponse;
import java.io.OutputStream;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

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

    @Autowired
    private ICarInfoService carInfoService;

    @Autowired
    private IOdsSzdnTollService odsSzdnTollService;

    private static final Integer[] strNum  = {0,11,12,14,15,17,18,19,21};
    private static final String[] strName  = {"序号","出口收费站","出口时间","通行PASSID","车牌","交易车型","车种","入口站","入口时间","一级类型","二级类型","省内","省外","小计","省内","省外","小计","省内","省外","小计","备注",""};
    /**
     * 查询异常车辆流水列表
     */
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
     * 根据车牌号查询: 根据单位
     * @param carExceptRecord
     * @return
     */
    @GetMapping("/listCarOrgId")
    public TableDataInfo listCarOrgId(CarExceptRecord carExceptRecord) {
        startPage();
        if (null == carExceptRecord.getEpsId()){
            carExceptRecord.setEpsId(-1L);
        }
        List<CarExceptRecord> list = carExceptRecordService.selectCarExceptRecordListNew(carExceptRecord);


        return getDataTable(list);
    }

    /**
     * 导出异常车辆流水列表
     */
    @Log(title = "异常车辆流水", businessType = BusinessType.EXPORT)
    @GetMapping("/exportOrgId")
    public AjaxResult exportOrgId(CarExceptRecord carExceptRecord, HttpServletResponse response) {

        if (null == carExceptRecord.getEpsId()){
            carExceptRecord.setEpsId(-1L);
        }
        List<CarExceptRecord> list = carExceptRecordService.selectCarExceptRecordListNew(carExceptRecord);
        // 车型
        Map<String,String> carTypeMap = sysDictDataService.selectDictDataMap("car_type");

        // 车种
        Map<String,String> carVehicleMap = sysDictDataService.selectDictDataMap("car_vehicle");

        // 逃费类型
        Map<String,String> escapedTypeMap = sysDictDataService.selectDictDataMap("escaped_type");

        // 补缴状态
        Map<String,String> statusMap = sysDictDataService.selectDictDataMap("supplementary_status");


        for (int i = 0; i < list.size(); i++) {
            CarExceptRecord dp = list.get(i);

            if (null != dp.getCreateTime()){
                dp.setCreateTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getCreateTime()));
            }


            if (null != dp.getCreateTime()){
                dp.setCreateTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getCreateTime()));
            }

            if (null != dp.getInTime()){
                dp.setInTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getInTime()));
            }

            if (null != dp.getOutTime()){
                dp.setOutTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getOutTime()));
            }

            if(carTypeMap.containsKey(dp.getCarType())){
                dp.setCarType(CommonUtil.isNull(carTypeMap.get(dp.getCarType())));
            }

            if(carVehicleMap.containsKey(dp.getCarVehicle())){
                dp.setCarVehicle(CommonUtil.isNull(carVehicleMap.get(dp.getCarVehicle())));
            }

            if(escapedTypeMap.containsKey(dp.getEscapedType())){
                dp.setEscapedType(CommonUtil.isNull(escapedTypeMap.get(dp.getEscapedType())));
            }

            dp.setStatus(CommonUtil.isNull(statusMap.get(dp.getStatus())));
            dp.setSort(i+1);
            dp.setCarNoQuery("");
        }





        Map<String,Object> map = new HashMap<>();
        map.put("entitylist",list);
        try {
            String url = "templates/export/exportCarExcept.xlsx";
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
     * 根据车牌号查询: 根据车牌号查询
     * @param carExceptRecord
     * @return
     */
    @GetMapping("/listExceptId")
    public TableDataInfo listExceptId(CarExceptRecord carExceptRecord) {
        startPage();
        if (CommonUtil.isBlank(carExceptRecord.getExceptIds())){
            carExceptRecord.setExceptIds("-1");
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

        // 补缴状态
        Map<String,String> statusMap = sysDictDataService.selectDictDataMap("supplementary_status");


        for (int i = 0; i < list.size(); i++) {
            CarExceptRecord dp = list.get(i);

            if (null != dp.getCreateTime()){
                dp.setCreateTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getCreateTime()));
            }


            if (null != dp.getCreateTime()){
                dp.setCreateTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getCreateTime()));
            }

            if (null != dp.getInTime()){
                dp.setInTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getInTime()));
            }

            if (null != dp.getOutTime()){
                dp.setOutTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getOutTime()));
            }

            if(carTypeMap.containsKey(dp.getCarType())){
                dp.setCarType(CommonUtil.isNull(carTypeMap.get(dp.getCarType())));
            }

            if(carVehicleMap.containsKey(dp.getCarVehicle())){
                dp.setCarVehicle(CommonUtil.isNull(carVehicleMap.get(dp.getCarVehicle())));
            }

            if(escapedTypeMap.containsKey(dp.getEscapedType())){
                dp.setEscapedType(CommonUtil.isNull(escapedTypeMap.get(dp.getEscapedType())));
            }

            dp.setStatus(CommonUtil.isNull(statusMap.get(dp.getStatus())));
            dp.setSort(i+1);
            dp.setCarNoQuery("");
        }





        Map<String,Object> map = new HashMap<>();
        map.put("entitylist",list);
        try {
            String url = "templates/export/exportCarExcept.xlsx";
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

    /**
     * 获取confirmId
     */
    @GetMapping(value = "/getConfirmId/{id}")
    public AjaxResult getConfirmId(@PathVariable("id") String id) {
        AjaxResult success = AjaxResult.success();
        success.put("data", carExceptRecordService.getConfirmId(id));
        return success;
    }

    @Log(title = "新增流水导入", businessType = BusinessType.IMPORT)
    @PostMapping("/import")
    public AjaxResult doImport(@RequestParam("file") MultipartFile file) throws Exception {
        // 校验文件格式
        String fileName = file.getOriginalFilename();
        if (fileName.lastIndexOf(".xlsx") == -1) {
            return AjaxResult.error("请上传Excel文件(.xlsx)");
        }
        ImportSysUtil importUtil = new ImportSysUtil();
        XSSFSheet sheet = importUtil.getXSSFSheet(file.getInputStream(), 0); // 得到sheet页
        
        // 获取第二列头部
        List<ImportEntity> gzList = initListTwo();
        String[] colsName =  new String[gzList.size()];
        for (int i = 0; i < gzList.size(); i++) {
            colsName[i] = gzList.get(i).getColName();
        }
        
        // 获取第三列头部
        List<ImportEntity> gzListThree = initListTwo();
        String[] colsNameThree =  new String[gzListThree.size()];
        for (int i = 0; i < gzListThree.size(); i++) {
            colsNameThree[i] = gzListThree.get(i).getColName();
        }
        // 校验头部
        if (!importUtil.colVdaExcel08(sheet, colsName,1) && !importUtil.colVdaExcel08(sheet, colsNameThree,2)) {
            return AjaxResult.error("导入失败,模板不正确,请下载对应的模板！");
        }
        // 校验数据
        List<String[]> sheetList = importUtil.dataRtnExcel08(sheet, strName,strNum,3); // 返回结果集
        if (sheetList.size() == 0) {
            return AjaxResult.error("导入失败,模板excel没有数据可以导入，请确定！");
        }
        // 校验数据格式
        List<ImportErrorEntity> errorList = new ArrayList<ImportErrorEntity>(); // 错误列表
        List<CarExceptRecord> importList = new ArrayList<CarExceptRecord>(); // 导入的数据
        for (int i = 0; i < sheetList.size(); i++) {
            String[] strs = sheetList.get(i);
            Object rtnObj = ImportUtil.importExcel(errorList, gzList, i, strs, CarExceptRecord.class); // 结果集转对象
            if (errorList.size() == 0 && null != rtnObj) {
                CarExceptRecord importbo = (CarExceptRecord) rtnObj;
                importList.add(importbo);
            }

            if (errorList.size() > 100){
                break;
            }
        }


        // 新增车辆
        List<CarInfo> addlist = new ArrayList<>();
        Map<String,String> addCarMap = new HashMap<>();


        // 校验数据
        if (errorList.size() == 0) {

            // 查询终点车辆
            List<CarInfo> carList = carInfoService.selectCarInfoList(new CarInfo());
            Map<String, CarInfo> carMap = new HashMap<>();
            for (CarInfo carRtn : carList) {
                carMap.put(CommonUtil.isNull(carRtn.getCarNo()),carRtn);
            }

            // 查询收费站
            List<OdsSzdnToll> tolllist = odsSzdnTollService.selectOdsSzdnTollListNew(new OdsSzdnToll());
            Map<String, String> tollMap = new HashMap<>();
            for (OdsSzdnToll tollRtn : tolllist) {
                tollMap.put(CommonUtil.isNull(tollRtn.getTollName()),CommonUtil.isNull(tollRtn.getTollCode()));
            }

            // 车型
            Map<String,String> carTypeMap = sysDictDataService.selectDictDataLaleMap("car_type_change");

            // 车种
            // Map<String,String> carVehicleMap = sysDictDataService.selectDictDataLaleMap("car_vehicle");
            
            // 逃费类型
            Map<String,String> escapedTypeMap = sysDictDataService.selectDictDataLaleMap("escaped_type");

            // 车牌颜色
            Map<String,String> plateColorMap = sysDictDataService.selectDictDataLaleMap("plate_color");


            for (int i = 0; i < importList.size(); i++) {
                CarExceptRecord addbo = importList.get(i);


                // 车型
                String carType =  CommonUtil.isNull(addbo.getCarType());
                if (CommonUtil.isNotBlank(carType)){
                    if (carTypeMap.containsKey(carType)) {
                        addbo.setCarType(CommonUtil.isNull(carTypeMap.get(carType)));
                    }
                }

                String carTypeName = CommonUtil.isNull(addbo.getCarType());
                String carVehicle = "";
                if (carTypeName.equals("1")){
                    carVehicle = "1";
                }else if (carTypeName.equals("2")){
                    carVehicle = "1";
                } else if (carTypeName.equals("3")){
                    carVehicle = "1";
                }else if (carTypeName.equals("4")){
                    carVehicle = "1";
                }else if (carTypeName.equals("11")){
                    carVehicle = "2";
                }else if (carTypeName.equals("12")){
                    carVehicle = "2";
                } else if (carTypeName.equals("13")){
                    carVehicle = "2";
                }else if (carTypeName.equals("14")){
                    carVehicle = "2";
                }else if (carTypeName.equals("15")){
                    carVehicle = "2";
                } else if (carTypeName.equals("16")) {
                    carVehicle = "2";
                }else if (carTypeName.equals("21")) {
                    carVehicle = "3";
                }else if (carTypeName.equals("22")) {
                    carVehicle = "3";
                }else if (carTypeName.equals("23")) {
                    carVehicle = "3";
                }else if (carTypeName.equals("24")) {
                    carVehicle = "3";
                }else if (carTypeName.equals("25")) {
                    carVehicle = "3";
                }else if (carTypeName.equals("26")) {
                    carVehicle = "3";
                }else {
                    carVehicle = "99";
                }

                // 车种
               /* String carVehicle =  CommonUtil.isNull(addbo.getCarVehicle());
                if (CommonUtil.isNotBlank(carVehicle)){
                    if (carVehicleMap.containsKey(carVehicle)) {
                        addbo.setCarVehicle(CommonUtil.isNull(carVehicleMap.get(carVehicle)));
                    }
                }*/

                // 车种
                if (CommonUtil.isNotBlank(carVehicle)){
                    addbo.setCarVehicle(CommonUtil.isNull(carVehicle));
                }



                //车牌号、颜色处理
                String carNo = CommonUtil.isNull(addbo.getCarNo());
                String  plateColor = "";
                if (carNo.indexOf("_") > -1) {
                    String[] vehicleplateStr = carNo.split("_");
                    if (vehicleplateStr.length > 1){
                        plateColor = vehicleplateStr[1];
                    }
                    carNo = vehicleplateStr[0];
                }
                addbo.setCarNo(carNo);

                // 车牌颜色
                if (CommonUtil.isNotBlank(plateColor)){
                    if (plateColorMap.containsKey(plateColor)) {
                        plateColor = CommonUtil.isNull(plateColorMap.get(plateColor));
                    }
                }

                if (CommonUtil.isNotBlank(carNo)){
                    if (carMap.containsKey(carNo)) {
                        CarInfo carInfo = carMap.get(carNo);
                        addbo.setCarId(carInfo.getId());

                       /* if (CommonUtil.isBlank(addbo.getCarType())){
                            addbo.setCarType(carInfo.getCarType());
                        }

                        if (CommonUtil.isBlank(addbo.getCarVehicle())){
                            addbo.setCarVehicle(carInfo.getCarVehicle());
                        }*/

                        addbo.setCarNum(carInfo.getCarNum());
                    } else {
                       //  errorList.add(importUtil.getErrorBO(i + 1, "车牌号", carNo + " 车牌号在重点车辆库不存在！"));
                        if (addCarMap.containsKey(carNo)){
                        }else{
                            CarInfo addCarInfo = new CarInfo();
                            addCarInfo.setCarNo(carNo);
                            addCarInfo.setPlateColor(plateColor);
                            addCarInfo.setCarType(addbo.getCarType());
                            addCarInfo.setCarVehicle(addbo.getCarVehicle());
                            addlist.add(addCarInfo);
                            addCarMap.put(carNo,carNo);
                        }
                    }
                }
 
                // 逃费类型
                String escapedType = CommonUtil.isNull(addbo.getEscapedType());
                if (CommonUtil.isNotBlank(escapedType)){
                    if (escapedTypeMap.containsKey(escapedType)) {
                        addbo.setEscapedType(CommonUtil.isNull(escapedTypeMap.get(escapedType)));
                    } else {
                        errorList.add(importUtil.getErrorBO(i + 1, "逃费类型", escapedType + " 逃费类型不存在,请在字典菜单维护！"));
                    }
                }

                // 入口
                String inStation = CommonUtil.isNull(addbo.getInStation());
                if (CommonUtil.isNotBlank(inStation)){
                    if (tollMap.containsKey(inStation)) {
                        addbo.setInStation(CommonUtil.isNull(inStation));
                        addbo.setInStationId(CommonUtil.isNull(tollMap.get(inStation)));
                        
                    }
                }

                // 出口
                String outStation = CommonUtil.isNull(addbo.getOutStation());
                if (CommonUtil.isNotBlank(outStation)){
                    if (tollMap.containsKey(outStation)) {
                        addbo.setOutStation(CommonUtil.isNull(outStation));
                        addbo.setOutStationId(CommonUtil.isNull(tollMap.get(outStation)));
                    }
                }
                
                if (null != addbo.getTotalAmount() && null !=addbo.getChargeAmount()){
                    // 判断getTotalAmount>getChargeAmount
                    if(addbo.getTotalAmount().compareTo(addbo.getChargeAmount()) < 0){
                        errorList.add(importUtil.getErrorBO(i + 1, "缴费金额",  "收费金额不能大于应缴金额"));
                    }
                }
                
                // 时间验证
                if (null != addbo.getInTime() && null !=addbo.getOutTime()){
                    // 验证时间
                    if(addbo.getInTime().after(addbo.getOutTime())){
                        errorList.add(importUtil.getErrorBO(i + 1, "时间",  "入口时间大于出口时间，请确认!"));
                    }
                }

                if (errorList.size() > 100){
                    break;
                }
            }

        }

        // 插入数据库
        if (errorList.size() == 0) {
            // 新新增车辆--------------
            if(addlist.size() > 0){
                for (CarInfo addCar:addlist){
                    carInfoService.saveCarInfo(addCar);
                }
            }


            for (int i = 0; i < importList.size(); i++) {
                CarExceptRecord addbo = importList.get(i);
                if (null != addbo.getTotalAmount() && null !=addbo.getChargeAmount()){
                    addbo.setDifAmount(addbo.getTotalAmount().subtract(addbo.getChargeAmount()));
                }
                // 根据车牌号和入口时间
                CarExceptRecord querybo = new CarExceptRecord();
                querybo.setCarNo(CommonUtil.isNull(addbo.getCarNo()));
                querybo.setInTime(addbo.getInTime());
                List<CarExceptRecord> queryList = carExceptRecordService.selectCarExceptRecordList(querybo);
                if (queryList.size() > 0) {
                    addbo.setId(queryList.get(0).getId());
                }
                carExceptRecordService.saveCarExceptRecord(addbo);

            }

        }

        // 错误提示
        if (errorList.size() > 0) {
            return AjaxResult.error("error",errorList);
        }

        return AjaxResult.success("数据导入成功",importList);
    }

    /**
     * 初始化导入头部、属性、校验规则第二列
     */
    public List<ImportEntity> initListTwo() {
        List<ImportEntity> boList = new ArrayList<ImportEntity>();
        // 校验规则 1 必填 2小数 3整数 4日期 5身份证 6年月 多个逗号分隔例如：1,2
        boList.add(new ImportEntity("序号","",""));
        boList.add(new ImportEntity("出口收费站","outStation",""));
        boList.add(new ImportEntity("出口时间","outTime","1,8"));
        boList.add(new ImportEntity("通行PASSID","passType",""));
        boList.add(new ImportEntity("车牌","carNo","1"));
        
        boList.add(new ImportEntity("交易车型","carType",""));
        boList.add(new ImportEntity("车种","carVehicle",""));
        
        boList.add(new ImportEntity("入口站","inStation",""));
        boList.add(new ImportEntity("入口时间","inTime","1,8"));
        boList.add(new ImportEntity("漏交通行费类型","backCol1",""));
        boList.add(new ImportEntity("","escapedType","1"));
        
        boList.add(new ImportEntity("交易金额","",""));
        boList.add(new ImportEntity("","",""));
        boList.add(new ImportEntity("","chargeAmount","1,2"));
        
        boList.add(new ImportEntity("应交金额","",""));
        boList.add(new ImportEntity("","",""));
        boList.add(new ImportEntity("","totalAmount","1,2"));
        
        boList.add(new ImportEntity("实际追交金额","",""));
        boList.add(new ImportEntity("","",""));
        boList.add(new ImportEntity("","",""));

        boList.add(new ImportEntity("备注","remark",""));
        return boList;
    }
    /**
     * 初始化导入头部、属性、校验规则第三列
     */
    public List<ImportEntity> initListThree() {
        List<ImportEntity> boList = new ArrayList<ImportEntity>();
        // 校验规则 1 必填 2小数 3整数 4日期 5身份证 6年月 多个逗号分隔例如：1,2
        boList.add(new ImportEntity("","",""));
        boList.add(new ImportEntity("","outStation",""));
        boList.add(new ImportEntity("","outTime","1,8"));
        boList.add(new ImportEntity("","passType",""));
        boList.add(new ImportEntity("","carNo","1"));
        
        boList.add(new ImportEntity("","",""));
        boList.add(new ImportEntity("","",""));
        
        boList.add(new ImportEntity("","inStation",""));
        boList.add(new ImportEntity("","inTime","1,8"));
        boList.add(new ImportEntity("一级类型","backCol1",""));
        boList.add(new ImportEntity("二级类型","escapedType","1"));
        
        boList.add(new ImportEntity("省内","",""));
        boList.add(new ImportEntity("省外","",""));
        boList.add(new ImportEntity("小计","chargeAmount","1,2"));
        
        boList.add(new ImportEntity("省内","",""));
        boList.add(new ImportEntity("省外","",""));
        boList.add(new ImportEntity("小计","totalAmount","1,2"));
        
        boList.add(new ImportEntity("省内","",""));
        boList.add(new ImportEntity("省外","",""));
        boList.add(new ImportEntity("小计","","1,2"));
        
        boList.add(new ImportEntity("","remark",""));
        return boList;
    }


}
