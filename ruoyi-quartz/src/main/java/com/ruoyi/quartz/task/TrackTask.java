package com.ruoyi.quartz.task;

import com.ruoyi.base.service.IGeometryService;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.service.ICarSuspiciousService;
import com.ruoyi.manager.service.ICarTrackInfoService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.Date;

/**
 * 定时任务调度测试
 *
 * @author ruoyi
 */
@Slf4j
@Component("trackTask")
public class TrackTask {
    @Autowired
    private ICarTrackInfoService carTrackInfoService;

    @Autowired
    private ICarSuspiciousService carSuspiciousService;


    @Autowired
    private IGeometryService geometryService;

    /**
     * 每三分钟执行一次
     * 车俩实时轨迹同步:0 0/3 * * * ?
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncCurrentTrack() {
        log.info("车俩实时轨迹同步开始同步！"+new Date());
        carTrackInfoService.syncCurrentTrack();
        log.info("车俩实时轨迹同步结束同步！"+new Date());
    }



    /**
     * 每天凌晨5点
     * 可疑车俩:0 0 5 * * ?
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncSuspiciousCar() {
        log.info("可疑车俩数据同步开始同步！"+new Date());
        carSuspiciousService.syncSuspiciousCar();
        geometryService.getRedisList(); // 跟新缓存数据
        log.info("可疑车俩数据同步结束同步！"+new Date());
    }


    /**
     * 每天凌晨6点
     * 车俩历史轨迹同步:0 0 6 * * ?
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncHistoryTrack() {
        log.info("车俩历史轨迹同步开始同步！"+new Date());
        carTrackInfoService.syncHistoryTrack();
        log.info("车俩历史轨迹同步结束同步！"+new Date());
    }
}
