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

import javax.servlet.http.HttpServletResponse;
import java.io.OutputStream;
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



        list.stream().forEach(dp -> {
            if (null != dp.getCreateTime()){
                dp.setCreateTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getCreateTime()));
            }
            dp.setCarType(CommonUtil.isNull(carTypeMap.get(dp.getCarType())));
            dp.setCarVehicle(CommonUtil.isNull(carVehicleMap.get(dp.getCarVehicle())));
            dp.setEscapedType(CommonUtil.isNull(escapedTypeMap.get(dp.getEscapedType())));
            dp.setStatus(CommonUtil.isNull(statusMap.get(dp.getStatus())));
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

            // 通行标识
            Map<String,String> passTypeMap = sysDictDataService.selectDictDataLaleMap("run_type");

            // 逃费类型
            Map<String,String> escapedTypeMap = sysDictDataService.selectDictDataLaleMap("escaped_type");


            for (int i = 0; i < importList.size(); i++) {
                CarExceptRecord addbo = importList.get(i);

                String carNo = CommonUtil.isNull(addbo.getCarNo());
                if (CommonUtil.isNotBlank(carNo)){
                    if (carMap.containsKey(carNo)) {
                        CarInfo carInfo = carMap.get(carNo);
                        addbo.setCarId(carInfo.getId());
                        addbo.setCarType(carInfo.getCarType());
                        addbo.setCarVehicle(carInfo.getCarVehicle());
                        addbo.setCarNum(carInfo.getCarNum());
                    } else {
                        errorList.add(importUtil.getErrorBO(i + 1, "车牌号", carNo + " 车牌号在重点车辆库不存在！"));
                    }
                }

                // 通行标识
                String passType =  CommonUtil.isNull(addbo.getPassType());
                if (CommonUtil.isNotBlank(passType)){
                    if (passTypeMap.containsKey(passType)) {
                        addbo.setPassType(CommonUtil.isNull(passTypeMap.get(passType)));
                    } else {
                        errorList.add(importUtil.getErrorBO(i + 1, "通行标识", passType + " 通行标识不存在,请在字典菜单维护！"));
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
                    addbo.setInStationId(tollMap.get(inStation));
                }

                // 出口
                String outStation = CommonUtil.isNull(addbo.getOutStation());
                if (CommonUtil.isNotBlank(outStation)){
                    addbo.setOutStationId(tollMap.get(outStation));
                }


                if (errorList.size() > 100){
                    break;
                }
            }

        }

        // 插入数据库
        if (errorList.size() == 0) {
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
     * 初始化导入头部、属性、校验规则
     */
    public List<ImportEntity> initList() {
        List<ImportEntity> boList = new ArrayList<ImportEntity>();
        // 校验规则 1 必填 2小数 3整数 4日期 5身份证 6年月 多个逗号分隔例如：1,2
        boList.add(new ImportEntity("车牌号","carNo","1"));
        boList.add(new ImportEntity("通行标识","passType",""));
        boList.add(new ImportEntity("入口站","inStation",""));
        boList.add(new ImportEntity("入口时间","inTime","1,8"));
        boList.add(new ImportEntity("出口站","outStation",""));
        boList.add(new ImportEntity("出口时间","outTime","1,8"));
        boList.add(new ImportEntity("应缴金额（元）","totalAmount","1,2"));
        boList.add(new ImportEntity("收费金额（元）","chargeAmount","1,2"));
        boList.add(new ImportEntity("逃费类型","escapedType","1"));
        boList.add(new ImportEntity("备注","remark",""));
        return boList;
    }


}
