package com.ruoyi.framework.config;

import org.apache.ibatis.session.SqlSessionFactory;
import org.mybatis.spring.mapper.MapperFactoryBean;
import org.springframework.beans.MutablePropertyValues;
import org.springframework.beans.factory.config.BeanDefinition;
import org.springframework.beans.factory.config.BeanFactoryPostProcessor;
import org.springframework.beans.factory.config.ConfigurableListableBeanFactory;
import org.springframework.beans.factory.config.RuntimeBeanReference;
import org.springframework.beans.factory.support.AbstractBeanDefinition;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.PriorityOrdered;
import org.springframework.util.ClassUtils;
import org.springframework.util.StringUtils;

import java.util.concurrent.atomic.AtomicInteger;

/**
 * Bridges the Spring Boot 4 / Spring Framework 7 AOT gap for MyBatis-Plus mappers.
 *
 * <p>{@code @MapperScan} registers every mapper as a {@link MapperFactoryBean} with
 * {@code AUTOWIRE_BY_TYPE}, relying on Spring to call
 * {@code setSqlSessionFactory(SqlSessionFactory)} at runtime. Spring's AOT bean
 * definition code generator does NOT retain {@code autowireMode}: the generated
 * {@code XxxMapper__BeanDefinitions} classes only contain {@code mapperInterface}
 * and {@code addToConfig}. The resulting native image therefore fails at startup with
 * {@code "Property 'sqlSessionFactory' or 'sqlSessionTemplate' are required"}.
 *
 * <p>This post-processor turns the implicit by-type autowiring into an explicit
 * {@link RuntimeBeanReference}, which the AOT generator does serialize. It runs both
 * during {@code process-aot} (so the generated code contains the reference) and at
 * runtime (harmless no-op when the reference is already present). It is registered
 * unconditionally so the JVM fat jar and the native image share the same code path;
 * the added property is semantically identical to the original by-type autowiring.
 *
 * <p>See docs/v3/native-image-aot-mybatis-fix.md for the full diagnosis.
 */
@Configuration(proxyBeanMethods = false)
public class NativeMapperSqlSessionFactoryRegistrar {

    private static final String SQL_SESSION_FACTORY_BEAN = "sqlSessionFactory";

    /**
     * Static @Bean so the configuration class is not instantiated early and the
     * post-processor is available before any mapper bean is created.
     */
    @Bean
    public static BeanFactoryPostProcessor mapperSqlSessionFactoryBeanReference() {
        return new MapperSqlSessionFactoryBeanReference();
    }

    static final class MapperSqlSessionFactoryBeanReference
            implements BeanFactoryPostProcessor, PriorityOrdered {

        @Override
        public void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
            String factoryBeanName = resolveSqlSessionFactoryName(beanFactory);
            if (factoryBeanName == null) {
                // No SqlSessionFactory definition yet: keep the original by-type behaviour.
                return;
            }
            AtomicInteger patched = new AtomicInteger();
            for (String beanName : beanFactory.getBeanDefinitionNames()) {
                BeanDefinition definition = beanFactory.getBeanDefinition(beanName);
                if (!(definition instanceof AbstractBeanDefinition abd)) {
                    continue;
                }
                Class<?> beanClass = resolveBeanClass(abd, beanFactory);
                if (beanClass == null || !MapperFactoryBean.class.isAssignableFrom(beanClass)) {
                    continue;
                }
                MutablePropertyValues values = abd.getPropertyValues();
                if (values.contains("sqlSessionFactory") || values.contains("sqlSessionTemplate")) {
                    continue;
                }
                values.add("sqlSessionFactory", new RuntimeBeanReference(factoryBeanName));
                patched.incrementAndGet();
            }
            // System.out is intentional: this also runs inside the AOT build JVM where
            // logging infrastructure may not be initialised yet.
            System.out.println("[native-aot] explicit sqlSessionFactory reference patched into "
                    + patched.get() + " MapperFactoryBean definition(s) -> " + factoryBeanName);
        }

        private static String resolveSqlSessionFactoryName(ConfigurableListableBeanFactory beanFactory) {
            if (beanFactory.containsBeanDefinition(SQL_SESSION_FACTORY_BEAN)) {
                return SQL_SESSION_FACTORY_BEAN;
            }
            String[] names = beanFactory.getBeanNamesForType(SqlSessionFactory.class, true, false);
            return names.length > 0 ? names[0] : null;
        }

        private static Class<?> resolveBeanClass(AbstractBeanDefinition definition,
                                                 ConfigurableListableBeanFactory beanFactory) {
            if (definition.hasBeanClass()) {
                return definition.getBeanClass();
            }
            String className = definition.getBeanClassName();
            if (!StringUtils.hasText(className)) {
                return null;
            }
            try {
                return ClassUtils.forName(className, beanFactory.getBeanClassLoader());
            } catch (Throwable ignored) {
                return null;
            }
        }

        @Override
        public int getOrder() {
            return PriorityOrdered.HIGHEST_PRECEDENCE;
        }
    }
}
