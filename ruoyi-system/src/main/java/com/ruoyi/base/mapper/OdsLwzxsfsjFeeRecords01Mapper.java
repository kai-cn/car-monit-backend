package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeRecords01;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 基础-收费流水Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Repository
public interface OdsLwzxsfsjFeeRecords01Mapper extends BaseMapper<OdsLwzxsfsjFeeRecords01> {
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
     * 批量删除基础-收费流水
     *
     * @param bigIds 需要删除的数据ID
     * @return 结果
     */
    int deleteOdsLwzxsfsjFeeRecords01ByIds(String[] bigIds);

    /**
     * 删除基础-收费流水
     *
     * @param bigId 基础-收费流水ID
     * @return 结果
     */
    int deleteOdsLwzxsfsjFeeRecords01ById(String bigId);

}
