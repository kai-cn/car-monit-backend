package com.ruoyi.manager.service.bigscreen;

import com.ruoyi.common.core.metrics.MetricsRegistry;
import com.ruoyi.integration.api.ApiHttpResult;
import com.ruoyi.integration.api.TrafficApiHttpClient;
import com.ruoyi.integration.api.TrafficApiScenario;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * api 导出能力探测。
 *
 * <p>api 能力端点返回全局开关与“按表/按字段”的支持矩阵
 * （{@code fullDimensionFilters/multiValueDimensionFilters/plateColorName/dimensionFilters/displayFields}）。
 * backend 据此自动放开对应能力；api 未实现（404）或不可达时保持保守拒绝。</p>
 *
 * <p>探测结果缓存 5 分钟；配置 {@code bigscreen.export.full-dimension-filters=true/false}
 * 可强制覆盖（true=按“全表全字段支持”放行，false=全部拒绝）。</p>
 *
 * @author car-monit-backend-java-v3
 */
@Service
public class ExportCapabilityService
{
    private static final Logger log = LoggerFactory.getLogger(ExportCapabilityService.class);

    private static final long PROBE_INTERVAL_MS = 5L * 60L * 1000L;

    private static final String CAPABILITIES_PATH = "/api/v3/export/capabilities";

    private static final Set<String> ALL_TABLES =
            new HashSet<String>(Arrays.asList("snapshot", "fee", "trail"));

    private static final Set<String> CODE_DIMENSIONS = new HashSet<String>(Arrays.asList(
            "orgcode", "sectioncode", "roadcode", "gantrycode", "tollcode", "gantryid"));

    private static final Set<String> NAME_DIMENSIONS = new HashSet<String>(Arrays.asList(
            "orgname", "sectionname", "roadname", "gantryname", "tollname"));

    /** auto / true / false */
    @Value("${bigscreen.export.full-dimension-filters:auto}")
    private String mode;

    @Autowired
    private TrafficApiHttpClient httpClient;

    private volatile Capabilities cached;

    private volatile long nextProbeAt = 0L;

    /**
     * 返回当前能力；api 未实现或不可达时返回“空能力”（全部拒绝）。
     */
    public Capabilities current()
    {
        String value = mode == null ? "auto" : mode.trim();
        if ("true".equalsIgnoreCase(value) || "on".equalsIgnoreCase(value))
        {
            return Capabilities.allSupported();
        }
        if ("false".equalsIgnoreCase(value) || "off".equalsIgnoreCase(value))
        {
            return Capabilities.none();
        }
        long now = System.currentTimeMillis();
        Capabilities current = cached;
        if (current != null && now < nextProbeAt)
        {
            return current;
        }
        Capabilities probed = probe();
        cached = probed;
        nextProbeAt = now + PROBE_INTERVAL_MS;
        return probed;
    }

    private Capabilities probe()
    {
        try
        {
            ApiHttpResult<Map> result = httpClient.get(TrafficApiScenario.EXPORT_STATUS,
                    CAPABILITIES_PATH, Collections.<String, String>emptyMap(), Map.class);
            if (result == null || !result.is2xx() || result.getResult() == null)
            {
                MetricsRegistry.increment("export.capability.gate_closed");
                return Capabilities.none();
            }
            Capabilities caps = parse(result.getResult());
            if (caps.fullDimensionFilters)
            {
                log.info("[导出能力] 维度过滤已支持 tables={}", caps.dimensionFields.keySet());
            }
            if (caps.plateColorNameTables.contains("fee"))
            {
                log.info("[导出能力] fee 展示导出已支持 plate_color_name");
            }
            return caps;
        }
        catch (RuntimeException e)
        {
            log.debug("[导出能力] 探测失败，按未支持处理: {}", e.getMessage());
            return Capabilities.none();
        }
    }

    @SuppressWarnings("unchecked")
    private Capabilities parse(Map body)
    {
        boolean full = truthy(body.get("fullDimensionFilters"));
        boolean plateColorName = truthy(body.get("plateColorName"));
        Map<String, Set<String>> dimensionFields = new LinkedHashMap<String, Set<String>>();
        Object dimensions = body.get("dimensionFilters");
        if (dimensions instanceof Map)
        {
            for (Map.Entry<?, ?> entry : ((Map<?, ?>) dimensions).entrySet())
            {
                String table = String.valueOf(entry.getKey());
                Set<String> fields = new HashSet<String>();
                Object values = entry.getValue();
                if (values instanceof List)
                {
                    for (Object item : (List<?>) values)
                    {
                        if (item != null && !String.valueOf(item).trim().isEmpty())
                        {
                            fields.add(String.valueOf(item).trim());
                        }
                    }
                }
                dimensionFields.put(table, fields);
            }
        }
        Set<String> plateColorTables = new HashSet<String>();
        Object displayFields = body.get("displayFields");
        if (displayFields instanceof Map)
        {
            for (Map.Entry<?, ?> entry : ((Map<?, ?>) displayFields).entrySet())
            {
                String table = String.valueOf(entry.getKey());
                Object values = entry.getValue();
                if (values instanceof List)
                {
                    for (Object item : (List<?>) values)
                    {
                        if ("plate_color_name".equals(String.valueOf(item)))
                        {
                            plateColorTables.add(table);
                            break;
                        }
                    }
                }
            }
        }
        return new Capabilities(full, plateColorName, dimensionFields, plateColorTables);
    }

    private boolean truthy(Object value)
    {
        return value != null && ("true".equalsIgnoreCase(String.valueOf(value))
                || "1".equals(String.valueOf(value)));
    }

    /**
     * 导出能力快照。
     */
    public static class Capabilities
    {
        private final boolean fullDimensionFilters;

        private final boolean plateColorName;

        private final Map<String, Set<String>> dimensionFields;

        private final Set<String> plateColorNameTables;

        Capabilities(boolean fullDimensionFilters, boolean plateColorName,
                     Map<String, Set<String>> dimensionFields, Set<String> plateColorNameTables)
        {
            this.fullDimensionFilters = fullDimensionFilters;
            this.plateColorName = plateColorName;
            this.dimensionFields = dimensionFields;
            this.plateColorNameTables = plateColorNameTables;
        }

        static Capabilities none()
        {
            return new Capabilities(false, false,
                    Collections.<String, Set<String>>emptyMap(), Collections.<String>emptySet());
        }

        static Capabilities allSupported()
        {
            Map<String, Set<String>> fields = new LinkedHashMap<String, Set<String>>();
            Set<String> all = new HashSet<String>();
            all.addAll(CODE_DIMENSIONS);
            for (String table : ALL_TABLES)
            {
                fields.put(table, all);
            }
            return new Capabilities(true, true, fields, ALL_TABLES);
        }

        /** 全字段导出：该表是否支持维度编码/名称过滤。 */
        public boolean supportsDimension(String type)
        {
            if (!fullDimensionFilters || type == null)
            {
                return false;
            }
            Set<String> fields = dimensionFields.get(type);
            return fields != null && !fields.isEmpty();
        }

        /** 字段级校验：编码字段查能力矩阵；名称字段只要该表支持维度过滤即可（api 负责码表解析）。 */
        public boolean supportsDimensionField(String type, String field)
        {
            if (CODE_DIMENSIONS.contains(field))
            {
                Set<String> fields = dimensionFields.get(type);
                return fullDimensionFilters && fields != null && fields.contains(field);
            }
            if (NAME_DIMENSIONS.contains(field))
            {
                return supportsDimension(type);
            }
            return false;
        }

        /** 展示导出：该表是否已支持 plate_color_name 列。 */
        public boolean supportsPlateColorName(String type)
        {
            return plateColorName && plateColorNameTables.contains(type);
        }
    }
}
