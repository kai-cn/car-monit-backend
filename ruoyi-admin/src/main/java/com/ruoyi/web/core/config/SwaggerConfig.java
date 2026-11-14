package com.ruoyi.web.core.config;

import com.ruoyi.common.config.RuoYiConfig;
import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * OpenAPI 3 接口文档配置
 *
 * <p>迁移说明：springfox 3.0.0 依赖 Spring 5 / javax 与 Ant 路径匹配器，在 Spring Boot 3/4
 * 下无法启动（Failed to start bean 'documentationPluginsBootstrapper'），故整体替换为
 * springdoc-openapi 3.x。访问路径：/swagger-ui/index.html、/v3/api-docs。</p>
 *
 * @author ruoyi
 */
@Configuration
public class SwaggerConfig
{
    /** 系统基础配置 */
    @Autowired
    private RuoYiConfig ruoyiConfig;

    /**
     * 创建API
     *
     * <p>开关沿用 swagger.enabled（默认 false，生产关闭），由 springdoc 的
     * springdoc.api-docs.enabled / springdoc.swagger-ui.enabled 同步控制。</p>
     */
    @Bean
    @ConditionalOnProperty(prefix = "swagger", name = "enabled", havingValue = "true")
    public OpenAPI createRestApi()
    {
        return new OpenAPI()
                // 用来创建该API的基本信息，展示在文档的页面中（自定义展示的信息）
                .info(apiInfo())
                /* 设置安全模式，swagger可以设置访问token */
                .components(new Components().addSecuritySchemes("Authorization",
                        new SecurityScheme()
                                .type(SecurityScheme.Type.APIKEY)
                                .in(SecurityScheme.In.HEADER)
                                .name("Authorization")))
                .addSecurityItem(new SecurityRequirement().addList("Authorization"));
    }

    /**
     * 添加摘要信息
     */
    private Info apiInfo()
    {
        return new Info()
                // 设置标题
                .title("标题：若依管理系统_接口文档")
                // 描述
                .description("描述：用于管理集团旗下公司的人员信息,具体包括XXX,XXX模块...")
                // 作者信息
                .contact(new Contact().name(ruoyiConfig.getName()))
                // 版本
                .version("版本号:" + ruoyiConfig.getVersion());
    }
}
