package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.CarParaVO;
import com.ruoyi.base.domain.ZdataTrailTracks;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 轨迹数据Mapper接口
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@Repository
public interface ZdataTrailTracksMapper extends BaseMapper<ZdataTrailTracks> {
    /**
     * 查询轨迹数据
     *
     * @param uuid 轨迹数据ID
     * @return 轨迹数据
     */
    ZdataTrailTracks selectZdataTrailTracksById(String uuid);

    /**
     * 查询轨迹数据列表
     *
     * @param zdataTrailTracks 轨迹数据
     * @return 轨迹数据集合
     */
    List<ZdataTrailTracks> selectZdataTrailTracksList(ZdataTrailTracks zdataTrailTracks);


    /**
     * 轨迹查询
     */
    List<ZdataTrailTracks> getHistoryTrail(CarParaVO carParaVO);


}
