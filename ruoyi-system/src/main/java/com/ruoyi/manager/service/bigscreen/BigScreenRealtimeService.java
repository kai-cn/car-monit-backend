package com.ruoyi.manager.service.bigscreen;

import com.alibaba.fastjson2.TypeReference;
import com.ruoyi.common.core.cache.CacheContext;
import com.ruoyi.common.core.cache.TwoLevelCache;
import com.ruoyi.integration.api.ApiClientException;
import com.ruoyi.integration.api.TrafficApiClient;
import com.ruoyi.manager.domain.CarSuspicious;
import com.ruoyi.manager.domain.CarWarningInfo;
import com.ruoyi.manager.domain.vo.bigscreen.CarInfoVO;
import com.ruoyi.manager.domain.vo.bigscreen.CarLocationParam;
import com.ruoyi.manager.service.ICarInfoService;
import com.ruoyi.manager.service.ICarSuspiciousService;
import com.ruoyi.manager.service.ICarWarningInfoService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 大屏实时列表与小结果查询：实时列表走 api（ES），失败回退 Redis 快照；
 * exceptionCar / carVoList 走短 TTL 缓存。
 *
 * @author car-monit-backend-java-v3
 */
@Service
public class BigScreenRealtimeService
{
    private static final Logger log = LoggerFactory.getLogger(BigScreenRealtimeService.class);

    private static final long L1_SECONDS = 10L;

    private static final long L2_SECONDS = 30L;

    private static final long STALE_SECONDS = 60L;

    private static final int WARNING_LIMIT = 100;

    @Autowired
    private TwoLevelCache cache;

    @Autowired
    private TrafficApiClient trafficApiClient;

    @Autowired
    private ICarWarningInfoService carWarningInfoService;

    @Autowired
    private ICarSuspiciousService carSuspiciousService;

    @Autowired
    private ICarInfoService carInfoService;

    @Autowired
    private FeatureSwitchService featureSwitchService;

    @Autowired
    private BigScreenDictService bigScreenDictService;

    public List<CarWarningInfo> carWarning(final CarLocationParam param)
    {
        String key = cache.key("bigscreen:realtime", "warning:" + BigScreenCacheSupport.hash(
                param.getRoadCode(), param.getSectionCode(), param.getTollCode(),
                param.getGantryCode(), param.getFwqbm(), param.getEscapedType(),
                param.getCarNoQuery()));
        return cache.get(key, L1_SECONDS, L2_SECONDS, STALE_SECONDS,
                new TypeReference<List<CarWarningInfo>>()
                {
                }.getType(), () -> loadWarning(param));
    }

    public List<CarSuspicious> exceptionCar()
    {
        String key = cache.key("bigscreen:realtime", "exceptionCar");
        return cache.get(key, L1_SECONDS, L2_SECONDS, STALE_SECONDS,
                new TypeReference<List<CarSuspicious>>()
                {
                }.getType(), () -> carSuspiciousService.selectCarSuspiciousListLimit10());
    }

    public List<CarInfoVO> carVoList()
    {
        String key = cache.key("bigscreen:realtime", "carVoList");
        return cache.get(key, L1_SECONDS, L2_SECONDS, STALE_SECONDS,
                new TypeReference<List<CarInfoVO>>()
                {
                }.getType(), () -> carInfoService.selectCarVoList());
    }

    private List<CarWarningInfo> loadWarning(CarLocationParam param)
    {
        // 旧语义：type 选中但未选具体编码时，用 StationCapture/GantryCapture/ServiceAreaCapture
        // 作为“抓拍类型”过滤；ES car-warning 索引没有 capture_type 字段，精确 term 会误查为空。
        // 另外 api 的过滤参数均为单值 term，旧接口允许多值逗号串（如 sectionCode 多选）。
        // 这两类请求保留 Redis 快照过滤，避免语义退化；待 api 增加 captureType/terms 过滤后再切换。
        if (!featureSwitchService.isEnabled(FeatureSwitchService.WARNING_API))
        {
            CacheContext.markDegrade("SWITCH_WARNING_API_OFF");
            CacheContext.markSource("REDIS_SNAPSHOT");
            return enrichPlateColor(carWarningInfoService.selectCarWarningInfoListLimit100(param));
        }
        try
        {
            // api 契约：多值为 terms、captureType 哨兵由 api 解析；索引缺失/无数据 200+[]，
            // ES 不可达 503 才走 Redis 快照降级。
            List<CarWarningInfo> rows = trafficApiClient.warningList(
                    trimListValue(param.getRoadCode()), trimListValue(param.getSectionCode()),
                    trimListValue(param.getTollCode()), trimListValue(param.getGantryCode()),
                    trimListValue(param.getFwqbm()), trimListValue(param.getEscapedType()),
                    trimListValue(param.getCarNoQuery()), WARNING_LIMIT);
            CacheContext.markSource("API");
            return enrichPlateColor(rows);
        }
        catch (ApiClientException e)
        {
            log.warn("[大屏预警] api 不可用，回退 Redis 快照 code={} msg={}", e.getCode(), e.getMessage());
            CacheContext.markDegrade(e.getCode().name());
            CacheContext.markSource("REDIS_SNAPSHOT");
            return enrichPlateColor(carWarningInfoService.selectCarWarningInfoListLimit100(param));
        }
    }

    /**
     * 车牌颜色名称以字典 plate_color 为准；未知码保留原始值并标记 UNKNOWN，不丢行。
     */
    private List<CarWarningInfo> enrichPlateColor(List<CarWarningInfo> rows)
    {
        if (rows == null || rows.isEmpty())
        {
            return rows;
        }
        for (CarWarningInfo row : rows)
        {
            BigScreenDictService.PlateColorResult color =
                    bigScreenDictService.resolvePlateColor(row.getPlateColor());
            row.setPlateColorName(color.getName());
            if (!color.isKnown() && !color.getName().isEmpty())
            {
                row.setPlateColorMark("UNKNOWN");
            }
        }
        return rows;
    }

    private String trimListValue(String value)
    {
        if (value == null)
        {
            return null;
        }
        String trimmed = value.trim();
        while (trimmed.endsWith(","))
        {
            trimmed = trimmed.substring(0, trimmed.length() - 1).trim();
        }
        return trimmed;
    }
}
