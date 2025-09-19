package com.ruoyi.quartz.task;

import com.ruoyi.manager.service.ICarTrackInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.Date;

/**
 * 定时任务调度测试
 *
 * @author ruoyi
 */
@Component("trackTask")
public class TrackTask {
    @Autowired
    private ICarTrackInfoService carTrackInfoService;

    /**
     * 车俩轨迹
     */
    @Transactional(rollbackFor = Exception.class)
    public void sync() {
        System.out.println("轨迹数据开始同步！"+new Date());
        carTrackInfoService.sync();
        System.out.println("轨迹数据介绍同步！"+new Date());
    }

    /**
     * 可疑车俩
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncSuspiciousCar() {
        System.out.println("可疑车俩数据开始同步！"+new Date());
        carTrackInfoService.syncSuspiciousCar();
        System.out.println("可疑车俩介绍同步！"+new Date());
    }

}
