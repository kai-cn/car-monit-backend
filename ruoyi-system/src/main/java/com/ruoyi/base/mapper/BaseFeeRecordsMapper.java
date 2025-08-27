package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.BaseFeeRecords;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 基础-收费流水Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Repository
public interface BaseFeeRecordsMapper extends BaseMapper<BaseFeeRecords> {
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
     * 批量删除基础-收费流水
     *
     * @param bigIds 需要删除的数据ID
     * @return 结果
     */
    int deleteBaseFeeRecordsByIds(String[] bigIds);

    /**
     * 删除基础-收费流水
     *
     * @param bigId 基础-收费流水ID
     * @return 结果
     */
    int deleteBaseFeeRecordsById(String bigId);

}
