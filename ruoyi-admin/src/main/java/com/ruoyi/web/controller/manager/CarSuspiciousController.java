package com.ruoyi.web.controller.manager;

import cn.afterturn.easypoi.entity.ImageEntity;
import cn.afterturn.easypoi.excel.ExcelExportUtil;
import cn.afterturn.easypoi.excel.entity.TemplateExportParams;
import cn.afterturn.easypoi.word.WordExportUtil;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.file.ImageUtils;
import com.ruoyi.manager.domain.CarSuspicious;
import com.ruoyi.manager.domain.CarSuspiciousCheck;
import com.ruoyi.manager.service.ICarInfoService;
import com.ruoyi.manager.service.ICarSuspiciousCheckService;
import com.ruoyi.manager.service.ICarSuspiciousService;
import com.ruoyi.system.domain.SysFile;
import com.ruoyi.system.service.ISysDictDataService;
import com.ruoyi.system.service.ISysFileService;
import org.apache.poi.ss.usermodel.Workbook;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletResponse;
import java.io.OutputStream;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

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

    @Autowired
    private ICarSuspiciousCheckService carSuspiciousCheckService;

    @Autowired
    private ICarInfoService carInfoService;

    @Autowired
    private ISysFileService sysFileService;


    /**
     * 查询可疑车辆列表：菜单列表
     */
    @PreAuthorize("@ss.hasPermi('manager:suspicious:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarSuspicious carSuspicious) {
        startPage();

        //  路段
        String sectionCode = CommonUtil.deleteEnd(carSuspicious.getSectionCode());
        if (CommonUtil.isNotBlank(sectionCode)){
            if (sectionCode.indexOf(Constants.section_all) > -1) {
                carSuspicious.setSectionCode("");
            }
        }

        // 选择对象
        if (CommonUtil.isNotBlank(carSuspicious.getCode())){
            carSuspicious.setTrackNames(carSuspicious.getCode()); // 查询范围
        }

        // carSuspicious.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarSuspicious> list = carSuspiciousService.selectCarSuspiciousList(carSuspicious);
        return getDataTable(list);
    }



    /**
     * 查询可疑车辆列表：根据车牌号查询
     */
    @GetMapping("/listCarNo")
    public TableDataInfo listCarNo(CarSuspicious carSuspicious) {
        startPage();
        if (CommonUtil.isBlank(carSuspicious.getCarNo())){
            carSuspicious.setCarNo("-1");
        }
        List<CarSuspicious> list = carSuspiciousService.selectCarSuspiciousList(carSuspicious);
        return getDataTable(list);
    }


    /**
     * 查询可疑车辆列表：根据车牌号查询：查询证明材料
     */
    @GetMapping("/listFileCarNo")
    public TableDataInfo listFileCarNo(CarSuspicious carSuspicious) {
        startPage();
        if (CommonUtil.isBlank(carSuspicious.getCarNo())){
            carSuspicious.setCarNo("-1");
        }
        carSuspicious.setIsExcept("1");
        carSuspicious.setCheckStatus("1"); // 是可疑车俩并且
        List<CarSuspicious> list = carSuspiciousService.selectCarSuspiciousList(carSuspicious);
        List<CarSuspicious> rtnList = new ArrayList<>();
        // 逃费类型
        Map<String,String> escapedTypeMap = sysDictDataService.selectDictDataMap("escaped_type");
        for (CarSuspicious vo :list){
            CarSuspicious rtn = carSuspiciousService.selectCarSuspiciousById(vo.getId());
            if (rtn.getCheckList() != null){
                BigDecimal chargeAmount = new BigDecimal("0");
                BigDecimal totalAmount = new BigDecimal("0");
                BigDecimal difAmount = new BigDecimal("0");
                for (CarSuspiciousCheck check : rtn.getCheckList()) {
                    chargeAmount = chargeAmount.add(check.getChargeAmount());
                    totalAmount = totalAmount.add(check.getTotalAmount());
                    difAmount = difAmount.add(check.getDifAmount());
                }
                rtn.setChargeAmount(chargeAmount.toString());
                rtn.setTotalAmount(totalAmount.toString());
                rtn.setDifAmount(difAmount.toString());
                // 需要循环 : 逃费类型
                String bussName = "";
                String bussType = CommonUtil.deleteEnd(rtn.getEscapedType());
                if (CommonUtil.isNotBlank(bussType)) {
                    String[] bussTypeStr = bussType.split(",");
                    for (int i = 0; i < bussTypeStr.length; i++) {
                        if (escapedTypeMap.containsKey(bussTypeStr[i])) {
                            bussName = bussName + escapedTypeMap.get(bussTypeStr[i]) + ",";
                        }
                    }
                    rtn.setEscapedTypeName(bussName);
                }
            }
            rtnList.add(rtn);
        }
        return getDataTable(rtnList);
    }

    /**
     * 导出通行异常
     */
    @GetMapping("/exportAbnormalPassage")
    public void exportAbnormalPassage(String carSuspiciousId, HttpServletResponse response) {
        CarSuspicious carSuspicious = carSuspiciousService.getById(carSuspiciousId);

        CarSuspiciousCheck querybo = new CarSuspiciousCheck();
        querybo.setCarId(carSuspiciousId);
        List<CarSuspiciousCheck> checkList = carSuspiciousCheckService.selectCarSuspiciousCheckList(querybo);

        // 车牌颜色
        Map<String,String> plateColorMap = sysDictDataService.selectDictDataMap("plate_color");
        // 车型
        Map<String,String> carTypeMap = sysDictDataService.selectDictDataMap("car_type");
        // 车种
        Map<String,String> carVehicleMap = sysDictDataService.selectDictDataMap("car_vehicle");
        // 逃费类型
        Map<String,String> escapedTypeMap = sysDictDataService.selectDictDataMap("escaped_type");



        Map<String,Object> map = new HashMap<>();
        map.put("plateColor", carSuspicious.getPlateColor() == null ? "" : CommonUtil.isNull(plateColorMap.get(carSuspicious.getPlateColor())));
        map.put("carNo", CommonUtil.isNull(carSuspicious.getCarNo()));
        map.put("carType", carSuspicious.getCarType() == null ? "" : CommonUtil.isNull(carTypeMap.get(carSuspicious.getCarType())));
        String carVehicle = carSuspicious.getCarVehicle() == null ? "" : carVehicleMap.get(carSuspicious.getCarVehicle());
        map.put("carVehicle", carVehicle == null ? carSuspicious.getCarVehicle() : carVehicle);
        map.put("carNum", CommonUtil.isNull(carSuspicious.getCarNum()));
        map.put("inStation", CommonUtil.isNull(carSuspicious.getInStation()));
        map.put("inTime", CommonUtil.isNull(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS, carSuspicious.getInTime())));
        map.put("outstation", CommonUtil.isNull(carSuspicious.getOutStation()));
        map.put("outTime", CommonUtil.isNull(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS, carSuspicious.getOutTime())));
        map.put("gantrytStation", CommonUtil.isNull(carSuspicious.getGantrytStation()));
        map.put("gantryTime", CommonUtil.isNull(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS, carSuspicious.getGantryTime())));
        map.put("outGantrytStation", CommonUtil.isNull(carSuspicious.getOutGantrytStation()));
        map.put("outGantryTime", CommonUtil.isNull(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS, carSuspicious.getOutGantryTime())));

        // 需要循环 : 逃费类型
        String bussName = "";
        String bussType = CommonUtil.deleteEnd(carSuspicious.getEscapedType());
        if (CommonUtil.isNotBlank(bussType)) {
            String[] bussTypeStr = bussType.split(",");
            for (int i = 0; i < bussTypeStr.length; i++) {
                if (escapedTypeMap.containsKey(bussTypeStr[i])) {
                    bussName = bussName + escapedTypeMap.get(bussTypeStr[i]) + ",";
                }
            }
        }
        map.put("escapedType", CommonUtil.deleteEnd(bussName));
        if (checkList == null){
            map.put("chargeAmount", "");
            map.put("totalAmount", "");
            map.put("difAmount", "");
        }else {
            BigDecimal chargeAmount = new BigDecimal("0");
            BigDecimal totalAmount = new BigDecimal("0");
            BigDecimal difAmount = new BigDecimal("0");
            for (CarSuspiciousCheck check : checkList) {
                chargeAmount = chargeAmount.add(check.getChargeAmount());
                totalAmount = totalAmount.add(check.getTotalAmount());
                difAmount = difAmount.add(check.getDifAmount());
            }
            map.put("chargeAmount", chargeAmount.toString());
            map.put("totalAmount", totalAmount.toString());
            map.put("difAmount", difAmount.toString());
        }

        map.put("isExcept", "0".equals(carSuspicious.getIsExcept()) ? "无逃费" : "1".equals(carSuspicious.getIsExcept()) ? "确认逃费" : "");
        map.put("exceptRemark", CommonUtil.isNull(carSuspicious.getExceptRemark()));
        if (CommonUtil.isNotBlank(carSuspicious.getExceptFileIds())){
            List<SysFile> sysFiles = sysFileService.selectSysFileByIds(carSuspicious.getExceptFileIds());
            int i = 1;
            for (SysFile sysFile : sysFiles) {
                if (ImageUtils.isImage(sysFile.getType())){
                    byte[] byteObject = sysFileService.getByteObject(sysFile.getId());
                    ImageEntity image = new ImageEntity(byteObject, 250, 250);
                    //表格外添加简单图片
                    image.setType(ImageEntity.Data);
                    map.put("susImg" + i, image);
                    i++;
                }
            }
        }
        try {
            String url = "templates/export/carSuspicious.docx";
            XWPFDocument workbook = WordExportUtil.exportWord07(url, map);
            response.setContentType("application/octet-stream;charset=UTF-8");
            response.setHeader("Content-Disposition", "attachment");
            OutputStream outs = response.getOutputStream();
            workbook.write(outs);
            outs.flush();
            outs.close();
        } catch (Exception e) {
            e.printStackTrace();
        }
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

        //  路段
        String sectionCode = CommonUtil.deleteEnd(carSuspicious.getSectionCode());
        if (CommonUtil.isNotBlank(sectionCode)){
            if (sectionCode.indexOf(Constants.section_all) > -1) {
                carSuspicious.setSectionCode("");
            }
        }

        // 选择对象
        if (CommonUtil.isNotBlank(carSuspicious.getCode())){
            carSuspicious.setTrackNames(carSuspicious.getCode()); // 查询范围
        }

        List<CarSuspicious> list = carSuspiciousService.selectCarSuspiciousList(carSuspicious);
        // 车牌颜色
        Map<String,String> plateColorMap = sysDictDataService.selectDictDataMap("plate_color");
        // 车型
        Map<String,String> carTypeMap = sysDictDataService.selectDictDataMap("car_type");

        // 车种
        Map<String,String> carVehicleMap = sysDictDataService.selectDictDataMap("car_vehicle");

        // 逃费类型
        Map<String,String> escapedTypeMap = sysDictDataService.selectDictDataMap("escaped_type");

        Map<String,String> isExceptMap = sysDictDataService.selectDictDataMap("is_except");

        Map<String,String> checkStatusMap = sysDictDataService.selectDictDataMap("check_status");


        list.stream().forEach(dp -> {
            if (null != dp.getCreateTime()){
                dp.setCreateTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getCreateTime()));
            }
            dp.setPlateColor(CommonUtil.isNull(plateColorMap.get(dp.getPlateColor())));
            dp.setCarType(CommonUtil.isNull(carTypeMap.get(dp.getCarType())));
            dp.setCarVehicle(CommonUtil.isNull(carVehicleMap.get(dp.getCarVehicle())));
            dp.setEscapedType(CommonUtil.isNull(escapedTypeMap.get(dp.getEscapedType())));
            dp.setIsExcept(CommonUtil.isNull(isExceptMap.get(dp.getIsExcept())));
            dp.setCheckStatus(CommonUtil.isNull(checkStatusMap.get(dp.getCheckStatus())));
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


    /**
     * 可疑车辆核实
     */
//    @PreAuthorize("@ss.hasPermi('manager:suspicious:check')")
    @Log(title = "可疑车辆", businessType = BusinessType.UPDATE)
    @PutMapping("/check")
    public AjaxResult check(@RequestBody CarSuspicious carSuspicious) {
        return carSuspiciousService.cherkCarSuspicious(carSuspicious);
    }




}
