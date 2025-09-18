package com.ruoyi.base.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.ruoyi.base.domain.ZdataTrailTracks;

import java.util.List;

/**
 * 轨迹数据Service接口
 *
 * @author ruoyi
 * @date 2025-09-18
 */
public interface IZdataTrailTracksService extends IService<ZdataTrailTracks> {
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



}
