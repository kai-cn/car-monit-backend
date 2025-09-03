package com.ruoyi.web.core.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import springfox.documentation.builders.PathSelectors;
import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.service.*;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spi.service.contexts.SecurityContext;
import springfox.documentation.spring.web.plugins.Docket;

import java.util.Collections;
import java.util.List;

@Configuration
public class Knife4jConfig {

    @Bean
    public Docket topDocket() {
        return build("车辆管理", "com.ruoyi.web.controller");
    }


    /**
     * 构建Docket对象
     *
     * @param groupName   分组名称
     * @param scanPackage 扫描包名
     * @return 文档对象
     */
    public static Docket build(String groupName, String scanPackage) {

        List<SecurityContext> securityContexts = securityContexts();
        List<SecurityScheme> securitySchemes = securitySchemes();

        return new Docket(DocumentationType.SWAGGER_2).securityContexts(securityContexts)
                .securitySchemes(securitySchemes).apiInfo(ApiInfo.DEFAULT).groupName(groupName).select()
                .apis(RequestHandlerSelectors.basePackage(scanPackage)).paths(PathSelectors.any()).build();

    }

    // 构建securityContexts
    private static List<SecurityContext> securityContexts() {

        AuthorizationScope authorizationScope = new AuthorizationScope("global", "accessEverywhere");
        AuthorizationScope[] authorizationScopes = new AuthorizationScope[1];
        authorizationScopes[0] = authorizationScope;
        SecurityReference securityReference = new SecurityReference("Authorization", authorizationScopes);

        return Collections.singletonList(
                SecurityContext.builder().securityReferences(Collections.singletonList(securityReference))
                        .forPaths(PathSelectors.regex("/.*")).build());
    }

    // 构建securitySchemes
    private static List<SecurityScheme> securitySchemes() {
        return Collections
                .singletonList(new ApiKey("Authorization", "Authorization", "header"));
    }


}
