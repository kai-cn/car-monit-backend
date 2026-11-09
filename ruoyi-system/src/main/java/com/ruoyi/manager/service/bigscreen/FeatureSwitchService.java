package com.ruoyi.manager.service.bigscreen;

import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.utils.SecurityUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 灰度/回滚开关：Redis 运行期覆盖 + 配置文件默认值。
 *
 * <p>开关 key：{@code cm:{env}:switch:{name}}，值为 {@code on/off}（或 true/false）。
 * 读取带 10 秒本地缓存，避免每个请求都访问 Redis；未配置时回退 {@code bigscreen.switches.*}。</p>
 *
 * <p>用途：api 异常时无需重启即可把大屏路径切回本地兜底（statistics/warning/location/export/trail/dict-version）。</p>
 *
 * @author car-monit-backend-java-v3
 */
@Service
public class FeatureSwitchService
{
    private static final Logger log = LoggerFactory.getLogger(FeatureSwitchService.class);

    /** 开关名称常量，避免散落字符串 */
    public static final String STATS_API_FIRST = "stats-api-first";

    public static final String WARNING_API = "warning-api";

    public static final String LOCATION_INDEX = "location-index";

    public static final String EXPORT_V3 = "export-v3";

    public static final String DICT_VERSION = "dict-version";

    public static final String TRAIL_API = "trail-api";

    public static final String EXPORT_APPROVAL = "export-approval";

    /** 轨迹本地物化（Quartz 同步写 zdata_trail_tracks），默认关闭 */
    public static final String TRAIL_MATERIALIZE = "trail-materialize";

    private static final long LOCAL_TTL_MS = 10000L;

    @Value("${spring.profiles.active:dev}")
    private String env;

    @Autowired
    private RedisCache redisCache;

    @Autowired
    private GraySwitchProperties grayProperties;

    /** 配置文件默认值（Spring 绑定 bigscreen.switches.*，缺省为 true）。 */
    @Value("${bigscreen.switches.stats-api-first:true}")
    private boolean statsApiFirst;

    @Value("${bigscreen.switches.warning-api:true}")
    private boolean warningApi;

    @Value("${bigscreen.switches.location-index:true}")
    private boolean locationIndex;

    @Value("${bigscreen.switches.export-v3:true}")
    private boolean exportV3;

    @Value("${bigscreen.switches.dict-version:true}")
    private boolean dictVersion;

    @Value("${bigscreen.switches.trail-api:true}")
    private boolean trailApi;

    @Value("${bigscreen.switches.export-approval:false}")
    private boolean exportApproval;

    @Value("${bigscreen.switches.trail-materialize:false}")
    private boolean trailMaterialize;

    private final ConcurrentHashMap<String, CacheEntry> localCache =
            new ConcurrentHashMap<String, CacheEntry>();

    public boolean isEnabled(String name)
    {
        return isEnabled(name, currentTenantId());
    }

    /**
     * 按租户/百分比灰度判断：
     * <ol>
     *   <li>全局 Redis 覆盖（on/off）优先级最高；</li>
     *   <li>租户白名单非空时，仅名单内租户命中；</li>
     *   <li>百分比按 开关名+租户 稳定哈希放量；</li>
     *   <li>无灰度规则时回退配置默认值。</li>
     * </ol>
     */
    public boolean isEnabled(String name, String tenantId)
    {
        String cacheKey = name + "|" + (tenantId == null ? "" : tenantId);
        CacheEntry cached = localCache.get(cacheKey);
        long now = System.currentTimeMillis();
        if (cached != null && cached.expiresAt > now)
        {
            return cached.value;
        }
        boolean value = resolve(name, tenantId);
        localCache.put(cacheKey, new CacheEntry(value, now + LOCAL_TTL_MS));
        return value;
    }

    private boolean resolve(String name, String tenantId)
    {
        // 1) 全局覆盖
        Object global = readRedis("cm:" + env + ":switch:" + name);
        if (global != null)
        {
            return truthy(String.valueOf(global));
        }
        // 2) 灰度覆盖（Redis 优先，配置兜底）
        RuleState rule = resolveRule(name);
        if (rule != null)
        {
            if (!rule.tenants.isEmpty())
            {
                return tenantId != null && rule.tenants.contains(tenantId);
            }
            if (rule.percent <= 0)
            {
                return false;
            }
            if (rule.percent >= 100)
            {
                return true;
            }
            return bucket(name, tenantId) < rule.percent;
        }
        Boolean configured = defaults().get(name);
        return configured == null || configured;
    }

    private RuleState resolveRule(String name)
    {
        Object percentRaw = readRedis("cm:" + env + ":gray:" + name + ":percent");
        Object tenantsRaw = readRedis("cm:" + env + ":gray:" + name + ":tenants");
        if (percentRaw != null || tenantsRaw != null)
        {
            int percent = percentRaw == null ? 100 : parsePercent(String.valueOf(percentRaw));
            List<String> tenants = splitTenants(tenantsRaw == null ? null : String.valueOf(tenantsRaw));
            return new RuleState(percent, tenants);
        }
        if (grayProperties != null && grayProperties.getRules() != null)
        {
            GraySwitchProperties.Rule configured = grayProperties.getRules().get(name);
            if (configured != null)
            {
                return new RuleState(configured.getPercent(), configured.getTenants());
            }
        }
        return null;
    }

    private Object readRedis(String key)
    {
        try
        {
            return redisCache.getCacheObject(key);
        }
        catch (RuntimeException e)
        {
            log.warn("[开关] 读取 Redis 失败 key={} reason={}", key, e.getMessage());
            return null;
        }
    }

    private boolean truthy(String text)
    {
        String value = text == null ? "" : text.trim();
        return "on".equalsIgnoreCase(value) || "true".equalsIgnoreCase(value) || "1".equals(value);
    }

    private int parsePercent(String text)
    {
        try
        {
            int value = Integer.parseInt(text.trim());
            return Math.max(0, Math.min(100, value));
        }
        catch (NumberFormatException e)
        {
            return 100;
        }
    }

    private List<String> splitTenants(String csv)
    {
        List<String> result = new ArrayList<String>();
        if (csv == null || csv.trim().isEmpty())
        {
            return result;
        }
        for (String token : csv.split(","))
        {
            String trimmed = token.trim();
            if (!trimmed.isEmpty())
            {
                result.add(trimmed);
            }
        }
        return result;
    }

    /**
     * 稳定分桶：同一开关+租户始终得到同一个 0-99 值。
     */
    private int bucket(String name, String tenantId)
    {
        String key = name + "|" + (tenantId == null ? "anonymous" : tenantId);
        try
        {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(key.getBytes(StandardCharsets.UTF_8));
            // 首字节只有 0..255，%100 会让 0..55 出现 3 次、56..99 出现 2 次，
            // percent=50 的真实命中率约 58.6%。用 64 位哈希取模保证均匀。
            return (int) ((ByteBuffer.wrap(hash).getLong() & Long.MAX_VALUE) % 100L);
        }
        catch (Exception e)
        {
            return Math.floorMod(key.hashCode(), 100);
        }
    }

    /**
     * 运行期设置灰度：percent 0-100；tenants 非空时仅名单命中。
     */
    public void overrideGray(String name, int percent, String tenantsCsv)
    {
        int safePercent = Math.max(0, Math.min(100, percent));
        redisCache.setCacheObject("cm:" + env + ":gray:" + name + ":percent",
                String.valueOf(safePercent));
        if (tenantsCsv == null || tenantsCsv.trim().isEmpty())
        {
            redisCache.deleteObject("cm:" + env + ":gray:" + name + ":tenants");
        }
        else
        {
            redisCache.setCacheObject("cm:" + env + ":gray:" + name + ":tenants",
                    tenantsCsv.trim());
        }
        clearLocalCache(name);
        log.info("[开关] 灰度覆盖 {} percent={} tenants={}", name, safePercent, tenantsCsv);
    }

    public void clearGray(String name)
    {
        redisCache.deleteObject("cm:" + env + ":gray:" + name + ":percent");
        redisCache.deleteObject("cm:" + env + ":gray:" + name + ":tenants");
        clearLocalCache(name);
        log.info("[开关] 清除灰度覆盖 {}", name);
    }

    private void clearLocalCache(String name)
    {
        localCache.keySet().removeIf(key -> key.startsWith(name + "|"));
    }

    private String currentTenantId()
    {
        try
        {
            Long tenantId = SecurityUtils.getTenantId();
            return tenantId == null ? null : String.valueOf(tenantId);
        }
        catch (RuntimeException e)
        {
            return null;
        }
    }

    /** 运行期覆盖（写 Redis + 清理本地缓存）。 */
    public boolean override(String name, boolean enabled)
    {
        redisCache.setCacheObject(key(name), enabled ? "on" : "off");
        clearLocalCache(name);
        log.info("[开关] 运行期覆盖 {}={}", name, enabled);
        return enabled;
    }

    public void clearOverride(String name)
    {
        redisCache.deleteObject(key(name));
        clearLocalCache(name);
        log.info("[开关] 清除运行期覆盖 {}", name);
    }

    public Map<String, Boolean> snapshot()
    {
        Map<String, Boolean> result = new LinkedHashMap<String, Boolean>();
        result.put(STATS_API_FIRST, isEnabled(STATS_API_FIRST));
        result.put(WARNING_API, isEnabled(WARNING_API));
        result.put(LOCATION_INDEX, isEnabled(LOCATION_INDEX));
        result.put(EXPORT_V3, isEnabled(EXPORT_V3));
        result.put(DICT_VERSION, isEnabled(DICT_VERSION));
        result.put(TRAIL_API, isEnabled(TRAIL_API));
        result.put(EXPORT_APPROVAL, isEnabled(EXPORT_APPROVAL));
        result.put(TRAIL_MATERIALIZE, isEnabled(TRAIL_MATERIALIZE));
        return result;
    }

    /** 当前灰度规则快照（percent/tenants），供运维排查。 */
    public Map<String, Object> graySnapshot()
    {
        Map<String, Object> result = new LinkedHashMap<String, Object>();
        for (String name : snapshot().keySet())
        {
            RuleState rule = resolveRule(name);
            if (rule != null)
            {
                Map<String, Object> item = new LinkedHashMap<String, Object>();
                item.put("percent", rule.percent);
                item.put("tenants", rule.tenants);
                result.put(name, item);
            }
        }
        return result;
    }

    public Map<String, Boolean> defaults()
    {
        Map<String, Boolean> result = new LinkedHashMap<String, Boolean>();
        result.put(STATS_API_FIRST, statsApiFirst);
        result.put(WARNING_API, warningApi);
        result.put(LOCATION_INDEX, locationIndex);
        result.put(EXPORT_V3, exportV3);
        result.put(DICT_VERSION, dictVersion);
        result.put(TRAIL_API, trailApi);
        result.put(EXPORT_APPROVAL, exportApproval);
        result.put(TRAIL_MATERIALIZE, trailMaterialize);
        return result;
    }

    private boolean resolve(String name)
    {
        try
        {
            Object raw = redisCache.getCacheObject(key(name));
            if (raw != null)
            {
                String text = String.valueOf(raw).trim();
                return "on".equalsIgnoreCase(text) || "true".equalsIgnoreCase(text)
                        || "1".equals(text);
            }
        }
        catch (RuntimeException e)
        {
            log.warn("[开关] 读取 Redis 覆盖失败 name={} reason={}", name, e.getMessage());
        }
        Boolean configured = defaults().get(name);
        return configured == null || configured;
    }

    private String key(String name)
    {
        return "cm:" + env + ":switch:" + name;
    }

    private static class CacheEntry
    {
        private final boolean value;
        private final long expiresAt;

        CacheEntry(boolean value, long expiresAt)
        {
            this.value = value;
            this.expiresAt = expiresAt;
        }
    }

    private static class RuleState
    {
        private final int percent;
        private final List<String> tenants;

        RuleState(int percent, List<String> tenants)
        {
            this.percent = percent;
            this.tenants = tenants == null ? new ArrayList<String>() : tenants;
        }
    }
}
