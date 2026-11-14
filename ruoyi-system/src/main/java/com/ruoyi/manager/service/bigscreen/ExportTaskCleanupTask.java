package com.ruoyi.manager.service.bigscreen;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * 导出任务清理：定期清理长时间未轮询到终态的本地积压统计。
 *
 * <p>Redis 任务元数据由保留期 TTL 自动过期；本任务只清理进程内 activeTasks，
 * 避免指标长期虚高。调度复用 RuoYi scheduledExecutorService（工程无 @EnableScheduling）。</p>
 *
 * @author car-monit-backend-java-v3
 */
@Component
public class ExportTaskCleanupTask
{
    private static final Logger log = LoggerFactory.getLogger(ExportTaskCleanupTask.class);

    @Value("${export.cleanup.enabled:true}")
    private boolean enabled;

    @Value("${export.cleanup.interval-ms:3600000}")
    private long intervalMs;

    @Autowired
    private BigScreenExportService exportService;

    @Autowired
    @Qualifier("scheduledExecutorService")
    private ScheduledExecutorService scheduler;

    @PostConstruct
    public void start()
    {
        if (!enabled || scheduler == null)
        {
            return;
        }
        scheduler.scheduleWithFixedDelay(new Runnable()
        {
            @Override
            public void run()
            {
                try
                {
                    exportService.cleanupStaleTasks();
                }
                catch (RuntimeException e)
                {
                    log.warn("[导出清理] 执行失败: {}", e.getMessage());
                }
            }
        }, intervalMs, Math.max(60000L, intervalMs), TimeUnit.MILLISECONDS);
    }
}
