package com.ruoyi.web.controller.base;

import java.io.OutputStream;
import java.util.*;
import java.util.stream.Collectors;

import cn.afterturn.easypoi.excel.ExcelExportUtil;
import cn.afterturn.easypoi.excel.entity.TemplateExportParams;
import com.ruoyi.base.domain.OdsSzdnSection;
import com.ruoyi.base.domain.OdsSzdnToll;
import com.ruoyi.base.domain.OdsYhglVBaseOrg;
import com.ruoyi.base.service.IOdsSzdnTollService;
import com.ruoyi.base.service.IOdsYhglVBaseOrgService;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.utils.CommonUtil;
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
import com.ruoyi.base.domain.OdsSzdnGantry;
import com.ruoyi.base.service.IOdsSzdnGantryService;
import com.ruoyi.common.core.page.TableDataInfo;

import javax.servlet.http.HttpServletResponse;

/**
 * 门架信息Controller
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@RestController
@RequestMapping("/base/gantry")
public class OdsSzdnGantryController extends BaseController {

    @Autowired
    private IOdsSzdnGantryService odsSzdnGantryService;
    @Autowired
    private RedisCache redisCache;
    @Autowired
    private IOdsSzdnTollService tollService;
    @Autowired
    private IOdsYhglVBaseOrgService baseOrgService;

    /**
     * 查询门架信息列表
     */
    @GetMapping("/list")
    public TableDataInfo list(OdsSzdnGantry odsSzdnGantry) {
        startPage();
        // odsSzdnGantry.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<OdsSzdnGantry> list = odsSzdnGantryService.selectOdsSzdnGantryList(odsSzdnGantry);
        return getDataTable(list);
    }

    /**
     * 查询门架信息列表:选择门架弹窗
     */
    @GetMapping("/listAll")
    public TableDataInfo listAll(OdsSzdnGantry odsSzdnGantry) {
        startPage();
        List<OdsSzdnGantry> list = odsSzdnGantryService.selectOdsSzdnGantryList(odsSzdnGantry);
        return getDataTable(list);
    }


    /**
     * 导出门架信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:gantry:export')")
    @Log(title = "门架信息", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(OdsSzdnGantry odsSzdnGantry, HttpServletResponse response) {
        List<OdsSzdnGantry> list = new ArrayList<>();
        List obj = redisCache.getCacheObject(Constants.gantry_list);
        if (null != obj) {
            list = (List<OdsSzdnGantry>) obj;
        }
        if(!list.isEmpty()) {
            //过滤条件 boundary_gantry_type = '1', is_virtual = '0'
//            list = list.stream().filter(item -> "1".equals(item.getBoundaryGantryType()) && "0".equals(item.getIsVirtual())).collect(Collectors.toList());
            List<OdsSzdnSection> sectionList = redisCache.getCacheList(Constants.SECTION_LIST);
            Map<String, String> roadMap = sectionList.stream().collect(Collectors.toMap(OdsSzdnSection::getRoadCode, OdsSzdnSection::getRoadName, (k1, k2) -> k1));
            Map<String, String> sectionMap = sectionList.stream().collect(Collectors.toMap(OdsSzdnSection::getSectionCode, OdsSzdnSection::getSectionName, (k1, k2) -> k1));
            Map<String, String> tollMap = tollService.list().stream().collect(Collectors.toMap(OdsSzdnToll::getTollCode, OdsSzdnToll::getTollName));
            Map<String, String> orgMap = baseOrgService.list().stream().collect(Collectors.toMap(OdsYhglVBaseOrg::getOrgCode, OdsYhglVBaseOrg::getOrgName));
            for (OdsSzdnGantry gantry : list) {
                gantry.setRoadName(roadMap.getOrDefault(gantry.getRoadCode(), ""));
                gantry.setSectionName(sectionMap.getOrDefault(gantry.getSectionCode(), ""));
                gantry.setTollName(tollMap.getOrDefault(gantry.getTollCode(), ""));
                gantry.setOrgName(orgMap.getOrDefault(gantry.getOrgCode(), ""));
                gantry.setBoundaryGantryType("0".equals(gantry.getBoundaryGantryType()) ? "边界入口门架" : "边界出口门架");
                gantry.setIsVirtual("0".equals(gantry.getIsVirtual()) ? "否" : "是");
                gantry.setIsData("否");
                Object objNum = redisCache.getCacheObject(Constants.gantry_list_data + CommonUtil.isNull(gantry.getGantryCode()));
                if (null != objNum) {
                    Integer intCountNum = Integer.parseInt(objNum.toString());
                    if (intCountNum > 0){
                        gantry.setIsData("是");
                    }
                }
            }
            list = list.stream().sorted(Comparator.comparing(OdsSzdnGantry::getOrgCode).thenComparing(OdsSzdnGantry::getRoadCode).thenComparing(OdsSzdnGantry::getSectionCode)
                    .thenComparing(OdsSzdnGantry::getTollCode).thenComparing(OdsSzdnGantry::getGantryCode)).collect(Collectors.toList());
            Map<String, Object> map = new HashMap<>();
            map.put("entitylist", list);
            try {
                String url = "templates/export/gantry.xlsx";
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
        }
        return null;
    }

    /**
     * 获取门架信息详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(odsSzdnGantryService.selectOdsSzdnGantryById(id));
    }

    /**
     * 新增门架信息
     */
    @PreAuthorize("@ss.hasPermi('base:gantry:add')")
    @Log(title = "门架信息", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody OdsSzdnGantry odsSzdnGantry) {
        return odsSzdnGantryService.saveOdsSzdnGantry(odsSzdnGantry);
    }

    /**
     * 修改门架信息
     */
    @PreAuthorize("@ss.hasPermi('base:gantry:edit')")
    @Log(title = "门架信息", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody OdsSzdnGantry odsSzdnGantry) {
        return odsSzdnGantryService.saveOdsSzdnGantry(odsSzdnGantry);
    }

    /**
     * 删除门架信息
     */
    @PreAuthorize("@ss.hasPermi('base:gantry:remove')")
    @Log(title = "门架信息", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return odsSzdnGantryService.deleteOdsSzdnGantryByIds(ids);
    }

}
