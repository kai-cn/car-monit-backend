package com.ruoyi.web.controller.base;

import com.ruoyi.base.domain.OdsSzdnSection;
import com.ruoyi.base.domain.OdsSzdnToll;
import com.ruoyi.base.service.IOdsSzdnTollService;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.poi.ExcelUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 收费站基础信息Controller
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@RestController
@RequestMapping("/base/toll")
public class OdsSzdnTollController extends BaseController {

    @Autowired
    private IOdsSzdnTollService odsSzdnTollService;

    @Autowired
    private RedisCache redisCache;

    /**
     * 查询收费站基础信息列表：菜单列表界面
     */
    @GetMapping("/list")
    public TableDataInfo list(OdsSzdnToll odsSzdnToll) {
        startPage();
        // odsSzdnToll.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户

        List<OdsSzdnSection> sectionList = redisCache.getCacheList(Constants.SECTION_LIST);
        Map<String, String> roadMap = sectionList.stream().collect(Collectors.toMap(OdsSzdnSection::getRoadCode, OdsSzdnSection::getRoadName, (k1, k2) -> k1));
        Map<String, String> sectionMap = sectionList.stream().collect(Collectors.toMap(OdsSzdnSection::getSectionCode, OdsSzdnSection::getSectionName, (k1, k2) -> k1));

        List<OdsSzdnToll> list = odsSzdnTollService.selectOdsSzdnTollList(odsSzdnToll);
        for (OdsSzdnToll OdsSzdnToll : list) {
            OdsSzdnToll.setSectionName(sectionMap.getOrDefault(OdsSzdnToll.getSectionCode(), ""));
        }
        return getDataTable(list);
    }



    /**
     * 查询收费站基础信息列表：弹出界面窗口
     */
    @GetMapping("/listAll")
    public TableDataInfo listAll(OdsSzdnToll odsSzdnToll) {
        startPage();
        List<OdsSzdnToll> list = odsSzdnTollService.selectOdsSzdnTollList(odsSzdnToll);
        return getDataTable(list);
    }

    /**
     * 导出收费站基础信息列表
     */
    @PreAuthorize("@ss.hasPermi('base:toll:export')")
    @Log(title = "收费站基础信息", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(OdsSzdnToll odsSzdnToll) {
        List<OdsSzdnToll> list = odsSzdnTollService.selectOdsSzdnTollList(odsSzdnToll);
        ExcelUtil<OdsSzdnToll> util = new ExcelUtil<OdsSzdnToll>(OdsSzdnToll.class);
        return util.exportExcel(list, "收费站基础信息数据");
    }

    /**
     * 获取收费站基础信息详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(odsSzdnTollService.selectOdsSzdnTollById(id));
    }

    /**
     * 新增收费站基础信息
     */
    @PreAuthorize("@ss.hasPermi('base:toll:add')")
    @Log(title = "收费站基础信息", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody OdsSzdnToll odsSzdnToll) {
        return odsSzdnTollService.saveOdsSzdnToll(odsSzdnToll);
    }

    /**
     * 修改收费站基础信息
     */
    @PreAuthorize("@ss.hasPermi('base:toll:edit')")
    @Log(title = "收费站基础信息", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody OdsSzdnToll odsSzdnToll) {
        return odsSzdnTollService.saveOdsSzdnToll(odsSzdnToll);
    }

    /**
     * 删除收费站基础信息
     */
    @PreAuthorize("@ss.hasPermi('base:toll:remove')")
    @Log(title = "收费站基础信息", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return odsSzdnTollService.deleteOdsSzdnTollByIds(ids);
    }

}
