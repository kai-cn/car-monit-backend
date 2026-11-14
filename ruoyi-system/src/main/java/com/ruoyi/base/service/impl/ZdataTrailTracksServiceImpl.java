package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.ruoyi.base.domain.ZdataTrailTracks;
import com.ruoyi.base.mapper.ZdataTrailTracksMapper;
import com.ruoyi.base.service.IZdataTrailTracksService;
import com.ruoyi.common.utils.CommonUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

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
    public List<ZdataTrailTracks> carTrackQuery(ZdataTrailTracks zdataTrailTracks) {
        List<ZdataTrailTracks> list = new ArrayList<>();

        String isCylx = CommonUtil.isNull(zdataTrailTracks.getIsCylx()); // 是否常用路线
        if (isCylx.equals("1")){
            List<ZdataTrailTracks> cylist =  zdataTrailTracksMapper.getCyly(zdataTrailTracks);
            if (null !=cylist && cylist.size() > 0) {
                zdataTrailTracks.setUuidList(cylist.stream().map(ZdataTrailTracks::getUuid).collect(Collectors.toList()));
                Map<String, Integer> map = cylist.stream().collect(Collectors.toMap(ZdataTrailTracks::getUuid, ZdataTrailTracks::getPassCount));
                list = zdataTrailTracksMapper.getHistoryTrail(zdataTrailTracks);
                if (null != list && list.size() > 0){
                    for (ZdataTrailTracks rtn : list) {
                        String uuId = rtn.getUuid();
                        if (null !=map){
                            if (map.containsKey(uuId)){
                                rtn.setPlateKey(rtn.getPlateKey() + "(通行" + map.get(uuId) +"次)");
                            }
                        }
                    }
                    // return list.stream().peek(item -> item.setPlateKey(item.getPlateKey() + "(通行" + map.get(item.getUuid()) +"次)")).collect(Collectors.toList());
                }
            }
        }else{
            // 查询常用路线
            list = zdataTrailTracksMapper.getHistoryTrail(zdataTrailTracks);
        }

        for (ZdataTrailTracks rtn : list) {
            if (CommonUtil.isNotBlank(rtn.getStartLon())){
                rtn.setStartLonDec(new BigDecimal(rtn.getStartLon()));
            }

            if (CommonUtil.isNotBlank(rtn.getStratLat())){
                rtn.setStratLatDec(new BigDecimal(rtn.getStratLat()));
            }

            if (CommonUtil.isNotBlank(rtn.getEndLon())){
                rtn.setEndLonDec(new BigDecimal(rtn.getEndLon()));
            }

            if (CommonUtil.isNotBlank(rtn.getEndLat())){
                rtn.setEndLatDec(new BigDecimal(rtn.getEndLat()));
            }

        }

        return list;
    }

    @Override
    public int removeRealData(List<String> carNoList) {
       return zdataTrailTracksMapper.removeRealData(carNoList);
    }
}
