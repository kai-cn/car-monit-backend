package com.ruoyi.manager.service.bigscreen;

import com.alibaba.fastjson2.TypeReference;
import com.ruoyi.base.service.IOdsRtSzdnSnapshotFlowAddcodeService;
import com.ruoyi.common.core.cache.CacheContext;
import com.ruoyi.common.core.cache.TwoLevelCache;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.integration.api.ApiClientException;
import com.ruoyi.integration.api.TrafficApiClient;
import com.ruoyi.integration.api.TrafficQueryContract;
import com.ruoyi.manager.domain.vo.bigscreen.CarAuditVO;
import com.ruoyi.manager.domain.vo.bigscreen.CarStatisticsVO;
import com.ruoyi.manager.domain.vo.bigscreen.IncomeStatisticParam;
import com.ruoyi.manager.domain.vo.bigscreen.TopTenVO;
import com.ruoyi.manager.domain.vo.bigscreen.incomeStatisticVO;
import com.ruoyi.manager.service.ICarAduitFreeService;
import com.ruoyi.manager.service.ICarConfimFreeService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Supplier;

/**
 * 大屏统计 facade：预聚合/API 优先 + 两级缓存 + legacy 兜底 + 分级降级。
 *
 * <p>缓存 TTL：L1 10s / L2 60s / stale 120s，覆盖大屏 30-60s 轮询；缓存 key 含全部查询参数，
 * 禁止跨组织/跨筛选条件复用。</p>
 *
 * <p>模式配置 {@code bigscreen.stats.mode}：api（只走 api）、legacy（只走本地业务表）、
 * hybrid（默认，api 优先，404/超时/5xx 时回退 legacy 并标记 X-Degrade）。</p>
 *
 * @author car-monit-backend-java-v3
 */
@Service
public class BigScreenStatsService
{
    private static final Logger log = LoggerFactory.getLogger(BigScreenStatsService.class);

    private static final long L1_SECONDS = 10L;

    private static final long L2_SECONDS = 60L;

    private static final long STALE_SECONDS = 120L;

    @Value("${bigscreen.stats.mode:hybrid}")
    private String mode;

    @Autowired
    private TwoLevelCache cache;

    @Autowired
    private TrafficApiClient trafficApiClient;

    @Autowired
    private ICarConfimFreeService carConfimFreeService;

    @Autowired
    private ICarAduitFreeService carAduitFreeService;

    @Autowired
    private IOdsRtSzdnSnapshotFlowAddcodeService snapshotFlowAddcodeService;

    @Autowired
    private FeatureSwitchService featureSwitchService;

    public List<CarStatisticsVO> carStatistics(final IncomeStatisticParam param)
    {
        if (!apiFirstEnabled())
        {
            CacheContext.markSource("LEGACY_DB");
            return carConfimFreeService.getCarStatistics(param);
        }
        String key = cache.key("bigscreen:stats", "carStatistics:" + BigScreenCacheSupport.hash(
                param.getApplyTime1(), param.getApplyTime2(), param.getOrgId(), param.getEscapedType()));
        return cache.get(key, L1_SECONDS, L2_SECONDS, STALE_SECONDS,
                new TypeReference<List<CarStatisticsVO>>()
                {
                }.getType(),
                () -> withFallback("carStatistics",
                        () -> loadEscapeStatistics(param),
                        () -> carConfimFreeService.getCarStatistics(param)));
    }

    public CarAuditVO carAudit(final IncomeStatisticParam param)
    {
        if (!apiFirstEnabled())
        {
            CacheContext.markSource("LEGACY_DB");
            return loadLegacyCarAudit(param);
        }
        String key = cache.key("bigscreen:stats", "carAudit:" + BigScreenCacheSupport.hash(
                param.getApplyTime1(), param.getApplyTime2()));
        return cache.get(key, L1_SECONDS, L2_SECONDS, STALE_SECONDS,
                CarAuditVO.class,
                () -> withFallback("carAudit",
                        () -> trafficApiClient.auditStatistics(param),
                        () -> loadLegacyCarAudit(param)));
    }

    public List<incomeStatisticVO> incomeStatistic(final IncomeStatisticParam param)
    {
        if (CommonUtil.isBlank(param.getQueryDateType()))
        {
            param.setQueryDateType("suo");
        }
        if (!apiFirstEnabled())
        {
            CacheContext.markSource("LEGACY_DB");
            return carAduitFreeService.incomeStatistic(param);
        }
        // api 的 income 端点按 yyyy-MM-dd 解析 startDate；兼容前端传 yyyy-MM 的月份口径
        String startDate = param.getStartDate();
        if (startDate != null && startDate.trim().matches("\\d{4}-\\d{2}"))
        {
            param.setStartDate(startDate.trim() + "-01");
        }
        String key = cache.key("bigscreen:stats", "income:" + BigScreenCacheSupport.hash(
                param.getQueryDateType(), param.getStartDate(),
                param.getApplyTime1(), param.getApplyTime2()));
        return cache.get(key, L1_SECONDS, L2_SECONDS, STALE_SECONDS,
                new TypeReference<List<incomeStatisticVO>>()
                {
                }.getType(),
                () -> withFallback("incomeStatistic",
                        () -> trafficApiClient.incomeStatistics(param),
                        () -> carAduitFreeService.incomeStatistic(param)));
    }

    public List<TopTenVO> topTen(String startTime, String endTime)
    {
        final String[] range = TrafficQueryContract.normalizeDateRange(startTime, endTime);
        if (!apiFirstEnabled())
        {
            CacheContext.markSource("LEGACY_DB");
            return snapshotFlowAddcodeService.getTopTen(range[0], range[1]);
        }
        String key = cache.key("bigscreen:stats",
                "topTen:" + BigScreenCacheSupport.hash(range[0], range[1]));
        return cache.get(key, L1_SECONDS, L2_SECONDS, STALE_SECONDS,
                new TypeReference<List<TopTenVO>>()
                {
                }.getType(),
                () -> withFallback("topTen",
                        () -> trafficApiClient.warningTop(range[0], range[1], 10),
                        () -> snapshotFlowAddcodeService.getTopTen(range[0], range[1])));
    }

    /**
     * api 优先是否开启：模式非 legacy 且运行期开关（含租户灰度）允许。
     * 关闭时统计方法直接走 legacy，不再读缓存，保证一键回退即时生效。
     */
    private boolean apiFirstEnabled()
    {
        return !"legacy".equalsIgnoreCase(mode)
                && featureSwitchService.isEnabled(FeatureSwitchService.STATS_API_FIRST);
    }

    private <T> T withFallback(String endpoint, Supplier<T> apiCall, Supplier<T> legacyCall)
    {
        if (!apiFirstEnabled())
        {
            CacheContext.markSource("LEGACY_DB");
            return legacyCall.get();
        }
        try
        {
            T value = apiCall.get();
            CacheContext.markSource("API");
            return value;
        }
        catch (ApiClientException e)
        {
            if ("api".equalsIgnoreCase(mode)
                    || e.getCode() == com.ruoyi.integration.api.ApiErrorCode.INVALID_ARGUMENT
                    || e.getCode() == com.ruoyi.integration.api.ApiErrorCode.UNAUTHORIZED
                    || e.getCode() == com.ruoyi.integration.api.ApiErrorCode.FORBIDDEN)
            {
                throw e;
            }
            log.warn("[大屏统计] api 不可用，回退 legacy endpoint={} code={} msg={}",
                    endpoint, e.getCode(), e.getMessage());
            CacheContext.markDegrade(e.getCode().name());
            CacheContext.markSource("LEGACY_DB");
            return legacyCall.get();
        }
    }

    private CarAuditVO loadLegacyCarAudit(IncomeStatisticParam param)
    {
        CarAuditVO vo = new CarAuditVO();
        CarStatisticsVO escaped = carAduitFreeService.getCarAudit(param);
        if (escaped != null)
        {
            vo.setTotalAmount(escaped.getEscapedAmount());
            vo.setTotalCount(escaped.getNumber());
        }
        CarStatisticsVO confirmed = carConfimFreeService.getCarConfirm(param);
        if (confirmed != null)
        {
            vo.setFinishedAmount(confirmed.getEscapedAmount());
            vo.setFinishedCount(confirmed.getNumber());
        }
        return vo;
    }

    /**
     * api 的 escape 端点固定返回 5 种类型（无数据补 0）；带 escapedType 过滤时按 legacy 语义收窄，
     * 避免前端筛选某一类型时仍收到其他类型的 0 值行。
     */
    private List<CarStatisticsVO> loadEscapeStatistics(IncomeStatisticParam param)
    {
        List<CarStatisticsVO> rows = trafficApiClient.escapeStatistics(param);
        String escapedType = param.getEscapedType();
        if (CommonUtil.isBlank(escapedType))
        {
            return rows;
        }
        List<CarStatisticsVO> filtered = new ArrayList<CarStatisticsVO>();
        for (CarStatisticsVO row : rows)
        {
            if (!escapedType.trim().equals(row.getEscapedType()))
            {
                continue;
            }
            boolean empty = (row.getNumber() == null || row.getNumber() == 0)
                    && (row.getEscapedAmount() == null
                            || row.getEscapedAmount().compareTo(java.math.BigDecimal.ZERO) == 0);
            if (!empty)
            {
                filtered.add(row);
            }
        }
        return filtered;
    }
}
