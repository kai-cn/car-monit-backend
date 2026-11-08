package com.ruoyi.manager.service.bigscreen;

import com.alibaba.fastjson2.TypeReference;
import com.ruoyi.base.domain.DwdLcztFwqjcxx;
import com.ruoyi.base.domain.OdsSzdnGantry;
import com.ruoyi.base.domain.OdsSzdnSection;
import com.ruoyi.base.domain.OdsSzdnToll;
import com.ruoyi.base.service.IDwdLcztFwqjcxxService;
import com.ruoyi.base.service.IOdsSzdnGantryService;
import com.ruoyi.base.service.IOdsSzdnSectionService;
import com.ruoyi.base.service.IOdsSzdnTollService;
import com.ruoyi.base.service.IOdsYhglVBaseOrgService;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.cache.TwoLevelCache;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.domain.vo.bigscreen.OrgVO;
import com.ruoyi.manager.domain.vo.bigscreen.SectionVO;
import com.ruoyi.manager.domain.vo.bigscreen.TollGantryFwqVO;
import com.ruoyi.system.service.ISysDictDataService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * 大屏字典/小表缓存。TTL：L1 60s + L2 5 分钟 + stale 10 分钟。
 *
 * <p>主动失效：缓存 key 带 {@link DictVersionService} 版本段，字典写入后 INCR 版本号，
 * 各节点 5 秒内切换到新 key；Redis 不可用时退化为 TTL 失效。</p>
 *
 * <p>车牌颜色以 {@code sys_dict_data(dict_type=plate_color)} 为准，不再硬编码颜色枚举。</p>
 *
 * @author car-monit-backend-java-v3
 */
@Service
public class BigScreenDictService
{
    private static final long L1_SECONDS = 60L;

    private static final long L2_SECONDS = 300L;

    private static final long STALE_SECONDS = 600L;

    @Autowired
    private TwoLevelCache cache;

    @Autowired
    private IOdsSzdnSectionService odsSzdnSectionService;

    @Autowired
    private IOdsSzdnTollService tollService;

    @Autowired
    private IOdsSzdnGantryService gantryService;

    @Autowired
    private IDwdLcztFwqjcxxService fwqjcxxService;

    @Autowired
    private IOdsYhglVBaseOrgService baseOrgService;

    @Autowired
    private ISysDictDataService sysDictDataService;

    @Autowired
    private DictVersionService dictVersionService;

    public List<SectionVO> sectionList()
    {
        String key = cache.key("bigscreen:dict",
                dictVersionService.segment(DictVersionService.SECTION) + "sectionList");
        return cache.get(key, L1_SECONDS, L2_SECONDS, STALE_SECONDS,
                new TypeReference<List<SectionVO>>()
                {
                }.getType(), this::loadSectionList);
    }

    public List<TollGantryFwqVO> tollGantryFwqList(String sectionCode, String type)
    {
        String domain = "3".equals(type) ? DictVersionService.FWQ
                : ("2".equals(type) ? DictVersionService.GANTRY : DictVersionService.TOLL);
        String key = cache.key("bigscreen:dict",
                dictVersionService.segment(domain)
                        + "tollGantryFwq:" + BigScreenCacheSupport.hash(sectionCode, type));
        return cache.get(key, L1_SECONDS, L2_SECONDS, STALE_SECONDS,
                new TypeReference<List<TollGantryFwqVO>>()
                {
                }.getType(), () -> loadTollGantryFwqList(sectionCode, type));
    }

    public List<OrgVO> orgList()
    {
        String key = cache.key("bigscreen:dict",
                dictVersionService.segment(DictVersionService.ORG) + "orgList");
        return cache.get(key, L1_SECONDS, L2_SECONDS, STALE_SECONDS,
                new TypeReference<List<OrgVO>>()
                {
                }.getType(), this::loadOrgList);
    }

    /**
     * 路段编码 → 路段信息（供流水列表/导出做名称回填，避免每次查库）。
     */
    public Map<String, SectionVO> sectionMap()
    {
        String key = cache.key("bigscreen:dict",
                dictVersionService.segment(DictVersionService.SECTION) + "sectionMap");
        return cache.get(key, L1_SECONDS, L2_SECONDS, STALE_SECONDS,
                new TypeReference<Map<String, SectionVO>>()
                {
                }.getType(), this::loadSectionMap);
    }

    public Map<String, String> dictMap(String dictType)
    {
        String key = cache.key("bigscreen:dict",
                dictVersionService.segment(DictVersionService.SYS_DICT)
                        + "type:" + BigScreenCacheSupport.hash(dictType));
        return cache.get(key, L1_SECONDS, L2_SECONDS, STALE_SECONDS,
                new TypeReference<Map<String, String>>()
                {
                }.getType(), () -> sysDictDataService.selectDictDataMap(dictType));
    }

    /**
     * 车牌颜色码 → 名称，以 {@code sys_dict_data(dict_type=plate_color)} 为准。
     *
     * <p>字典缺失/查询失败时返回空 Map（调用方回退显示原始码并标记，不丢行）。</p>
     */
    public Map<String, String> plateColorMap()
    {
        try
        {
            Map<String, String> map = dictMap("plate_color");
            return map == null ? java.util.Collections.<String, String>emptyMap() : map;
        }
        catch (RuntimeException e)
        {
            return java.util.Collections.<String, String>emptyMap();
        }
    }

    /**
     * 解析车牌颜色名称：优先字典 label；未知码返回原始码且标记 {@code UNKNOWN}。
     */
    public PlateColorResult resolvePlateColor(String raw)
    {
        if (raw == null || raw.trim().isEmpty())
        {
            return new PlateColorResult("", false);
        }
        String code = raw.trim();
        Map<String, String> map = plateColorMap();
        String label = map.get(code);
        if (label != null && !label.trim().isEmpty())
        {
            return new PlateColorResult(label, true);
        }
        return new PlateColorResult(code, false);
    }

    /**
     * 车牌颜色解析结果：{@code unknown=true} 表示字典未命中（回退原始码）。
     */
    public static class PlateColorResult
    {
        private final String name;

        private final boolean known;

        public PlateColorResult(String name, boolean known)
        {
            this.name = name;
            this.known = known;
        }

        public String getName()
        {
            return name;
        }

        public boolean isKnown()
        {
            return known;
        }
    }

    private List<SectionVO> loadSectionList()
    {
        List<SectionVO> sections = odsSzdnSectionService.selectOdsSzdnSectionListNew(new OdsSzdnSection())
                .stream().map(item ->
                {
                    SectionVO sectionVO = new SectionVO();
                    sectionVO.setSectionCode(item.getSectionCode());
                    sectionVO.setSectionName(item.getSectionName());
                    return sectionVO;
                }).collect(Collectors.toList());

        List<SectionVO> result = new ArrayList<SectionVO>();
        SectionVO sectionAll = new SectionVO();
        sectionAll.setSectionCode(Constants.section_all);
        sectionAll.setSectionName("全部");
        result.add(sectionAll);
        result.addAll(sections);
        return result;
    }

    private List<TollGantryFwqVO> loadTollGantryFwqList(String rawSectionCode, String type)
    {
        if (CommonUtil.isBlank(rawSectionCode))
        {
            return new ArrayList<TollGantryFwqVO>();
        }
        String sectionCode = CommonUtil.deleteEnd(rawSectionCode);
        String[] split = sectionCode.split(",");
        List<String> sectionCodeList = Arrays.stream(split).collect(Collectors.toList());
        if (sectionCode.indexOf(Constants.section_all) > -1)
        {
            sectionCodeList = new ArrayList<String>();
        }

        if ("1".equals(type))
        {
            OdsSzdnToll query = new OdsSzdnToll();
            query.setSectionCodeList(sectionCodeList);
            return tollService.selectOdsSzdnTollListNew(query).stream().map(item ->
            {
                TollGantryFwqVO vo = new TollGantryFwqVO();
                vo.setType("1");
                vo.setCode(item.getTollCode());
                vo.setName(item.getTollName());
                return vo;
            }).collect(Collectors.toList());
        }
        if ("2".equals(type))
        {
            OdsSzdnGantry query = new OdsSzdnGantry();
            query.setSectionCodeList(sectionCodeList);
            return gantryService.selectOdsSzdnGantryListNew(query).stream().map(item ->
            {
                TollGantryFwqVO vo = new TollGantryFwqVO();
                vo.setType("2");
                vo.setCode(item.getGantryCode());
                vo.setName(item.getGantryName());
                return vo;
            }).collect(Collectors.toList());
        }
        if ("3".equals(type))
        {
            DwdLcztFwqjcxx query = new DwdLcztFwqjcxx();
            query.setSectionCodeList(sectionCodeList);
            return fwqjcxxService.selectDwdLcztFwqjcxxListNew(query).stream().map(item ->
            {
                TollGantryFwqVO vo = new TollGantryFwqVO();
                vo.setType("3");
                vo.setCode(item.getFwqbm());
                vo.setName(item.getFwqmc());
                return vo;
            }).collect(Collectors.toList());
        }
        return new ArrayList<TollGantryFwqVO>();
    }

    private List<OrgVO> loadOrgList()
    {
        return baseOrgService.lambdaQuery()
                .select(com.ruoyi.base.domain.OdsYhglVBaseOrg::getOrgCode,
                        com.ruoyi.base.domain.OdsYhglVBaseOrg::getOrgName)
                .list().stream().map(item ->
                {
                    OrgVO orgVO = new OrgVO();
                    orgVO.setOrgCode(item.getOrgCode());
                    orgVO.setOrgName(item.getOrgName());
                    return orgVO;
                }).collect(Collectors.toList());
    }

    private Map<String, SectionVO> loadSectionMap()
    {
        List<OdsSzdnSection> sections = odsSzdnSectionService.selectOdsSzdnSectionListNew(new OdsSzdnSection());
        Map<String, SectionVO> result = new java.util.HashMap<String, SectionVO>();
        if (sections != null)
        {
            for (OdsSzdnSection section : sections)
            {
                SectionVO vo = new SectionVO();
                vo.setSectionCode(section.getSectionCode());
                vo.setSectionName(section.getSectionName());
                vo.setRoadName(section.getRoadName());
                result.put(CommonUtil.isNull(section.getSectionCode()), vo);
            }
        }
        return result;
    }
}
