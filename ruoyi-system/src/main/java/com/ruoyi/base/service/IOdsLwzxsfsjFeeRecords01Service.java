package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeRecords01;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 基础-收费流水Service接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
public interface IOdsLwzxsfsjFeeRecords01Service extends IService<OdsLwzxsfsjFeeRecords01> {
    /**
     * 查询基础-收费流水
     *
     * @param bigId 基础-收费流水ID
     * @return 基础-收费流水
     */
    OdsLwzxsfsjFeeRecords01 selectOdsLwzxsfsjFeeRecords01ById(String bigId);

    /**
     * 查询基础-收费流水列表
     *
     * @param odsLwzxsfsjFeeRecords01 基础-收费流水
     * @return 基础-收费流水集合
     */
    List<OdsLwzxsfsjFeeRecords01> selectOdsLwzxsfsjFeeRecords01List(OdsLwzxsfsjFeeRecords01 odsLwzxsfsjFeeRecords01);


    /**
     * 新增或者修改基础-收费流水
     *
     * @param odsLwzxsfsjFeeRecords01 基础-收费流水
     * @return 结果
     */
    AjaxResult saveOdsLwzxsfsjFeeRecords01(OdsLwzxsfsjFeeRecords01 odsLwzxsfsjFeeRecords01);

    /**
     * 批量删除基础-收费流水
     *
     * @param bigIds 需要删除的基础-收费流水ID
     * @return 结果
     */
    AjaxResult deleteOdsLwzxsfsjFeeRecords01ByIds(String[] bigIds);

}
