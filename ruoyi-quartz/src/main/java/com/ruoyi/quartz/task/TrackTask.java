package com.ruoyi.quartz.task;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.service.ICarSuspiciousService;
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

    @Autowired
    private ICarSuspiciousService carSuspiciousService;

    /**
     * 车俩轨迹
     */
    @Transactional(rollbackFor = Exception.class)
    public void sync() {
        System.out.println("车俩实时轨迹同步开始同步！"+new Date());
        carTrackInfoService.sync();
        System.out.println("车俩实时轨迹同步介绍同步！"+new Date());
    }

    /**
     * 可疑车俩
     */
    @Transactional(rollbackFor = Exception.class)
    public void syncSuspiciousCar() {
        System.out.println("可疑车俩数据同步开始同步！"+new Date());
        AjaxResult res = carSuspiciousService.syncSuspiciousCar();
        System.out.println("可疑车俩数据同步介绍同步！"+new Date());
    }

}
