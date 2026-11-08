package com.ruoyi.manager.service.bigscreen;

import com.ruoyi.integration.api.ApiClientException;
import com.ruoyi.integration.api.ApiErrorCode;
import com.ruoyi.integration.api.TrafficQueryContract;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
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
            // api 只对 fee 展示列声明了 plate_color_name；未支持时不要请求空列
            if (plateColorNameSupported && "fee".equals(type)
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
            if ("plate_color_name".equals(field) && !plateColorNameSupported)
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

    public static void validateFuzzy(Map<String, String> fuzzyFields)
    {
        TrafficQueryContract.validateFuzzyMap(fuzzyFields);
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
            String field = entry.getKey();
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
