package com.ruoyi.framework.config;

import org.apache.http.HttpHost;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Elasticsearch配置类
 * <p>
 * 用途：配置Elasticsearch客户端，用于与ES集群进行交互
 * 功能：
 * 1. 创建RestHighLevelClient客户端
 * 2. 自动在Bean销毁时关闭连接
 * </p>
 *
 * @author ruoyi
 */
@Configuration
public class ElasticsearchConfig {

    /** Elasticsearch服务器主机地址 */
    @Value("${elasticsearch.host}")
    private String host;

    /** Elasticsearch服务端口，默认9200 */
    @Value("${elasticsearch.port}")
    private int port;

    /**
     * 创建Elasticsearch高级客户端
     * <p>
     * 用途：提供ES的高级API操作，包括索引、搜索、删除等
     * destroyMethod="close"：Spring容器销毁Bean时自动调用close方法关闭连接
     * </p>
     */
    @Bean(destroyMethod = "close")
    public RestHighLevelClient restHighLevelClient() {
        return new RestHighLevelClient(
                RestClient.builder(
                        new HttpHost(host, port, "http")
                )
        );
    }
}
