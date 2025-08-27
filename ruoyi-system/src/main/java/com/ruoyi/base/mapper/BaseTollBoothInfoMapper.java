package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.BaseTollBoothInfo;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 收费所基础信息Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Repository
public interface BaseTollBoothInfoMapper extends BaseMapper<BaseTollBoothInfo> {
    /**
     * 查询收费所基础信息
     *
     * @param agentPk 收费所基础信息ID
     * @return 收费所基础信息
     */
    BaseTollBoothInfo selectBaseTollBoothInfoById(String agentPk);

    /**
     * 查询收费所基础信息列表
     *
     * @param baseTollBoothInfo 收费所基础信息
     * @return 收费所基础信息集合
     */
    List<BaseTollBoothInfo> selectBaseTollBoothInfoList(BaseTollBoothInfo baseTollBoothInfo);

    /**
     * 批量删除收费所基础信息
     *
     * @param agentPks 需要删除的数据ID
     * @return 结果
     */
    int deleteBaseTollBoothInfoByIds(String[] agentPks);

    /**
     * 删除收费所基础信息
     *
     * @param agentPk 收费所基础信息ID
     * @return 结果
     */
    int deleteBaseTollBoothInfoById(String agentPk);

}
