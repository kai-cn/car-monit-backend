package com.ruoyi.framework.config;

import java.time.Duration;
import java.util.TimeZone;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.jackson.autoconfigure.JsonMapperBuilderCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.EnableAspectJAutoProxy;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

/**
 * 程序注解配置
 *
 * @author ruoyi
 */
@Configuration
// 表示通过aop框架暴露该代理对象,AopContext能够访问
@EnableAspectJAutoProxy(exposeProxy = true)
// 指定要扫描的Mapper类的包的路径
@MapperScan("com.ruoyi.**.mapper")
public class ApplicationConfig
{
    @Value("${export.download.connect-timeout-ms:3000}")
    private int downloadConnectTimeoutMs;

    @Value("${export.download.read-timeout-ms:1800000}")
    private int downloadReadTimeoutMs;

    @Value("${traffic-api.internal-token:}")
    private String internalToken;

    /**
     * 时区配置（Spring Boot 4 起 Jackson 2 的 Jackson2ObjectMapperBuilderCustomizer 已由
     * Jackson 3 的 JsonMapperBuilderCustomizer 取代）
     */
    @Bean
    public JsonMapperBuilderCustomizer jacksonObjectMapperCustomization()
    {
        return jsonMapperBuilder -> jsonMapperBuilder.defaultTimeZone(TimeZone.getDefault());
    }

    @Bean
    public RestTemplate restTemplate()
    {
        return new RestTemplate();
    }

    /**
     * 导出文件下载专用：长读超时、流式读取，避免大文件占用在线查询时间片。
     */
    @Bean(name = "trafficApiDownloadRestTemplate")
    public RestTemplate trafficApiDownloadRestTemplate()
    {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        // Spring Framework 6.1 起 setConnectTimeout/setReadTimeout 只接受 Duration
        factory.setConnectTimeout(Duration.ofMillis(downloadConnectTimeoutMs));
        factory.setReadTimeout(Duration.ofMillis(downloadReadTimeoutMs));
        RestTemplate template = new RestTemplate(factory);
        if (internalToken != null && !internalToken.trim().isEmpty())
        {
            final String token = internalToken.trim();
            template.getInterceptors().add((request, body, execution) -> {
                request.getHeaders().set("X-Internal-Token", token);
                return execution.execute(request, body);
            });
        }
        return template;
    }
}
