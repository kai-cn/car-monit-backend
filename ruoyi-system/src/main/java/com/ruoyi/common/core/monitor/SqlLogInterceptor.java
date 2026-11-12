package com.ruoyi.common.core.monitor;

import com.ruoyi.common.core.context.TraceContext;
import org.apache.ibatis.executor.Executor;
import org.apache.ibatis.mapping.BoundSql;
import org.apache.ibatis.mapping.MappedStatement;
import org.apache.ibatis.mapping.ParameterMapping;
import org.apache.ibatis.plugin.*;
import org.apache.ibatis.reflection.MetaObject;
import org.apache.ibatis.session.Configuration;
import org.apache.ibatis.session.ResultHandler;
import org.apache.ibatis.session.RowBounds;
import org.apache.ibatis.type.TypeHandlerRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Properties;
import java.util.regex.Matcher;

/**
 * SQL日志拦截器（MyBatis Plugin）
 * <p>
 * 【设计目的】
 * 1. 拦截所有MyBatis SQL执行，记录完整SQL和执行耗时
 * 2. 自动识别慢SQL并触发告警（阈值默认1000ms，可配置）
 * 3. 将SQL执行信息收集到 MetricCollector 做性能分析
 * </p>
 *
 * <p>【拦截点说明】</p>
 * <pre>
 * 使用 MyBatis 官方 Plugin 机制：
 * - @Signature(type = Executor.class, method = "query") 拦截查询
 * - @Signature(type = Executor.class, method = "update") 拦截更新/删除
 * 拦截时机在SQL实际执行前，获得完整的执行上下文
 * </pre>
 *
 * <p>【日志内容】</p>
 * <pre>
 * 1. TraceId：关联当前HTTP请求的链路追踪ID
 * 2. Mapper ID：如 com.ruoyi.base.mapper.SnapshotFlowMapper.selectList
 * 3. SQL文本：完整的可直接执行的SQL（参数已替换）
 * 4. 执行耗时：毫秒级精度
 * 5. 慢SQL标记：超过阈值的SQL会被标注 [慢SQL]
 * </pre>
 *
 * @author ruoyi
 */
@Intercepts({
        @Signature(type = Executor.class, method = "query",
                args = {MappedStatement.class, Object.class, RowBounds.class, ResultHandler.class}),
        @Signature(type = Executor.class, method = "query",
                args = {MappedStatement.class, Object.class, RowBounds.class, ResultHandler.class,
                        org.apache.ibatis.cache.CacheKey.class, BoundSql.class}),
        @Signature(type = Executor.class, method = "update",
                args = {MappedStatement.class, Object.class})
})
@Component
public class SqlLogInterceptor implements Interceptor {

    private static final Logger log = LoggerFactory.getLogger(SqlLogInterceptor.class);

    /**
     * 慢SQL阈值（毫秒），SQL执行时间超过此值时触发告警
     * 可通过 application.yml 中 monitor.slow-sql-threshold 配置
     */
    private long slowSqlThreshold = 1000L;

    /**
     * 是否打印完整SQL（包含参数值）
     */
    private boolean printFullSql = true;

    /**
     * 指标收集器（注入用于收集SQL性能指标）
     */
    @Resource
    private MetricCollector metricCollector;

    /**
     * 告警引擎（注入用于慢SQL告警）
     */
    @Resource
    private AlertEngine alertEngine;

    /**
     * 核心拦截方法
     * <p>
     * 【执行流程】
     * 1. 从Invocation中获取 MappedStatement（包含SQL信息）
     * 2. 记录开始时间戳
     * 3. 调用 invocation.proceed() 执行真正的SQL
     * 4. 计算耗时并输出日志
     * 5. 判断是否为慢SQL，决定是否触发告警
     * </p>
     *
     * @param invocation MyBatis调用上下文
     * @return SQL执行结果
     */
    @Override
    public Object intercept(Invocation invocation) throws Throwable {
        // 1. 获取 MappedStatement（包含SQL元信息）
        MappedStatement mappedStatement = (MappedStatement) invocation.getArgs()[0];
        Object parameter = invocation.getArgs()[1];

        // 2. 获取SQL唯一标识（Mapper类名+方法名）
        String sqlId = mappedStatement.getId();

        // 3. 记录开始时间
        long startTime = System.currentTimeMillis();

        // 4. 执行真正的SQL
        Object result = null;
        Throwable throwable = null;
        try {
            result = invocation.proceed();
        } catch (Throwable t) {
            throwable = t;
            throw t;
        } finally {
            // 5. 计算耗时
            long cost = System.currentTimeMillis() - startTime;

            // 6. 收集到指标收集器
            if (metricCollector != null) {
                metricCollector.recordSqlExecution(sqlId, cost);
            }

            // 7. 构造日志信息
            BoundSql boundSql = mappedStatement.getBoundSql(parameter);
            Configuration configuration = mappedStatement.getConfiguration();
            String fullSql = printFullSql ? getFullSql(configuration, boundSql) : boundSql.getSql();

            // 8. 输出日志（慢SQL用WARN级别，普通SQL用DEBUG级别）
            if (cost >= slowSqlThreshold) {
                log.warn(
                        "\n╔══════════════════════════════════════════════════════════\n" +
                        "║ 【慢SQL告警】\n" +
                        "║  Mapper: {}\n" +
                        "║  耗时: {} ms (阈值: {} ms)\n" +
                        "║  SQL: {}\n" +
                        "║  TraceId: {}\n" +
                        "╚══════════════════════════════════════════════════════════",
                        sqlId, cost, slowSqlThreshold, fullSql, TraceContext.getTraceId()
                );

                // 9. 触发告警引擎
                if (alertEngine != null) {
                    alertEngine.alertSlowRequest(sqlId, cost, slowSqlThreshold, TraceContext.getTraceId());
                }
            } else {
                // 普通SQL使用DEBUG级别
                log.debug("[SQL] {} | 耗时: {}ms | TraceId: {}",
                        sqlId, cost, TraceContext.getTraceId());
                if (printFullSql) {
                    log.debug("[SQL-Text] {}", fullSql);
                }
            }

            // 10. SQL异常时记录（即使被catch也要记录）
            if (throwable != null) {
                log.error("[SQL异常] {}, 耗时: {}ms, 异常: {}",
                        sqlId, cost, throwable.getMessage());
                if (alertEngine != null) {
                    alertEngine.alertDatabaseError(sqlId, throwable.getMessage(), TraceContext.getTraceId());
                }
            }
        }
        return result;
    }

    /**
     * 将MyBatis Plugin包装成拦截链
     * 这是MyBatis Plugin机制要求的实现
     */
    @Override
    public Object plugin(Object target) {
        return Plugin.wrap(target, this);
    }

    /**
     * 设置Plugin属性（可通过XML或配置文件配置）
     * 支持的属性：
     * - slowSqlThreshold：慢SQL阈值（毫秒）
     * - printFullSql：是否打印完整SQL
     */
    @Override
    public void setProperties(Properties properties) {
        String threshold = properties.getProperty("slowSqlThreshold");
        if (threshold != null && !threshold.trim().isEmpty()) {
            try {
                this.slowSqlThreshold = Long.parseLong(threshold.trim());
            } catch (NumberFormatException e) {
                log.warn("[SQL拦截器] slowSqlThreshold配置无效，使用默认值: 1000ms");
            }
        }
        String fullSql = properties.getProperty("printFullSql");
        if (fullSql != null && !fullSql.trim().isEmpty()) {
            this.printFullSql = Boolean.parseBoolean(fullSql.trim());
        }
    }

    // ===================== 辅助方法 =====================

    /**
     * 构造完整的可执行SQL（将参数占位符?替换为实际值）
     * <p>
     * 【实现思路】
     * 1. 从BoundSql中获取原始SQL和参数映射关系
     * 2. 遍历每个参数，根据TypeHandler获取实际值
     * 3. 根据参数类型进行格式化（字符串加引号、日期格式化等）
     * 4. 将?替换为格式化后的参数值
     * </p>
     *
     * @param configuration MyBatis配置对象
     * @param boundSql      绑定后的SQL对象
     * @return 完整的可执行SQL字符串
     */
    private String getFullSql(Configuration configuration, BoundSql boundSql) {
        Object parameterObject = boundSql.getParameterObject();
        List<ParameterMapping> parameterMappings = boundSql.getParameterMappings();

        // 1. 获取原始SQL（去除换行、多余空格）
        String sql = boundSql.getSql().replaceAll("[\\s]+", " ");

        if (parameterMappings == null || parameterMappings.isEmpty()) {
            return sql;
        }

        // 2. 获取TypeHandler注册表（用于类型转换）
        TypeHandlerRegistry typeHandlerRegistry = configuration.getTypeHandlerRegistry();

        // 3. 遍历参数，逐个替换?占位符
        MetaObject metaObject = parameterObject == null ? null :
                configuration.newMetaObject(parameterObject);

        for (ParameterMapping parameterMapping : parameterMappings) {
            String propertyName = parameterMapping.getProperty();
            Object value;

            if (boundSql.hasAdditionalParameter(propertyName)) {
                // 3.1 从额外参数中获取（如foreach等动态SQL）
                value = boundSql.getAdditionalParameter(propertyName);
            } else if (parameterObject == null) {
                value = null;
            } else if (typeHandlerRegistry.hasTypeHandler(parameterObject.getClass())) {
                // 3.2 基本类型参数，直接使用
                value = parameterObject;
            } else {
                // 3.3 复杂对象参数，通过反射获取
                if (metaObject == null) {
                    value = null;
                } else {
                    value = metaObject.getValue(propertyName);
                }
            }

            // 4. 将值格式化为SQL字符串
            String paramValue = formatParameter(value);

            // 5. 替换第一个?为参数值
            // 注意：paramValue 可能包含正则元字符（如 BCrypt 口令中的 '$2a$10$...'），
            // 必须用 Matcher.quoteReplacement 转义，否则 replaceFirst 会把 '$2' 当成反向引用，
            // 抛出 IndexOutOfBoundsException: No group 2（该异常会中断当前 SQL 执行）。
            sql = sql.replaceFirst("\\?", Matcher.quoteReplacement(paramValue));
        }

        // 6. 限制SQL长度，避免日志过大（超过2000字符截断）
        if (sql.length() > 2000) {
            sql = sql.substring(0, 2000) + "...(已截断)";
        }

        return sql;
    }

    /**
     * 将参数值格式化为SQL字符串中的表现形式
     * <p>
     * 【规则】
     * - String/Date等加单引号
     * - 数值类型不加引号
     * - null输出为NULL
     * </p>
     */
    private String formatParameter(Object value) {
        if (value == null) {
            return "NULL";
        }

        // 1. 字符串类型：加单引号并转义
        if (value instanceof String) {
            String str = (String) value;
            // 转义SQL中的单引号
            str = str.replace("'", "''");
            // 限制字符串长度
            if (str.length() > 200) {
                str = str.substring(0, 200) + "...";
            }
            return "'" + str + "'";
        }

        // 2. 日期类型：格式化后加单引号
        if (value instanceof Date) {
            return "'" + new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format((Date) value) + "'";
        }

        // 3. 数值/布尔等类型：直接toString
        return value.toString();
    }

    /**
     * 设置慢SQL阈值（支持动态修改）
     */
    public void setSlowSqlThreshold(long thresholdMs) {
        this.slowSqlThreshold = thresholdMs;
    }

    /**
     * 获取当前慢SQL阈值
     */
    public long getSlowSqlThreshold() {
        return this.slowSqlThreshold;
    }
}
