# Java 8（Spring Boot 2.5.15 / ruoyi 多模块）镜像。
# 构建阶段用带 Maven 的 Temurin 8，运行阶段只留 JRE，避免把 JDK 和源码带进最终镜像。
# 运行阶段选 Temurin 8 JRE 的原因：项目 pom 只声明 java.version=1.8，21/25 在本仓库无出处。
FROM maven:3.9-eclipse-temurin-8 AS build
WORKDIR /build
COPY . .
RUN mvn -B -q -DskipTests package \
 && cp ruoyi-admin/target/ruoyi-admin-*.jar /build/app.jar

FROM eclipse-temurin:8-jre

# ruoyi 默认把上传目录写成 Windows 路径 D:/ruoyi/uploadPath，容器里必须覆盖。
ENV RUOYI_PROFILE=/app/uploadPath \
    TZ=Asia/Shanghai

RUN groupadd -r app && useradd -r -g app -u 10001 app \
 && mkdir -p /app/logs /app/uploadPath \
 && chown -R app:app /app

WORKDIR /app
COPY --from=build /build/app.jar /app/app.jar

USER 10001
EXPOSE 9989
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
