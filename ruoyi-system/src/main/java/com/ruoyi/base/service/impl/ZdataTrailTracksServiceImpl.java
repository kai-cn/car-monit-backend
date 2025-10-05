package com.ruoyi.base.service.impl;

import com.alibaba.fastjson2.JSON;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.base.domain.TrailBo;
import com.ruoyi.base.domain.TrailInfo;
import com.ruoyi.base.domain.ZdataTrailTracks;
import com.ruoyi.base.mapper.ZdataTrailTracksMapper;
import com.ruoyi.base.service.IZdataTrailTracksService;
import com.ruoyi.common.utils.CommonUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

/**
 * 轨迹数据Service业务层处理
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@Service
public class ZdataTrailTracksServiceImpl extends ServiceImpl<ZdataTrailTracksMapper, ZdataTrailTracks> implements IZdataTrailTracksService {

    @Autowired
    private ZdataTrailTracksMapper zdataTrailTracksMapper;

    /**
     * 查询轨迹数据
     *
     * @param uuid 轨迹数据ID
     * @return 轨迹数据
     */
    @Override
    public ZdataTrailTracks selectZdataTrailTracksById(String uuid) {
        return zdataTrailTracksMapper.selectZdataTrailTracksById(uuid);
    }

    /**
     * 查询轨迹数据列表
     *
     * @param zdataTrailTracks 轨迹数据
     * @return 轨迹数据
     */
    @Override
    public List<ZdataTrailTracks> selectZdataTrailTracksList(ZdataTrailTracks zdataTrailTracks) {
        return zdataTrailTracksMapper.selectZdataTrailTracksList(zdataTrailTracks);
    }

    /**
     * 查询车俩历史记录
     * @param zdataTrailTracks
     * @return
     */
    @Override
    public List<TrailInfo> carTrackQuery(ZdataTrailTracks zdataTrailTracks) {
        List<ZdataTrailTracks> carlist = zdataTrailTracksMapper.getHistoryTrail(zdataTrailTracks);
        List<TrailInfo> rtnList = new ArrayList<>();
        if (null != carlist && carlist.size() > 0) {
            for (ZdataTrailTracks tracksBo : carlist) {
                String keyValue = tracksBo.getTrailPoints(); // 行驶轨迹
                List<TrailBo> josnList = new ArrayList<TrailBo>();
                if (CommonUtil.isNotBlank(keyValue)) {
                    josnList = JSON.parseArray(keyValue, TrailBo.class);
                    tracksBo.setTrailPoints("");  // 行驶轨迹
                    String carNo =CommonUtil.isNull(tracksBo.getPlateKey());
                    TrailInfo trailInfo = new TrailInfo();
                    trailInfo.setTrailUuid(carNo);
                    trailInfo.setTracks(tracksBo);
                    trailInfo.setTrailList(josnList);
                    rtnList.add(trailInfo);
                }
            }
        }
        return rtnList;
    }

}
