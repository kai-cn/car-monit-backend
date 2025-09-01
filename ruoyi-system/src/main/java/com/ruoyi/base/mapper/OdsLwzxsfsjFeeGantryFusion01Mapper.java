package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeGantryFusion01;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 交易流水Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Repository
public interface OdsLwzxsfsjFeeGantryFusion01Mapper extends BaseMapper<OdsLwzxsfsjFeeGantryFusion01> {
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
     * 批量删除交易流水
     *
     * @param bigIds 需要删除的数据ID
     * @return 结果
     */
    int deleteOdsLwzxsfsjFeeGantryFusion01ByIds(String[] bigIds);

    /**
     * 删除交易流水
     *
     * @param bigId 交易流水ID
     * @return 结果
     */
    int deleteOdsLwzxsfsjFeeGantryFusion01ById(String bigId);

}
