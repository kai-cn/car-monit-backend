package com.ruoyi.base.service;

import com.ruoyi.base.domain.OdsLwzxsfsjFeeGantryFusion01;
import com.ruoyi.common.core.domain.AjaxResult;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 交易流水Service接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
public interface IOdsLwzxsfsjFeeGantryFusion01Service extends IService<OdsLwzxsfsjFeeGantryFusion01> {
    /**
     * 查询交易流水
     *
     * @param bigId 交易流水ID
     * @return 交易流水
     */
    OdsLwzxsfsjFeeGantryFusion01 selectOdsLwzxsfsjFeeGantryFusion01ById(String bigId);

    /**
     * 查询交易流水列表
     *
     * @param odsLwzxsfsjFeeGantryFusion01 交易流水
     * @return 交易流水集合
     */
    List<OdsLwzxsfsjFeeGantryFusion01> selectOdsLwzxsfsjFeeGantryFusion01List(OdsLwzxsfsjFeeGantryFusion01 odsLwzxsfsjFeeGantryFusion01);


    /**
     * 新增或者修改交易流水
     *
     * @param odsLwzxsfsjFeeGantryFusion01 交易流水
     * @return 结果
     */
    AjaxResult saveOdsLwzxsfsjFeeGantryFusion01(OdsLwzxsfsjFeeGantryFusion01 odsLwzxsfsjFeeGantryFusion01);

    /**
     * 批量删除交易流水
     *
     * @param bigIds 需要删除的交易流水ID
     * @return 结果
     */
    AjaxResult deleteOdsLwzxsfsjFeeGantryFusion01ByIds(String[] bigIds);

}
