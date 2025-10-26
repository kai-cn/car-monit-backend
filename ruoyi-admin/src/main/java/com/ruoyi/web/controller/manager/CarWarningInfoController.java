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
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.stream.Collectors;

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

        String flag = "";
        if (CommonUtil.isNotBlank(carWarningInfo.getQueryRante())){
            flag = carWarningInfo.getQueryRante();
        }
        if (CommonUtil.isBlank(flag)){
            flag = "curDate"; // 默认查询当天并且车辆为
        }
        carWarningInfo.setFlag(flag);

        // 设置时间
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd");
        String formattedDate = sdf.format(new Date());
        if (flag.equals("curDate")){
            carWarningInfo.setFlagTime(formattedDate);
        }else  if (flag.equals("histhory")){
            carWarningInfo.setFlagTime(formattedDate);
        }


        String sectionCode = CommonUtil.deleteEnd(carWarningInfo.getSectionCode());
        if (CommonUtil.isNotBlank(sectionCode)){
            // 路段
            carWarningInfo.setSectionCodeList(Arrays.stream(sectionCode.split(",")).collect(Collectors.toList()));
            carWarningInfo.setSectionCode(""); // 查询范围
        }

        String code = CommonUtil.deleteEnd(carWarningInfo.getCode());
        if (CommonUtil.isNotBlank(code)){
            // 服务区 收费站
            carWarningInfo.setCodeList(Arrays.stream(code.split(",")).collect(Collectors.toList()));
            carWarningInfo.setCode(""); // 查询范围
        }

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

        // 车牌颜色
        Map<String,String> plateColorMap = sysDictDataService.selectDictDataMap("plate_color");

        // 车型
        Map<String,String> carTypeMap = sysDictDataService.selectDictDataMap("car_type");
        // 车种
        Map<String,String> carVehicleMap = sysDictDataService.selectDictDataMap("car_vehicle");
        // 逃费类型
        Map<String,String> escapedTypeMap = sysDictDataService.selectDictDataMap("escaped_type");

        String flag = "";
        if (CommonUtil.isNotBlank(carWarningInfo.getQueryRante())){
            flag = carWarningInfo.getQueryRante();
        }
        if (CommonUtil.isBlank(flag)){
            flag = "curDate"; // 默认查询当天并且车辆为
        }
        carWarningInfo.setFlag(flag);

        // 设置时间
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd");
        String formattedDate = sdf.format(new Date());
        if (flag.equals("curDate")){
            carWarningInfo.setFlagTime(formattedDate);
        }else  if (flag.equals("histhory")){
            carWarningInfo.setFlagTime(formattedDate);
        }


        carWarningInfo.setTrackNames(carWarningInfo.getCode()); // 查询范围

        List<CarWarningInfo> list = carWarningInfoService.selectCarWarningInfoList(carWarningInfo);


        list.stream().forEach(dp -> {
            if (null != dp.getGantryTime()){
                dp.setGantryTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getGantryTime()));
            }
            if (null != dp.getCreateTime()){
                dp.setCreateTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getCreateTime()));
            }

            if (null != dp.getInTime()){
                dp.setInTimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS,dp.getInTime()));
            }

            dp.setPlateColor(CommonUtil.isNull(plateColorMap.get(dp.getPlateColor())));

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
