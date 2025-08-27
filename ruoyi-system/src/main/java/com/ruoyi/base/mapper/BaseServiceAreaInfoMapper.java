package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.BaseServiceAreaInfo;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 服务区基础信息Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Repository
public interface BaseServiceAreaInfoMapper extends BaseMapper<BaseServiceAreaInfo> {
    /**
     * 查询服务区基础信息
     *
     * @param agentPk 服务区基础信息ID
     * @return 服务区基础信息
     */
    BaseServiceAreaInfo selectBaseServiceAreaInfoById(String agentPk);

    /**
     * 查询服务区基础信息列表
     *
     * @param baseServiceAreaInfo 服务区基础信息
     * @return 服务区基础信息集合
     */
    List<BaseServiceAreaInfo> selectBaseServiceAreaInfoList(BaseServiceAreaInfo baseServiceAreaInfo);

    /**
     * 批量删除服务区基础信息
     *
     * @param agentPks 需要删除的数据ID
     * @return 结果
     */
    int deleteBaseServiceAreaInfoByIds(String[] agentPks);

    /**
     * 删除服务区基础信息
     *
     * @param agentPk 服务区基础信息ID
     * @return 结果
     */
    int deleteBaseServiceAreaInfoById(String agentPk);

}
