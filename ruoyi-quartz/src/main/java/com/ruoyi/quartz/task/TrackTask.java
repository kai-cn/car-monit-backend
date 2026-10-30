package com.ruoyi.quartz.task;

import com.ruoyi.base.domain.TrailInfo;
import com.ruoyi.base.service.IGeometryService;
import com.ruoyi.manager.domain.CarExceptRecord;
import com.ruoyi.manager.service.ICarExceptRecordService;
import com.ruoyi.manager.service.ICarSuspiciousService;
import com.ruoyi.manager.service.ICarTrackInfoService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;

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

    @Autowired
    private ICarExceptRecordService carExceptRecordService;


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
        List<TrailInfo> trailInfoList = new ArrayList<>();
         carSuspiciousService.syncSuspiciousCar("redis",trailInfoList);
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
        geometryService.updateRedisList(); // 跟新缓存数据
        log.info("车俩历史轨迹同步结束同步！"+new Date());

    }

    /**
     * 每天凌晨7点
     * 车辆逃费数据更新:0 0 7 * * ?
     */
    @Transactional(rollbackFor = Exception.class)
    public void saveCarExcept() {
        log.info("车辆逃费数据更新开始！"+new Date());
        carExceptRecordService.saveCarExcept(new CarExceptRecord());
        log.info("车辆逃费数据更新结束！"+new Date());
    }

    /**
     * 每10分钟执行一次
     * 车俩历史轨迹同步:0 0/10 * * * ?
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncHistoryTrackNoCar() {
       /* log.info("车俩历史轨迹同步开始同步！"+new Date());
        carTrackInfoService.syncHistoryTrackNoCar();
        log.info("车俩历史轨迹同步结束同步！"+new Date());*/
    }


    /**
     * 可疑车辆迁移：保留一个月的数据
     * 车俩历史轨迹同步:0 0 21 * * ?
     */
    @Transactional(rollbackFor = Exception.class)
    public void changeCarSuspicious() {
        log.info("可疑车辆迁移开始同步！" + new Date());
        carSuspiciousService.changeCarSuspicious();
        log.info("可疑车辆迁移同步！" + new Date());
    }


}
