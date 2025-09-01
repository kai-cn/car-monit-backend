package com.ruoyi.web.controller.base;

import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.ruoyi.base.domain.model.OdsLwzxsfsjFeeGantryFusion01Model;
import com.ruoyi.base.service.forest.HttpOdsLwzxsfsjFeeGantryFusion01Service;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.exception.ServiceException;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;

/**
 * 交易流水Controller
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@RestController
@RequestMapping("/base/feeGantry")
public class OdsLwzxsfsjFeeGantryFusion01Controller extends BaseController {

    @Resource
    private HttpOdsLwzxsfsjFeeGantryFusion01Service httpOdsLwzxsfsjFeeGantryFusion01Service;

    /**
     * 查询交易流水列表
     */
    @PreAuthorize("@ss.hasPermi('base:feeGantry:list')")
    @GetMapping("/list")
    public TableDataInfo list(OdsLwzxsfsjFeeGantryFusion01Model odsLwzxsfsjFeeGantryFusion01Model) {
        JSONObject jsonObject = httpOdsLwzxsfsjFeeGantryFusion01Service.getOdsLwzxsfsjFeeGantryFusion01Page(odsLwzxsfsjFeeGantryFusion01Model);
        if(null == jsonObject || 200 != jsonObject.getInt("code")){
            logger.error("门架抓拍交易流水数据获取异常：" + jsonObject);
            throw new ServiceException("获取数据异常,请联系管理员");
        }
        return JSONUtil.toBean(jsonObject, TableDataInfo.class);
    }

//    /**
//     * 导出交易流水列表
//     */
//    @PreAuthorize("@ss.hasPermi('manager:01:export')")
//    @Log(title = "交易流水", businessType = BusinessType.EXPORT)
//    @GetMapping("/export")
//    public AjaxResult export(OdsLwzxsfsjFeeGantryFusion01 odsLwzxsfsjFeeGantryFusion01) {
//        List<OdsLwzxsfsjFeeGantryFusion01> list = odsLwzxsfsjFeeGantryFusion01Service.selectOdsLwzxsfsjFeeGantryFusion01List(odsLwzxsfsjFeeGantryFusion01);
//        ExcelUtil<OdsLwzxsfsjFeeGantryFusion01> util = new ExcelUtil<OdsLwzxsfsjFeeGantryFusion01>(OdsLwzxsfsjFeeGantryFusion01.class);
//        return util.exportExcel(list, "交易流水数据");
//    }
}
