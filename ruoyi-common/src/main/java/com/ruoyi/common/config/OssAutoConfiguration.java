

package com.ruoyi.common.config;

import com.ruoyi.common.utils.http.OssEndpoint;
import com.ruoyi.common.utils.http.OssTemplate;
import lombok.AllArgsConstructor;
import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;

/**
 * aws 自动配置类
 *
 * <p>Boot 3 起自动配置只认 META-INF/spring/…AutoConfiguration.imports，
 * 因此本类改为 {@link AutoConfiguration} 并在该 imports 文件中登记（原来只靠 spring.factories）。</p>
 *
 * @author ose
 * @author 858695266
 */
@AutoConfiguration
@AllArgsConstructor
@EnableConfigurationProperties({ OssProperties.class })
public class OssAutoConfiguration {

	private final OssProperties properties;

	@Bean
	@ConditionalOnMissingBean(OssTemplate.class)
	@ConditionalOnProperty(name = "oss.enable", havingValue = "true", matchIfMissing = true)
	public OssTemplate ossTemplate() {
		return new OssTemplate(properties);
	}

	@Bean
	@ConditionalOnProperty(name = "oss.info", havingValue = "true")
	public OssEndpoint ossEndpoint(OssTemplate template) {
		return new OssEndpoint(template);
	}

}
