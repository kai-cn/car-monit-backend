package com.ruoyi.common.config;

import com.ruoyi.common.utils.SnowflakeIdWorker;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * @author gl
 * @version 1.0
 * @description
 * @date 2023/8/23 17:11
 */

@Configuration
public class IdWorkerConfig {

    /**
     * 保证 SnowflakeIdWorker 单例
     * @return
     */
    @Bean
    public SnowflakeIdWorker snowflakeIdWorker() {
        return new SnowflakeIdWorker(0, 0);
    }

}
