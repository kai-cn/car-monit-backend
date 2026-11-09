package com.ruoyi.manager.service.bigscreen;

import com.ruoyi.integration.api.ApiClientException;
import com.ruoyi.integration.api.ApiErrorCode;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 导出字段与路径策略。
 *
 * <p>展示字段路径只允许 ES 中保留的轻量字段，明确拒绝轨迹点与大文本；
 * 全字段路径不做字段限制，但要求用途说明与权限。</p>
 *
 * @author car-monit-backend-java-v3
 */
public final class ExportPolicy
{
    public static final String MODE_DISPLAY = "display";

    public static final String MODE_FULL = "full";

    private static final int MAX_DISPLAY_FIELDS = 60;

    private static final Set<String> BLOCKED_DISPLAY_FIELDS = new HashSet<String>(Arrays.asList(
            "trailpoints", "trailPoints", "trackJosn", "trackJson", "snappicturepath",
            "reserve1", "reserve2", "reserve3", "reserve4", "reserve5"));

    private static final List<String> SNAPSHOT_DISPLAY_FIELDS = Arrays.asList(
            "big_id", "snapshottime", "platenumber", "platecolor", "platecolorcode",
            "orgcode", "orgname", "sectioncode", "sectionname", "roadcode", "roadname",
            "gantrycode", "gantryname", "tollcode", "tollname", "direction", "pileno",
            "lon", "lat", "cartype", "cartypecode", "carcolor");

    private static final List<String> FEE_DISPLAY_FIELDS = Arrays.asList(
            "big_id", "vehicleplate", "plate_core", "plate_color_code", "plate_color_raw",
            "plate_parse_status", "transtime", "gantryid", "gantryname", "sectioncode",
            "sectionname", "orgcode", "orgname", "fee", "payfee", "axlecount", "passstate",
            "entollstationid", "extollstationid");

    private static final List<String> TRAIL_DISPLAY_FIELDS = Arrays.asList(
            "cid", "envehicleid", "entime", "extime", "entollstationid", "entollstationname",
            "extollstationid", "extollstationname", "trailtype", "point_count",
            "route_sections", "route_gantries");

    private ExportPolicy()
    {
    }

    public static String validateMode(String type, String mode)
    {
        if (type == null || !Arrays.asList("snapshot", "fee", "trail").contains(type))
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "export",
                    "导出类型非法，仅支持 snapshot/fee/trail: " + type);
        }
        if (!MODE_DISPLAY.equals(mode) && !MODE_FULL.equals(mode))
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "export",
                    "导出路径非法: " + mode);
        }
        return mode;
    }

    public static List<String> resolveDisplayFields(String type, List<String> requested,
                                                    boolean plateColorNameSupported)
    {
        if (requested == null || requested.isEmpty())
        {
            List<String> defaults = new ArrayList<String>(defaultDisplayFields(type));
            // api 已对 snapshot/fee 展示列声明 plate_color_name；未支持时不要请求空列
            if (plateColorNameSupported && ("fee".equals(type) || "snapshot".equals(type))
                    && !defaults.contains("plate_color_name"))
            {
                defaults.add("plate_color_name");
            }
            return defaults;
        }
        if (requested.size() > MAX_DISPLAY_FIELDS)
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "export",
                    "展示字段最多 " + MAX_DISPLAY_FIELDS + " 个");
        }
        for (String field : requested)
        {
            if (BLOCKED_DISPLAY_FIELDS.contains(field))
            {
                throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "export",
                        "展示字段路径不允许包含大字段: " + field + "，请使用全字段导出");
            }
            if ("plate_color_name".equals(field)
                    && ("trail".equals(type) || !plateColorNameSupported))
            {
                throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "export",
                        "api 尚未支持 " + type + " 展示字段 plate_color_name");
            }
        }
        return requested;
    }

    public static List<String> defaultDisplayFields(String type)
    {
        if ("fee".equals(type))
        {
            return FEE_DISPLAY_FIELDS;
        }
        if ("trail".equals(type))
        {
            return TRAIL_DISPLAY_FIELDS;
        }
        return SNAPSHOT_DISPLAY_FIELDS;
    }

    /**
     * 过滤字段与取值校验。
     *
     * <p>api 对未知过滤键在 {@code switch} 中静默忽略，会导致“带了筛选却导出全量”。
     * 因此 backend 必须先做字段白名单校验：未知键直接 400。</p>
     *
     * <p>码值类字段（机构/路段/门架/收费广场/车牌颜色）走精确匹配，允许单字符；
     * 车牌与名称类字段仍要求至少 2 个字符，避免单字符扫描。</p>
     */
    public static void validateFuzzy(Map<String, String> fuzzyFields)
    {
        if (fuzzyFields == null)
        {
            return;
        }
        for (Map.Entry<String, String> entry : fuzzyFields.entrySet())
        {
            String rawKey = entry.getKey();
            String field = rawKey == null ? "" : rawKey.trim();
            String value = entry.getValue();
            if (value == null || value.trim().isEmpty())
            {
                continue;
            }
            // 校验用 trim 后的 key、下发若用原 key，会出现「白名单通过但 api 静默忽略」，
            // 用户以为带了筛选实际导出全量；这里直接拒绝带首尾空白的键。
            if (rawKey == null || !rawKey.equals(field))
            {
                throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "export",
                        "过滤字段名不能包含首尾空白: " + rawKey);
            }
            String trimmed = value.trim();
            if (trimmed.length() > MAX_FILTER_VALUE_LENGTH)
            {
                throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "export",
                        "过滤字段 " + field + " 取值过长（上限 " + MAX_FILTER_VALUE_LENGTH + " 个字符）");
            }
            if (EXACT_FILTERS.contains(field))
            {
                continue;
            }
            if (!FUZZY_FILTERS.contains(field))
            {
                throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "export",
                        "不支持的过滤字段: " + field);
            }
            if (trimmed.length() < 2)
            {
                throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "export",
                        "过滤字段 " + field + " 至少需要 2 个字符");
            }
        }
    }

    public static void validatePurpose(String purpose)
    {
        if (purpose == null || purpose.trim().length() < 4)
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "export",
                    "全字段导出必须填写用途说明（至少 4 个字符）");
        }
    }

    private static final Set<String> PLATE_FILTERS = new HashSet<String>(Arrays.asList(
            "platenumber", "vehicleplate", "carNo", "plateColor", "plate_color"));

    /** 精确匹配字段：码值类允许单字符（如 plateColor=1），不做“模糊≥2 字符”限制。 */
    private static final Set<String> EXACT_FILTERS = new HashSet<String>(Arrays.asList(
            "plateColor", "plate_color", "orgcode", "sectioncode", "roadcode",
            "gantrycode", "tollcode", "gantryid"));

    /** 模糊匹配字段：需至少 2 个字符，避免单字符全表扫描。 */
    private static final Set<String> FUZZY_FILTERS = new HashSet<String>(Arrays.asList(
            "platenumber", "vehicleplate", "carNo", "orgname", "sectionname",
            "roadname", "gantryname", "tollname"));

    private static final int MAX_FILTER_VALUE_LENGTH = 64;

    private static final String ORGCODE = "orgcode";

    /**
     * 服务端数据范围收敛。
     *
     * <p>非管理员只能导出自己机构（登录用户 {@code subCode}）的数据：请求未带 orgcode 时强制注入，
     * 带了其它机构时直接拒绝。api 的 trail 表未声明任何维度过滤，无法安全收敛，因此非管理员不允许导出。</p>
     *
     * @return 已注入机构过滤条件的新 map（不修改入参）
     */
    public static Map<String, String> applyOrgScope(String type, Map<String, String> fuzzyFields,
                                                    boolean admin, String userOrgCode)
    {
        Map<String, String> scoped = new LinkedHashMap<String, String>();
        String requestedOrg = null;
        if (fuzzyFields != null)
        {
            for (Map.Entry<String, String> entry : fuzzyFields.entrySet())
            {
                if (entry.getKey() != null && ORGCODE.equalsIgnoreCase(entry.getKey().trim()))
                {
                    requestedOrg = entry.getValue();
                }
                else
                {
                    scoped.put(entry.getKey(), entry.getValue());
                }
            }
        }
        if (admin)
        {
            if (requestedOrg != null && !requestedOrg.trim().isEmpty())
            {
                scoped.put(ORGCODE, requestedOrg.trim());
            }
            return scoped;
        }
        if ("trail".equals(type))
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "export",
                    "轨迹导出暂不支持按机构收敛数据范围，仅管理员可导出");
        }
        String scope = userOrgCode == null ? "" : userOrgCode.trim();
        if (scope.isEmpty() || "-1".equals(scope))
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "export",
                    "当前账号未绑定机构，无法导出业务数据");
        }
        if (requestedOrg != null && !requestedOrg.trim().isEmpty()
                && !scope.equals(requestedOrg.trim()))
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "export",
                    "导出机构超出当前账号数据范围: " + requestedOrg);
        }
        scoped.put(ORGCODE, scope);
        return scoped;
    }

    private static final Set<String> DIMENSION_FILTERS = new HashSet<String>(Arrays.asList(
            "orgcode", "sectioncode", "roadcode", "gantrycode", "tollcode", "gantryid",
            "orgname", "sectionname", "roadname", "gantryname", "tollname"));

    /**
     * 全字段导出过滤能力校验。
     *
     * @param type 导出表：snapshot/fee/trail
     * @param capabilities api 能力探测结果（含按表/字段矩阵）
     */
    public static void validateFullFilters(String type, Map<String, String> fuzzyFields,
                                           ExportCapabilityService.Capabilities capabilities)
    {
        if (fuzzyFields == null || fuzzyFields.isEmpty())
        {
            return;
        }
        for (Map.Entry<String, String> entry : fuzzyFields.entrySet())
        {
            String field = entry.getKey() == null ? "" : entry.getKey().trim();
            if (PLATE_FILTERS.contains(field))
            {
                continue;
            }
            if (!DIMENSION_FILTERS.contains(field))
            {
                throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "export",
                        "全字段导出不支持过滤字段: " + field);
            }
            if (capabilities == null || !capabilities.supportsDimensionField(type, field))
            {
                throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "export",
                        "全字段导出当前不支持 " + type + " 的维度过滤 " + field
                                + "（api 按表能力矩阵未声明）");
            }
        }
    }
}
