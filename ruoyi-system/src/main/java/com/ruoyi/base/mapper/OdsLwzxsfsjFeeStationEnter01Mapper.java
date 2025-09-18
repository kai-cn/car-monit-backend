package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeStationEnter01;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 收费站入口数据Mapper接口
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@Repository
public interface OdsLwzxsfsjFeeStationEnter01Mapper extends BaseMapper<OdsLwzxsfsjFeeStationEnter01> {
    /**
     * 查询收费站入口数据
     *
     * @param bigId 收费站入口数据ID
     * @return 收费站入口数据
     */
    OdsLwzxsfsjFeeStationEnter01 selectOdsLwzxsfsjFeeStationEnter01ById(Long bigId);

    /**
     * 查询收费站入口数据列表
     *
     * @param odsLwzxsfsjFeeStationEnter01 收费站入口数据
     * @return 收费站入口数据集合
     */
    List<OdsLwzxsfsjFeeStationEnter01> selectOdsLwzxsfsjFeeStationEnter01List(OdsLwzxsfsjFeeStationEnter01 odsLwzxsfsjFeeStationEnter01);


}
