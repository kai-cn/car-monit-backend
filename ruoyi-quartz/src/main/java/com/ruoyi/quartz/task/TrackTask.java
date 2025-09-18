package com.ruoyi.quartz.task;

import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

/**
 * 定时任务调度测试
 * 
 * @author ruoyi
 */
@Component("trackTask")
public class TrackTask
{
    @Transactional(rollbackFor = Exception.class)
    public void sync() {
        System.out.println("轨迹数据开始同步！");
    }
}
