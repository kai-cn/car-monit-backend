package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeStationExit01;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 收费站出口流水Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Repository
public interface OdsLwzxsfsjFeeStationExit01Mapper extends BaseMapper<OdsLwzxsfsjFeeStationExit01> {
    /**
     * 查询收费站出口流水
     *
     * @param bigId 收费站出口流水ID
     * @return 收费站出口流水
     */
    OdsLwzxsfsjFeeStationExit01 selectOdsLwzxsfsjFeeStationExit01ById(String bigId);

    /**
     * 查询收费站出口流水列表
     *
     * @param odsLwzxsfsjFeeStationExit01 收费站出口流水
     * @return 收费站出口流水集合
     */
    List<OdsLwzxsfsjFeeStationExit01> selectOdsLwzxsfsjFeeStationExit01List(OdsLwzxsfsjFeeStationExit01 odsLwzxsfsjFeeStationExit01);

    /**
     * 批量删除收费站出口流水
     *
     * @param bigIds 需要删除的数据ID
     * @return 结果
     */
    int deleteOdsLwzxsfsjFeeStationExit01ByIds(String[] bigIds);

    /**
     * 删除收费站出口流水
     *
     * @param bigId 收费站出口流水ID
     * @return 结果
     */
    int deleteOdsLwzxsfsjFeeStationExit01ById(String bigId);

}
