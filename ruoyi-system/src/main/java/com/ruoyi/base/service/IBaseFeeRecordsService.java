package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.BaseFeeRecords;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 基础-收费流水Service接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
public interface IBaseFeeRecordsService extends IService<BaseFeeRecords> {
    /**
     * 查询基础-收费流水
     *
     * @param bigId 基础-收费流水ID
     * @return 基础-收费流水
     */
    BaseFeeRecords selectBaseFeeRecordsById(String bigId);

    /**
     * 查询基础-收费流水列表
     *
     * @param baseFeeRecords 基础-收费流水
     * @return 基础-收费流水集合
     */
    List<BaseFeeRecords> selectBaseFeeRecordsList(BaseFeeRecords baseFeeRecords);


    /**
     * 新增或者修改基础-收费流水
     *
     * @param baseFeeRecords 基础-收费流水
     * @return 结果
     */
    AjaxResult saveBaseFeeRecords(BaseFeeRecords baseFeeRecords);

    /**
     * 批量删除基础-收费流水
     *
     * @param bigIds 需要删除的基础-收费流水ID
     * @return 结果
     */
    AjaxResult deleteBaseFeeRecordsByIds(String[] bigIds);

}
