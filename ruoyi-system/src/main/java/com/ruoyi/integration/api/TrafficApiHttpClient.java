package com.ruoyi.integration.api;

import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.DeserializationFeature;
import tools.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.client.ClientHttpResponse;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.DefaultResponseErrorHandler;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

import jakarta.annotation.PostConstruct;
import java.io.IOException;
import java.net.URI;
import java.time.Duration;
import java.util.EnumMap;
import java.util.Map;

/**
 * 按场景隔离超时的 api HTTP 客户端。
 *
 * <p>每个 {@link TrafficApiScenario} 一个 RestTemplate：连接超时统一，读超时按场景；
 * 非 2xx 不抛异常，由 {@link ResilientApiExecutor} 统一映射错误码。</p>
 *
 * @author car-monit-backend-java-v3
 */
@Service
public class TrafficApiHttpClient
{
    private static final Logger log = LoggerFactory.getLogger(TrafficApiHttpClient.class);

    private final TrafficApiProperties properties;

    private final ObjectMapper objectMapper;

    private final Map<TrafficApiScenario, RestTemplate> templates =
            new EnumMap<TrafficApiScenario, RestTemplate>(TrafficApiScenario.class);

    @Value("${vehicleMonitor.baseUrl}")
    private String baseUrl;

    /** 与 api traffic.security.internal-token 一致，用于访问受保护的内部端点。 */
    @Value("${traffic-api.internal-token:}")
    private String internalToken;

    @Autowired
    public TrafficApiHttpClient(TrafficApiProperties properties, ObjectMapper objectMapper)
    {
        this.properties = properties;
        // api 返回字段可能多于 backend VO（如 warning/list 的维度快照字段），忽略未知字段
        this.objectMapper = objectMapper.rebuild()
                .disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)
                .build();
    }

    @PostConstruct
    public void init()
    {
        for (TrafficApiScenario scenario : TrafficApiScenario.values())
        {
            SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
            factory.setConnectTimeout(Duration.ofMillis(properties.getConnectTimeoutMs()));
            factory.setReadTimeout(Duration.ofMillis(properties.readTimeoutMs(scenario)));
            RestTemplate template = new RestTemplate(factory);
            template.setErrorHandler(new NoThrowErrorHandler());
            if (internalToken != null && !internalToken.trim().isEmpty())
            {
                final String token = internalToken.trim();
                template.getInterceptors().add((request, body, execution) -> {
                    request.getHeaders().set("X-Internal-Token", token);
                    return execution.execute(request, body);
                });
            }
            templates.put(scenario, template);
        }
    }

    public <T> ApiHttpResult<T> get(TrafficApiScenario scenario, String path,
                                    Map<String, String> params, Class<T> type)
    {
        return exchange(scenario, path, params, HttpMethod.GET, null, type, null);
    }

    public <T> ApiHttpResult<T> get(TrafficApiScenario scenario, String path,
                                    Map<String, String> params, TypeReference<T> type)
    {
        return exchange(scenario, path, params, HttpMethod.GET, null, null, type);
    }

    public <T> ApiHttpResult<T> post(TrafficApiScenario scenario, String path,
                                     Map<String, String> params, Object body, TypeReference<T> type)
    {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Object> entity = new HttpEntity<Object>(body, headers);
        return exchange(scenario, path, params, HttpMethod.POST, entity, null, type);
    }

    private <T> ApiHttpResult<T> exchange(TrafficApiScenario scenario, String path,
                                          Map<String, String> params, HttpMethod method,
                                          HttpEntity<?> entity, Class<T> type, TypeReference<T> typeRef)
    {
        RestTemplate template = templates.get(scenario);
        URI uri = buildUri(path, params);
        try
        {
            org.springframework.http.ResponseEntity<String> response =
                    template.exchange(uri, method, entity, String.class);
            int status = response.getStatusCode().value();
            String body = response.getBody();
            if (status < 200 || status >= 300)
            {
                return ApiHttpResult.error(status, body, null);
            }
            if (type == null && typeRef == null)
            {
                return ApiHttpResult.ok(status, body, null);
            }
            if (body == null || body.trim().isEmpty())
            {
                // 2xx 空体必须走 CONTRACT_VIOLATION 降级，不能静默返回 null 让调用方
                // 把「api 异常」当成空列表/空统计；裸 body 场景（type==null）不在此分支。
                return ApiHttpResult.contractViolation(status, body,
                        new IOException("api 返回 2xx 空响应体"));
            }
            T parsed = type != null
                    ? objectMapper.readValue(body, type)
                    : objectMapper.readValue(body, typeRef);
            return ApiHttpResult.ok(status, body, parsed);
        }
        catch (RuntimeException e)
        {
            // Jackson 3 的 JacksonException 与 Spring 的 RestClientException 均为非受检异常，统一在此兜底
            return ApiHttpResult.error(0, null, e);
        }
    }

    private URI buildUri(String path, Map<String, String> params)
    {
        String root = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        UriComponentsBuilder builder = UriComponentsBuilder.fromUriString(root + path);
        if (params != null)
        {
            for (Map.Entry<String, String> entry : params.entrySet())
            {
                if (entry.getValue() != null)
                {
                    builder.queryParam(entry.getKey(), entry.getValue());
                }
            }
        }
        return builder.build().encode().toUri();
    }

    /**
     * 非 2xx 由执行器按状态码映射，不让 RestTemplate 抛 HttpStatusCodeException。
     */
    private static class NoThrowErrorHandler extends DefaultResponseErrorHandler
    {
        @Override
        public void handleError(URI url, HttpMethod method, ClientHttpResponse response) throws IOException
        {
            log.debug("[api] 非 2xx 响应 {} {} status={}", method, url, response.getStatusCode().value());
        }
    }
}
