package com.ruoyi.web.controller.base;

import com.alibaba.fastjson2.JSONObject;
import com.ruoyi.base.domain.Geometry;
import com.ruoyi.base.service.IGeometryService;
import com.ruoyi.base.service.IHenDaService;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.poi.ExcelUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * 车辆信息Controller
 *
 * @author ruoyi
 * @date 2025-09-27
 */
@RestController
@RequestMapping("/base/geometry")
public class GeometryController extends BaseController {

    @Autowired
    private IGeometryService geometryService;

    @Autowired
    private IHenDaService henDaService;

    @Resource
    ThreadPoolTaskExecutor executor;

    /**
     * henDa查询路线经纬度
     */
    @PreAuthorize("@ss.hasPermi('base:geometry:list')")
    @GetMapping("/getHenDa")
    public AjaxResult getHenDa(Geometry geometry) {
        JSONObject pileToLonLat = henDaService.getPileToLonLat(geometry.getLxbh(), geometry.getZhStr(), geometry.getLxfx());
        return AjaxResult.success(pileToLonLat);
    }

    /**
     * 同步所有路线经纬度，首次请求先清空geometry表数据，后续重复请求不需要清空
     * 跑到一半hengda接口批量超时，重启项目重新请求继续跑
     * G4521一条数据都查不到，沿用老数据
     */
    @GetMapping("/syncAllGeometry")
    public AjaxResult syncAllGeometry() {
        List<Geometry> list = geometryService.syncAllGeometry();
        syncGeometry(list);
        return AjaxResult.success();
    }

    /**
     * 手动补齐路线经纬度
     * 有些路线桩号间会隔断，需要手动查询下一个有经纬度的桩号，传入参数手动补齐
     * 同一个路线编号、方向、起点桩号不要重复请求，否则会插入一模一样的数据
     * 根据传入的路线编号、方向、起点桩号向上补齐经纬度
     */
    @GetMapping("/syncAllGeometry1")
    public AjaxResult syncAllGeometry1(Geometry geometry) {
        List<Geometry> list = new ArrayList<>();
        list.add(geometry);
        syncGeometry(list);
        return AjaxResult.success();
    }

    public void syncGeometry(List<Geometry> list){
        for (Geometry geometry : list) {
            executor.execute(() -> {
                Integer qdzh = geometry.getQdzh();
                List<double[]> doubleList = new ArrayList<>();
                int count = 10;
                int i = 0;
                // 10个桩号有7个以上经纬度就继续跑下一截
                while (count >= 7){
                    String zh;
                    if (i < 10){
                        zh = qdzh + "." + i;
                    }else {
                        zh = String.valueOf(qdzh + 1);
                    }
                    JSONObject jsonObject = henDaService.getPileToLonLat(geometry.getLxbh(), zh, geometry.getLxfx());
                    if (jsonObject != null){
                        doubleList.add(new double[]{jsonObject.getDoubleValue("longitude"), jsonObject.getDoubleValue("latitude")});
                    }
                    if (i == 10){
                        count = doubleList.size();
                        // 10个桩号有5个以上经纬度才入库
                        if (doubleList.size() >= 5){
                            double[][] doubles = new double[doubleList.size()][2];
                            for (int j = 0; j < doubleList.size(); j++) {
                                doubles[j] = doubleList.get(j);
                            }
                            Geometry save = new Geometry(geometry.getLxbh(), geometry.getLxfx(), qdzh, qdzh+1, Arrays.deepToString(doubles));
                            geometryService.save(save);
                        }
                        doubleList = new ArrayList<>();
                        qdzh ++;
                        i = 0;
                    }else {
                        i++;
                    }
                }
            });
        }
    }




    /**
     * 查询车辆信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:geometry:list')")
    @GetMapping("/list")
    public TableDataInfo list(Geometry geometry) {
        startPage();
        // geometry.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<Geometry> list = geometryService.selectGeometryList(geometry);
        return getDataTable(list);
    }

    /**
     * 导出车辆信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:geometry:export')")
    @Log(title = "车辆信息", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(Geometry geometry) {
        List<Geometry> list = geometryService.selectGeometryList(geometry);
        ExcelUtil<Geometry> util = new ExcelUtil<Geometry>(Geometry.class);
        return util.exportExcel(list, "车辆信息数据");
    }

    /**
     * 获取车辆信息详细信息
     */
    @GetMapping(value = "/{ID}")
    public AjaxResult getInfo(@PathVariable("ID") Integer ID) {
        return AjaxResult.success(geometryService.selectGeometryById(ID));
    }

    /**
     * 新增车辆信息
     */
    @PreAuthorize("@ss.hasPermi('base:geometry:add')")
    @Log(title = "车辆信息", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody Geometry geometry) {
        return geometryService.saveGeometry(geometry);
    }

    /**
     * 修改车辆信息
     */
    @PreAuthorize("@ss.hasPermi('base:geometry:edit')")
    @Log(title = "车辆信息", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody Geometry geometry) {
        return geometryService.saveGeometry(geometry);
    }

    /**
     * 删除车辆信息
     */
    @PreAuthorize("@ss.hasPermi('base:geometry:remove')")
    @Log(title = "车辆信息", businessType = BusinessType.DELETE)
    @DeleteMapping("/{IDs}")
    public AjaxResult remove(@PathVariable Integer[] IDs) {
        return geometryService.deleteGeometryByIds(IDs);
    }

}
