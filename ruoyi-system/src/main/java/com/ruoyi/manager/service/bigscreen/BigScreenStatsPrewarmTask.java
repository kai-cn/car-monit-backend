package com.ruoyi.manager.service.bigscreen;

import com.ruoyi.manager.domain.vo.bigscreen.IncomeStatisticParam;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * 统计预聚合缓存预热（阶段二）。
 *
 * <p>大屏轮询集中在下班前/整点；预热任务在 api 预聚合可用时把 escape/audit/income/topN
 * 的默认时间窗写入两级缓存，减少首批请求的冷启动延迟。默认关闭，避免无谓负载。</p>
 *
 * @author car-monit-backend-java-v3
 */
@Component
public class BigScreenStatsPrewarmTask
{
    private static final Logger log = LoggerFactory.getLogger(BigScreenStatsPrewarmTask.class);

    @Value("${bigscreen.stats.prewarm.enabled:false}")
    private boolean enabled;

    @Autowired
    private BigScreenStatsService statsService;

    @Autowired
    private FeatureSwitchService featureSwitchService;

    @Value("${bigscreen.stats.prewarm.interval-ms:300000}")
    private long intervalMs;

    @Autowired
    @Qualifier("scheduledExecutorService")
    private ScheduledExecutorService scheduler;

    @PostConstruct
    public void start()
    {
        if (enabled && scheduler != null)
        {
            scheduler.scheduleWithFixedDelay(new Runnable()
            {
                @Override
                public void run()
                {
                    warm();
                }
            }, intervalMs, Math.max(60000L, intervalMs), TimeUnit.MILLISECONDS);
        }
    }

    public void warm()
    {
        if (!enabled
                || !featureSwitchService.isEnabled(FeatureSwitchService.STATS_API_FIRST))
        {
            return;
        }
        SimpleDateFormat day = new SimpleDateFormat("yyyy-MM-dd");
        SimpleDateFormat dateTime = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        Date now = new Date();
        String today = day.format(now);
        String start = dateTime.format(now);
        String end = dateTime.format(now);

        IncomeStatisticParam param = new IncomeStatisticParam();
        param.setApplyTime1(today);
        param.setApplyTime2(today);
        param.setQueryDateType("suo");
        param.setStartDate(today);
        try
        {
            statsService.carStatistics(param);
            statsService.carAudit(param);
            statsService.incomeStatistic(param);
            statsService.topTen(start, end);
        }
        catch (RuntimeException e)
        {
            // 预热失败不影响业务；api 不可用时缓存层会按降级策略处理
            log.debug("[大屏预热] 跳过: {}", e.getMessage());
        }
    }
}
