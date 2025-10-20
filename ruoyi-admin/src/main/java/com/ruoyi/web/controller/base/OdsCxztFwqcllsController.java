package com.ruoyi.web.controller.base;

import java.util.List;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.OdsCxztFwqclls;
import com.ruoyi.base.service.IOdsCxztFwqcllsService;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 服务区车辆流水Controller
 *
 * @author ruoyi
 * @date 2025-10-20
 */
@RestController
@RequestMapping("/manager/fwqclls")
public class OdsCxztFwqcllsController extends BaseController {

    @Autowired
    private IOdsCxztFwqcllsService odsCxztFwqcllsService;

    /**
     * 查询服务区车辆流水列表
     */
    @PreAuthorize("@ss.hasPermi('manager:fwqclls:list')")
    @GetMapping("/list")
    public TableDataInfo list(OdsCxztFwqclls odsCxztFwqclls) {
        startPage();
        // odsCxztFwqclls.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<OdsCxztFwqclls> list = odsCxztFwqcllsService.selectOdsCxztFwqcllsList(odsCxztFwqclls);
        return getDataTable(list);
    }

    /**
     * 获取服务区车辆流水详细信息
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") Long bigId) {
        return AjaxResult.success(odsCxztFwqcllsService.selectOdsCxztFwqcllsById(bigId));
    }


}
