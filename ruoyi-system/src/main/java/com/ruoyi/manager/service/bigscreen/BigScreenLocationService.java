package com.ruoyi.manager.service.bigscreen;

import com.alibaba.fastjson2.TypeReference;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.cache.CacheContext;
import com.ruoyi.common.core.cache.TwoLevelCache;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.domain.CarInfo;
import com.ruoyi.manager.domain.vo.bigscreen.CarLocationParam;
import com.ruoyi.manager.domain.vo.bigscreen.CarLocationVO;
import com.ruoyi.manager.service.ICarInfoService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 大屏地图点位查询：基于 Redis 车辆快照建立倒排索引 + 结果级两级缓存，消除每次请求的 O(N) 过滤。
 *
 * <p>索引只在快照版本（{@link Constants#car_list_version}）变化时重建；查询按「最小候选集」求交，
 * 常见筛选条件从 O(N) 降为 O(候选集)。carNo 无精确命中时回退一次子串扫描，保持原有 contains 语义。</p>
 *
 * <p>缓存 TTL：L1 5s / L2 10s / stale 20s（设计文档 §5.4.4）。</p>
 *
 * @author car-monit-backend-java-v3
 */
@Service
public class BigScreenLocationService
{
    private static final Logger log = LoggerFactory.getLogger(BigScreenLocationService.class);

    private static final long L1_SECONDS = 5L;

    private static final long L2_SECONDS = 10L;

    private static final long STALE_SECONDS = 20L;

    @Autowired
    private TwoLevelCache cache;

    @Autowired
    private RedisCache redisCache;

    @Autowired
    private ICarInfoService carInfoService;

    @Autowired
    private FeatureSwitchService featureSwitchService;

    private volatile Snapshot snapshot;

    public List<CarLocationVO> carLocation(final CarLocationParam param)
    {
        if (!featureSwitchService.isEnabled(FeatureSwitchService.LOCATION_INDEX))
        {
            // 回滚路径：关闭索引，按旧逻辑逐条过滤（仍走结果缓存）
            CacheContext.markDegrade("SWITCH_LOCATION_INDEX_OFF");
            return carLocationByScan(param);
        }
        Snapshot current = currentSnapshot();
        String key = cache.key("bigscreen:location",
                current.version + ":" + BigScreenCacheSupport.hash(param.getRoadCode(),
                        param.getSectionCode(), param.getTollCode(), param.getGantryCode(),
                        param.getFwqbm(), param.getEscapedType(), param.getCarNoQuery()));
        return cache.get(key, L1_SECONDS, L2_SECONDS, STALE_SECONDS,
                new TypeReference<List<CarLocationVO>>()
                {
                }.getType(), () -> filter(current, param));
    }

    private Snapshot currentSnapshot()
    {
        String version = readVersion();
        Snapshot current = snapshot;
        if (current != null && current.version.equals(version))
        {
            return current;
        }
        synchronized (this)
        {
            current = snapshot;
            if (current != null && current.version.equals(version))
            {
                return current;
            }
            try
            {
                List<CarInfo> cars = carInfoService.getRedisCarList();
                Snapshot rebuilt = build(version, cars);
                snapshot = rebuilt;
                return rebuilt;
            }
            catch (RuntimeException e)
            {
                if (current != null)
                {
                    log.warn("[地图点位] 快照重建失败，沿用上一版本 version={} reason={}",
                            current.version, e.getMessage());
                    CacheContext.markDegrade("CAR_SNAPSHOT_STALE");
                    return current;
                }
                throw e;
            }
        }
    }

    private String readVersion()
    {
        try
        {
            Object version = redisCache.getCacheObject(Constants.car_list_version);
            if (version != null && !String.valueOf(version).trim().isEmpty())
            {
                return String.valueOf(version);
            }
        }
        catch (RuntimeException e)
        {
            log.warn("[地图点位] 读取快照版本失败: {}", e.getMessage());
            CacheContext.markDegrade("REDIS_UNAVAILABLE");
        }
        Snapshot current = snapshot;
        return current == null ? "0" : current.version;
    }

    private Snapshot build(String version, List<CarInfo> cars)
    {
        List<Item> items = new ArrayList<Item>();
        Map<String, Item> itemById = new LinkedHashMap<String, Item>();
        Map<String, List<String>> codeIndex = new HashMap<String, List<String>>();
        Map<String, List<String>> escapedIndex = new HashMap<String, List<String>>();
        Map<String, List<String>> carNoIndex = new HashMap<String, List<String>>();

        if (cars != null)
        {
            for (CarInfo car : cars)
            {
                if (!"1".equals(CommonUtil.isNull(car.getStatus())))
                {
                    continue;
                }
                CarLocationVO vo = toVo(car);
                Item item = new Item(vo, CommonUtil.isNull(car.getGantryCode()),
                        CommonUtil.isNull(car.getEscapedType()), CommonUtil.isNull(car.getCarNo()));
                items.add(item);
                itemById.put(vo.getId(), item);
                indexTokens(codeIndex, item.gantryCode, vo.getId());
                indexTokens(escapedIndex, item.escapedType, vo.getId());
                indexTokens(carNoIndex, item.carNo, vo.getId());
            }
        }
        return new Snapshot(version, items, itemById, codeIndex, escapedIndex, carNoIndex);
    }

    private void indexTokens(Map<String, List<String>> index, String raw, String id)
    {
        if (raw == null || raw.trim().isEmpty())
        {
            return;
        }
        String[] tokens = raw.split(",");
        for (String token : tokens)
        {
            String trimmed = token.trim();
            if (trimmed.isEmpty())
            {
                continue;
            }
            List<String> ids = index.get(trimmed);
            if (ids == null)
            {
                ids = new ArrayList<String>();
                index.put(trimmed, ids);
            }
            ids.add(id);
        }
    }

    /**
     * 回滚路径：不使用倒排索引，按旧语义逐条过滤（O(N)），仍然走结果级缓存。
     */
    private List<CarLocationVO> carLocationByScan(final CarLocationParam param)
    {
        Snapshot current = currentSnapshot();
        String key = cache.key("bigscreen:location",
                current.version + ":scan:" + BigScreenCacheSupport.hash(param.getRoadCode(),
                        param.getSectionCode(), param.getTollCode(), param.getGantryCode(),
                        param.getFwqbm(), param.getEscapedType(), param.getCarNoQuery()));
        return cache.get(key, L1_SECONDS, L2_SECONDS, STALE_SECONDS,
                new TypeReference<List<CarLocationVO>>()
                {
                }.getType(), () -> scanFilter(current, param));
    }

    private List<CarLocationVO> scanFilter(Snapshot snapshot, CarLocationParam param)
    {
        List<CarLocationVO> result = new ArrayList<CarLocationVO>();
        for (Item item : snapshot.items)
        {
            if (!matchCode(item.gantryCode, param.getRoadCode())
                    || !matchCode(item.gantryCode, param.getSectionCode())
                    || !matchCode(item.gantryCode, param.getTollCode())
                    || !matchCode(item.gantryCode, param.getGantryCode())
                    || !matchCode(item.gantryCode, param.getFwqbm())
                    || !matchCode(item.escapedType, param.getEscapedType())
                    || !matchCode(item.carNo, param.getCarNoQuery()))
            {
                continue;
            }
            result.add(item.vo);
        }
        return result;
    }

    private boolean matchCode(String target, String value)
    {
        if (CommonUtil.isBlank(value))
        {
            return true;
        }
        return target != null && CommonUtil.isExitsStr(target, value);
    }

    private List<CarLocationVO> filter(Snapshot snapshot, CarLocationParam param)
    {
        List<String> candidates = null;
        candidates = intersect(candidates, codeCandidates(snapshot, param.getRoadCode()));
        candidates = intersect(candidates, codeCandidates(snapshot, param.getSectionCode()));
        candidates = intersect(candidates, codeCandidates(snapshot, param.getTollCode()));
        candidates = intersect(candidates, codeCandidates(snapshot, param.getGantryCode()));
        candidates = intersect(candidates, codeCandidates(snapshot, param.getFwqbm()));
        candidates = intersect(candidates, escapedCandidates(snapshot, param.getEscapedType()));
        candidates = intersect(candidates, carNoCandidates(snapshot, param.getCarNoQuery()));

        if (candidates == null)
        {
            return all(snapshot);
        }
        List<CarLocationVO> result = new ArrayList<CarLocationVO>(candidates.size());
        for (String id : candidates)
        {
            Item item = snapshot.itemById.get(id);
            if (item != null)
            {
                result.add(item.vo);
            }
        }
        return result;
    }

    private List<CarLocationVO> all(Snapshot snapshot)
    {
        List<CarLocationVO> result = new ArrayList<CarLocationVO>(snapshot.items.size());
        for (Item item : snapshot.items)
        {
            result.add(item.vo);
        }
        return result;
    }

    private List<String> codeCandidates(Snapshot snapshot, String value)
    {
        if (CommonUtil.isBlank(value))
        {
            return null;
        }
        List<String> hits = unionTokens(snapshot.codeIndex, value);
        if (hits.isEmpty())
        {
            hits = scan(snapshot, value, Field.CODE);
        }
        return hits;
    }

    private List<String> escapedCandidates(Snapshot snapshot, String value)
    {
        if (CommonUtil.isBlank(value))
        {
            return null;
        }
        List<String> hits = unionTokens(snapshot.escapedIndex, value);
        if (hits.isEmpty())
        {
            hits = scan(snapshot, value, Field.ESCAPED);
        }
        return hits;
    }

    private List<String> carNoCandidates(Snapshot snapshot, String value)
    {
        if (CommonUtil.isBlank(value))
        {
            return null;
        }
        List<String> hits = unionTokens(snapshot.carNoIndex, value);
        if (hits.isEmpty())
        {
            hits = scan(snapshot, value, Field.CAR_NO);
        }
        return hits;
    }

    private List<String> unionTokens(Map<String, List<String>> index, String raw)
    {
        Set<String> union = new LinkedHashSet<String>();
        for (String token : CommonUtil.deleteEnd(raw).split(","))
        {
            String trimmed = token.trim();
            if (trimmed.isEmpty())
            {
                continue;
            }
            List<String> ids = index.get(trimmed);
            if (ids != null)
            {
                union.addAll(ids);
            }
        }
        return new ArrayList<String>(union);
    }

    private List<String> scan(Snapshot snapshot, String value, Field field)
    {
        List<String> hits = new ArrayList<String>();
        for (Item item : snapshot.items)
        {
            String target = field == Field.CODE ? item.gantryCode
                    : (field == Field.ESCAPED ? item.escapedType : item.carNo);
            if (CommonUtil.isExitsStr(target, value))
            {
                hits.add(item.vo.getId());
            }
        }
        return hits;
    }

    private List<String> intersect(List<String> current, List<String> next)
    {
        if (next == null)
        {
            return current;
        }
        if (current == null)
        {
            return next;
        }
        List<String> base = current.size() <= next.size() ? current : next;
        Set<String> other = new LinkedHashSet<String>(current.size() <= next.size() ? next : current);
        List<String> result = new ArrayList<String>();
        for (String id : base)
        {
            if (other.contains(id))
            {
                result.add(id);
            }
        }
        return result;
    }

    private CarLocationVO toVo(CarInfo car)
    {
        CarLocationVO vo = new CarLocationVO();
        vo.setId(car.getId());
        vo.setCarNo(car.getCarNo());
        vo.setCarType(car.getCarType());
        vo.setLonStr(car.getLastPassLongitude());
        vo.setLatStr(car.getLastPassLatitude());
        vo.setLastPassType(car.getLastPassType());
        if (CommonUtil.isNotBlank(vo.getLonStr()))
        {
            vo.setLon(new BigDecimal(vo.getLonStr()));
        }
        if (CommonUtil.isNotBlank(vo.getLatStr()))
        {
            vo.setLat(new BigDecimal(vo.getLatStr()));
        }
        vo.setStatus(car.getStatus());
        return vo;
    }

    private enum Field
    {
        CODE, ESCAPED, CAR_NO
    }

    private static class Item
    {
        private final CarLocationVO vo;
        private final String gantryCode;
        private final String escapedType;
        private final String carNo;

        Item(CarLocationVO vo, String gantryCode, String escapedType, String carNo)
        {
            this.vo = vo;
            this.gantryCode = gantryCode;
            this.escapedType = escapedType;
            this.carNo = carNo;
        }
    }

    private static class Snapshot
    {
        private final String version;
        private final List<Item> items;
        private final Map<String, Item> itemById;
        private final Map<String, List<String>> codeIndex;
        private final Map<String, List<String>> escapedIndex;
        private final Map<String, List<String>> carNoIndex;

        Snapshot(String version, List<Item> items, Map<String, Item> itemById,
                 Map<String, List<String>> codeIndex, Map<String, List<String>> escapedIndex,
                 Map<String, List<String>> carNoIndex)
        {
            this.version = version;
            this.items = items;
            this.itemById = itemById;
            this.codeIndex = codeIndex;
            this.escapedIndex = escapedIndex;
            this.carNoIndex = carNoIndex;
        }
    }
}
