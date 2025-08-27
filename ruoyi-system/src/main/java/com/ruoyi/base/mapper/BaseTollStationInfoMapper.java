package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.BaseTollStationInfo;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 收费站基础信息Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Repository
public interface BaseTollStationInfoMapper extends BaseMapper<BaseTollStationInfo> {
    /**
     * 查询收费站基础信息
     *
     * @param id 收费站基础信息ID
     * @return 收费站基础信息
     */
    BaseTollStationInfo selectBaseTollStationInfoById(String id);

    /**
     * 查询收费站基础信息列表
     *
     * @param baseTollStationInfo 收费站基础信息
     * @return 收费站基础信息集合
     */
    List<BaseTollStationInfo> selectBaseTollStationInfoList(BaseTollStationInfo baseTollStationInfo);

    /**
     * 批量删除收费站基础信息
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteBaseTollStationInfoByIds(String[] ids);

    /**
     * 删除收费站基础信息
     *
     * @param id 收费站基础信息ID
     * @return 结果
     */
    int deleteBaseTollStationInfoById(String id);

}
