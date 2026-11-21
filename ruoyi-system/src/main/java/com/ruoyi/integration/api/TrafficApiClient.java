package com.ruoyi.integration.api;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ruoyi.base.domain.CarParaVO;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeRecords01;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.domain.TrailInfo;
import com.ruoyi.base.domain.ZdataTrailFitting;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.manager.domain.CarWarningInfo;
import com.ruoyi.manager.domain.vo.bigscreen.CarAuditVO;
import com.ruoyi.manager.domain.vo.bigscreen.CarStatisticsVO;
import com.ruoyi.manager.domain.vo.bigscreen.IncomeStatisticParam;
import com.ruoyi.manager.domain.vo.bigscreen.TopTenVO;
import com.ruoyi.manager.domain.vo.bigscreen.incomeStatisticVO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * backend → api 的类型化查询客户端。
 *
 * <p>所有方法遵循统一约定：先做查询契约校验，再按 {@link TrafficApiScenario} 选择超时，
 * 经 {@link ResilientApiExecutor} 执行重试/熔断，最终把 api 返回统一映射为
 * {@link ApiPageResult} / 领域对象；错误统一抛 {@link ApiClientException}。</p>
 *
 * @author car-monit-backend-java-v3
 */
@Service
public class TrafficApiClient
{
    private static final int DEFAULT_PAGE_SIZE = 10;

    private static final int WARNING_LIMIT = 100;

    /** 旧同步导出临时上限（设计 §1.3 A8：展示字段、单次 1 万条过渡限制） */
    private static final int LEGACY_EXPORT_LIMIT = 10000;

    private static final String SNAPSHOT_LIST = "/base/snapshotflow/list";

    private static final String SNAPSHOT_EXPORT = "/base/snapshotflow/listToExport";

    private static final String FEE_LIST = "/base/feerecords/list";

    private static final String FEE_EXPORT = "/base/feerecords/listToExport";

    private static final String STATS_ESCAPE = "/api/v1/bigscreen/stats/escape";

    private static final String STATS_AUDIT = "/api/v1/bigscreen/stats/audit";

    private static final String STATS_INCOME = "/api/v1/bigscreen/stats/income";

    private static final String STATS_WARNING_TOP = "/api/v1/bigscreen/stats/warning-top";

    private static final String WARNING_LIST = "/api/v1/bigscreen/warning/list";

    private static final String EXPORT_SUBMIT = "/api/v1/large/export/submit";

    private static final String EXPORT_STATUS = "/api/v1/large/export/status/";

    private static final String TRAIL_ONLINE = "/base/sysutil/carTrackQueryByCarNo";

    private static final String PROVCAPTURE_LIST = "/base/provcapture/list";

    private static final String STATIONCAPTURE_LIST = "/base/stationcapture/list";

    private static final String VEHICLE_WEIGHT_LIST = "/base/vehicleweight/list";

    private static final String FEE_GANTRY_LIST = "/base/feeGantry/list";

    private static final String FEE_STATION_ENTER_LIST = "/base/feeStationEnter/list";

    private static final String FEE_STATION_EXIT_LIST = "/base/feestationexit/list";

    private static final String FWQ_FLOW_LIST = "/manager/fwqclls/list";

    private static final String TRAFFIC_V3_LIST = "/api/v3/traffic/list";

    @Autowired
    private TrafficApiHttpClient httpClient;

    @Autowired
    private ResilientApiExecutor executor;

    @Autowired
    private TrafficApiProperties properties;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private com.ruoyi.manager.service.bigscreen.BigScreenDictService bigScreenDictService;

    private ObjectMapper apiMapper;

    @javax.annotation.PostConstruct
    public void initMapper()
    {
        // api 字段可能多于 backend VO，转换时忽略未知字段
        this.apiMapper = objectMapper.copy()
                .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
    }

    // ------------------------------------------------------------------
    // 三表列表
    // ------------------------------------------------------------------

    public ApiPageResult<OdsRtSzdnSnapshotFlowAddcode> snapshotPage(OdsRtSzdnSnapshotFlowAddcode query)
    {
        normalizePage(query.getPageNum(), query.getPageSize());
        TableDataInfo raw = executor.execute("snapshotPage",
                () -> httpClient.get(TrafficApiScenario.LIST, SNAPSHOT_LIST,
                        toQueryMap(query), TableDataInfo.class),
                properties.retries(TrafficApiScenario.LIST));
        List<OdsRtSzdnSnapshotFlowAddcode> rows = deserializeRows(raw, OdsRtSzdnSnapshotFlowAddcode.class);
        return new ApiPageResult<OdsRtSzdnSnapshotFlowAddcode>(rows,
                raw == null ? 0L : raw.getTotal(),
                query.getPageNum() == null ? 1 : query.getPageNum(),
                query.getPageSize() == null ? DEFAULT_PAGE_SIZE : query.getPageSize());
    }

    public List<OdsRtSzdnSnapshotFlowAddcode> snapshotExport(OdsRtSzdnSnapshotFlowAddcode query)
    {
        // api listToExport 使用 PageHelper（默认 pageSize=10）；旧同步导出按设计临时上限 1 万条
        query.setPageNum(1);
        query.setPageSize(LEGACY_EXPORT_LIMIT);
        List<OdsRtSzdnSnapshotFlowAddcode> rows = executor.execute("snapshotExport",
                () -> httpClient.get(TrafficApiScenario.LEGACY_EXPORT, SNAPSHOT_EXPORT,
                        toQueryMap(query), new TypeReference<List<OdsRtSzdnSnapshotFlowAddcode>>()
                        {
                        }),
                properties.retries(TrafficApiScenario.LEGACY_EXPORT));
        return rows == null ? new ArrayList<OdsRtSzdnSnapshotFlowAddcode>() : rows;
    }

    public ApiPageResult<OdsLwzxsfsjFeeRecords01> feePage(OdsLwzxsfsjFeeRecords01 query)
    {
        normalizePage(query.getPageNum(), query.getPageSize());
        TableDataInfo raw = executor.execute("feePage",
                () -> httpClient.get(TrafficApiScenario.LIST, FEE_LIST,
                        toQueryMap(query), TableDataInfo.class),
                properties.retries(TrafficApiScenario.LIST));
        List<OdsLwzxsfsjFeeRecords01> rows = deserializeRows(raw, OdsLwzxsfsjFeeRecords01.class);
        return new ApiPageResult<OdsLwzxsfsjFeeRecords01>(rows,
                raw == null ? 0L : raw.getTotal(),
                query.getPageNum() == null ? 1 : query.getPageNum(),
                query.getPageSize() == null ? DEFAULT_PAGE_SIZE : query.getPageSize());
    }

    public List<OdsLwzxsfsjFeeRecords01> feeExport(OdsLwzxsfsjFeeRecords01 query)
    {
        // 同 snapshotExport：显式 1 万条上限，避免 api 默认 pageSize=10 只导出首页
        query.setPageNum(1);
        query.setPageSize(LEGACY_EXPORT_LIMIT);
        List<OdsLwzxsfsjFeeRecords01> rows = executor.execute("feeExport",
                () -> httpClient.get(TrafficApiScenario.LEGACY_EXPORT, FEE_EXPORT,
                        toQueryMap(query), new TypeReference<List<OdsLwzxsfsjFeeRecords01>>()
                        {
                        }),
                properties.retries(TrafficApiScenario.LEGACY_EXPORT));
        return rows == null ? new ArrayList<OdsLwzxsfsjFeeRecords01>() : rows;
    }

    // ------------------------------------------------------------------
    // 扩展流水列表（省界/收费站抓拍、称重、出入口、服务区）
    // ------------------------------------------------------------------

    /**
     * 通用流水分页：api 与 backend 使用同名 domain，参数按字段名透传。
     *
     * <p>要求调用方先设置 pageNum/pageSize；空结果与 api 业务码由 {@link #deserializeRows} 统一处理。</p>
     */
    public <T> ApiPageResult<T> flowPage(String endpoint, Object query, int pageNum, int pageSize,
                                         Class<T> rowType)
    {
        TrafficQueryContract.validatePaging(pageNum, pageSize);
        Map<String, String> params = toQueryMap(query);
        params.put("pageNum", String.valueOf(pageNum));
        params.put("pageSize", String.valueOf(pageSize));
        TableDataInfo raw = executor.execute("flow:" + endpoint,
                () -> httpClient.get(TrafficApiScenario.FLOW_EXTENDED, endpoint, params,
                        TableDataInfo.class),
                properties.retries(TrafficApiScenario.FLOW_EXTENDED));
        List<T> rows = deserializeRows(raw, rowType);
        return new ApiPageResult<T>(rows, raw == null ? 0L : raw.getTotal(), pageNum, pageSize);
    }

    public <T> ApiPageResult<T> provcapturePage(Object query, int pageNum, int pageSize,
                                                Class<T> rowType)
    {
        return flowPage(PROVCAPTURE_LIST, query, pageNum, pageSize, rowType);
    }

    public <T> ApiPageResult<T> stationcapturePage(Object query, int pageNum, int pageSize,
                                                   Class<T> rowType)
    {
        return flowPage(STATIONCAPTURE_LIST, query, pageNum, pageSize, rowType);
    }

    public <T> ApiPageResult<T> vehicleWeightPage(Object query, int pageNum, int pageSize,
                                                 Class<T> rowType)
    {
        return flowPage(VEHICLE_WEIGHT_LIST, query, pageNum, pageSize, rowType);
    }

    public <T> ApiPageResult<T> feeGantryPage(Object query, int pageNum, int pageSize,
                                              Class<T> rowType)
    {
        return flowPage(FEE_GANTRY_LIST, query, pageNum, pageSize, rowType);
    }

    public <T> ApiPageResult<T> feeStationEnterPage(Object query, int pageNum, int pageSize,
                                                    Class<T> rowType)
    {
        return flowPage(FEE_STATION_ENTER_LIST, query, pageNum, pageSize, rowType);
    }

    public <T> ApiPageResult<T> feeStationExitPage(Object query, int pageNum, int pageSize,
                                                   Class<T> rowType)
    {
        return flowPage(FEE_STATION_EXIT_LIST, query, pageNum, pageSize, rowType);
    }

    public <T> ApiPageResult<T> serviceAreaFlowPage(Object query, int pageNum, int pageSize,
                                                    Class<T> rowType)
    {
        return flowPage(FWQ_FLOW_LIST, query, pageNum, pageSize, rowType);
    }

    /**
     * 扩展流水详情：按主键调用 api 的 {@code GET {endpoint}/{id}}（api 已提供等价端点）。
     *
     * <p>返回 {@code AjaxResult} 的 data 节点；api 业务码非 200 时映射为统一错误。</p>
     */
    public <T> T flowDetail(String endpoint, String id, Class<T> rowType)
    {
        if (id == null || !id.matches("[A-Za-z0-9_-]{1,128}"))
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "flowDetail",
                    "非法详情主键: " + id);
        }
        AjaxResult raw = executor.execute("flowDetail:" + endpoint,
                () -> httpClient.get(TrafficApiScenario.FLOW_EXTENDED, endpoint + "/" + id,
                        Collections.<String, String>emptyMap(), AjaxResult.class),
                properties.retries(TrafficApiScenario.FLOW_EXTENDED));
        if (raw == null)
        {
            return null;
        }
        Object code = raw.get("code");
        if (code != null)
        {
            int value;
            try
            {
                value = Integer.parseInt(String.valueOf(code));
            }
            catch (NumberFormatException e)
            {
                value = 200;
            }
            if (value != 200)
            {
                throw businessException("flowDetail", value, raw.get("msg"));
            }
        }
        Object data = raw.get("data");
        return data == null ? null : apiMapper.convertValue(data, rowType);
    }

    /**
     * 拟合轨迹列表：api 未提供 `/base/fitting/list`，统一走 V3 组合查询（table=trail）。
     */
    public ApiPageResult<ZdataTrailFitting> trailFittingPage(Object query, int pageNum, int pageSize,
                                                             Class<ZdataTrailFitting> rowType)
    {
        TrafficQueryContract.validatePaging(pageNum, pageSize);
        Map<String, Object> body = new LinkedHashMap<String, Object>();
        body.put("table", "trail");
        body.put("pageNum", pageNum);
        body.put("pageSize", pageSize);
        body.put("needTotal", true);
        if (query instanceof ZdataTrailFitting)
        {
            ZdataTrailFitting q = (ZdataTrailFitting) query;
            if (q.getEnvehicleid() != null && !q.getEnvehicleid().trim().isEmpty())
            {
                body.put("plate", q.getEnvehicleid().trim());
            }
            if (q.getEntime() != null)
            {
                body.put("startTime", new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
                        .format(q.getEntime()));
            }
            if (q.getExtime() != null)
            {
                body.put("endTime", new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss")
                        .format(q.getExtime()));
            }
        }
        Map<String, Object> response = executor.execute("trailFittingList",
                () -> httpClient.post(TrafficApiScenario.FLOW_EXTENDED, TRAFFIC_V3_LIST,
                        Collections.<String, String>emptyMap(), body,
                        new TypeReference<Map<String, Object>>()
                        {
                        }),
                properties.retries(TrafficApiScenario.FLOW_EXTENDED));
        checkBusinessCode("trailFittingList", response);
        Object rows = response.get("rows");
        List<ZdataTrailFitting> list = rows == null
                ? new ArrayList<ZdataTrailFitting>()
                : apiMapper.convertValue(rows, apiMapper.getTypeFactory()
                        .constructCollectionType(List.class, rowType));
        enrichPlateColor(list);
        long total = 0L;
        Object totalValue = response.get("total");
        if (totalValue instanceof Number)
        {
            total = ((Number) totalValue).longValue();
        }
        return new ApiPageResult<ZdataTrailFitting>(list, total, pageNum, pageSize);
    }

    // ------------------------------------------------------------------
    // 轨迹在线查询
    // ------------------------------------------------------------------

    /**
     * 轨迹在线列表：api 侧 ES 取元数据并按 cid 批量回查 GaussDB 轨迹点，返回 {@link TrailInfo}。
     */
    public ApiPageResult<TrailInfo> trailPage(CarParaVO query, int pageNum, int pageSize)
    {
        TrafficQueryContract.validatePaging(pageNum, pageSize);
        Map<String, String> params = toQueryMap(query);
        params.put("pageNum", String.valueOf(pageNum));
        params.put("pageSize", String.valueOf(pageSize));
        TableDataInfo raw = executor.execute("trailOnline",
                () -> httpClient.get(TrafficApiScenario.TRAIL, TRAIL_ONLINE, params,
                        TableDataInfo.class),
                properties.retries(TrafficApiScenario.TRAIL));
        List<TrailInfo> rows = deserializeRows(raw, TrailInfo.class);
        return new ApiPageResult<TrailInfo>(rows, raw == null ? 0L : raw.getTotal(), pageNum, pageSize);
    }

    // ------------------------------------------------------------------
    // 大屏统计
    // ------------------------------------------------------------------

    public List<CarStatisticsVO> escapeStatistics(IncomeStatisticParam param)
    {
        String[] range = TrafficQueryContract.normalizeDateRange(param.getApplyTime1(), param.getApplyTime2());
        Map<String, String> params = new LinkedHashMap<String, String>();
        params.put("startDate", range[0]);
        params.put("endDate", range[1]);
        addParam(params, "orgId", param.getOrgId());
        addParam(params, "escapedType", param.getEscapedType());
        List<CarStatisticsVO> rows = executor.execute("escapeStatistics",
                () -> httpClient.get(TrafficApiScenario.STATS, STATS_ESCAPE, params,
                        new TypeReference<List<CarStatisticsVO>>()
                        {
                        }),
                properties.retries(TrafficApiScenario.STATS));
        return rows == null ? new ArrayList<CarStatisticsVO>() : rows;
    }

    public CarAuditVO auditStatistics(IncomeStatisticParam param)
    {
        String[] range = TrafficQueryContract.normalizeDateRange(param.getApplyTime1(), param.getApplyTime2());
        Map<String, String> params = new LinkedHashMap<String, String>();
        params.put("startDate", range[0]);
        params.put("endDate", range[1]);
        return executor.execute("auditStatistics",
                () -> httpClient.get(TrafficApiScenario.STATS, STATS_AUDIT, params, CarAuditVO.class),
                properties.retries(TrafficApiScenario.STATS));
    }

    public List<incomeStatisticVO> incomeStatistics(IncomeStatisticParam param)
    {
        String applyTime1 = param.getApplyTime1();
        String applyTime2 = param.getApplyTime2();
        // 只传单侧时间也必须校验格式/顺序/365 天上限，避免非法串直接透传 api
        TrafficQueryContract.validateDateTimeRange(applyTime1, applyTime2);
        Map<String, String> params = new LinkedHashMap<String, String>();
        addParam(params, "queryDateType", param.getQueryDateType());
        addParam(params, "startDate", param.getStartDate());
        addParam(params, "applyTime1", applyTime1);
        addParam(params, "applyTime2", applyTime2);
        List<incomeStatisticVO> rows = executor.execute("incomeStatistics",
                () -> httpClient.get(TrafficApiScenario.STATS, STATS_INCOME, params,
                        new TypeReference<List<incomeStatisticVO>>()
                        {
                        }),
                properties.retries(TrafficApiScenario.STATS));
        return rows == null ? new ArrayList<incomeStatisticVO>() : rows;
    }

    public List<TopTenVO> warningTop(String startTime, String endTime, int topN)
    {
        String[] range = TrafficQueryContract.normalizeDateTimeRange(startTime, endTime);
        int limit = topN <= 0 ? 10 : Math.min(topN, 100);
        Map<String, String> params = new LinkedHashMap<String, String>();
        params.put("startTime", range[0]);
        params.put("endTime", range[1]);
        params.put("topN", String.valueOf(limit));
        List<TopTenVO> rows = executor.execute("warningTop",
                () -> httpClient.get(TrafficApiScenario.STATS, STATS_WARNING_TOP, params,
                        new TypeReference<List<TopTenVO>>()
                        {
                        }),
                properties.retries(TrafficApiScenario.STATS));
        return rows == null ? new ArrayList<TopTenVO>() : rows;
    }

    // ------------------------------------------------------------------
    // 大屏实时列表
    // ------------------------------------------------------------------

    public List<CarWarningInfo> warningList(String roadCode, String sectionCode, String tollCode,
                                            String gantryCode, String fwqbm, String escapedType,
                                            String carNo, int limit)
    {
        int safeLimit = limit <= 0 ? WARNING_LIMIT : Math.min(limit, WARNING_LIMIT);
        Map<String, String> params = new LinkedHashMap<String, String>();
        addParam(params, "roadCode", roadCode);
        addParam(params, "sectionCode", sectionCode);
        addParam(params, "tollCode", tollCode);
        addParam(params, "gantryCode", gantryCode);
        addParam(params, "fwqbm", fwqbm);
        addParam(params, "escapedType", escapedType);
        addParam(params, "carNo", carNo);
        params.put("limit", String.valueOf(safeLimit));
        List<CarWarningInfo> rows = executor.execute("warningList",
                () -> httpClient.get(TrafficApiScenario.WARNING_LIST, WARNING_LIST, params,
                        new TypeReference<List<CarWarningInfo>>()
                        {
                        }),
                properties.retries(TrafficApiScenario.WARNING_LIST));
        return rows == null ? new ArrayList<CarWarningInfo>() : rows;
    }

    // ------------------------------------------------------------------
    // 导出任务
    // ------------------------------------------------------------------

    public Map<String, Object> submitExport(String type, String startTime, String endTime,
                                            String mode, Map<String, Object> body)
    {
        String[] range = TrafficQueryContract.normalizeDateTimeRange(startTime, endTime);
        Map<String, String> params = new LinkedHashMap<String, String>();
        params.put("type", type);
        params.put("startTime", range[0]);
        params.put("endTime", range[1]);
        params.put("mode", mode);
        Map<String, Object> response = executor.execute("submitExport",
                () -> httpClient.post(TrafficApiScenario.EXPORT_SUBMIT, EXPORT_SUBMIT, params, body,
                        new TypeReference<Map<String, Object>>()
                        {
                        }),
                properties.retries(TrafficApiScenario.EXPORT_SUBMIT));
        checkBusinessCode("submitExport", response);
        Object taskId = response.get("taskId");
        if (taskId == null || String.valueOf(taskId).trim().isEmpty())
        {
            throw new ApiClientException(ApiErrorCode.CONTRACT_VIOLATION, "submitExport",
                    "api 未返回 taskId");
        }
        return response;
    }

    public Map<String, Object> exportStatus(String taskId)
    {
        if (taskId == null || !taskId.matches("[A-Za-z0-9_-]{1,64}"))
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "exportStatus",
                    "非法 taskId: " + taskId);
        }
        Map<String, Object> response = executor.execute("exportStatus",
                () -> httpClient.get(TrafficApiScenario.EXPORT_STATUS, EXPORT_STATUS + taskId,
                        Collections.<String, String>emptyMap(),
                        new TypeReference<Map<String, Object>>()
                        {
                        }),
                properties.retries(TrafficApiScenario.EXPORT_STATUS));
        if (response == null)
        {
            throw new ApiClientException(ApiErrorCode.NOT_FOUND, "exportStatus",
                    "导出任务不存在: " + taskId);
        }
        checkBusinessCode("exportStatus", response);
        return response;
    }

    // ------------------------------------------------------------------
    // 内部工具
    // ------------------------------------------------------------------

    private void normalizePage(Integer pageNum, Integer pageSize)
    {
        int pn = pageNum == null ? 1 : pageNum;
        int ps = pageSize == null ? DEFAULT_PAGE_SIZE : pageSize;
        TrafficQueryContract.validatePaging(pn, ps);
    }

    /**
     * DTO → 查询参数。只发送简单标量，列表/Map/对象跳过，避免把服务端解析用的集合字段重复下传。
     */
    private Map<String, String> toQueryMap(Object bean)
    {
        if (bean == null)
        {
            return Collections.emptyMap();
        }
        Map<String, Object> raw = apiMapper.convertValue(bean, new TypeReference<Map<String, Object>>()
        {
        });
        Map<String, String> result = new LinkedHashMap<String, String>();
        for (Map.Entry<String, Object> entry : raw.entrySet())
        {
            Object value = entry.getValue();
            if (value == null || value instanceof Collection || value instanceof Map)
            {
                continue;
            }
            if (value instanceof java.util.Date)
            {
                // api 侧按 yyyy-MM-dd HH:mm:ss 绑定日期参数，避免 epoch millis 解析失败
                result.put(entry.getKey(),
                        new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(value));
                continue;
            }
            if (value instanceof Number || value instanceof Boolean || value instanceof CharSequence)
            {
                result.put(entry.getKey(), String.valueOf(value));
            }
        }
        return result;
    }

    private void addParam(Map<String, String> params, String key, String value)
    {
        if (value != null && !value.trim().isEmpty())
        {
            params.put(key, value.trim());
        }
    }

    private <T> List<T> deserializeRows(TableDataInfo raw, Class<T> rowType)
    {
        if (raw == null)
        {
            return new ArrayList<T>();
        }
        if (raw.getCode() != 0 && raw.getCode() != 200)
        {
            // api 列表在 HTTP 200 内返回业务码（400/503 等），需按语义映射，不能一律当 5xx
            throw businessException("list", raw.getCode(), raw.getMsg());
        }
        if (raw.getRows() == null || raw.getRows().isEmpty())
        {
            return new ArrayList<T>();
        }
        List<T> rows = apiMapper.convertValue(raw.getRows(),
                apiMapper.getTypeFactory().constructCollectionType(List.class, rowType));
        enrichPlateColor(rows);
        return rows;
    }

    /**
     * 车牌颜色名称以 {@code sys_dict_data(dict_type=plate_color)} 为准。
     *
     * <p>字典缺失/未命中时回退原始码并标记 {@code UNKNOWN}，不丢弃整行。
     * 通过反射兼容不同流水 domain 的颜色字段名，避免为每个 domain 重复实现。</p>
     */
    private void enrichPlateColor(List<?> rows)
    {
        if (rows == null || rows.isEmpty())
        {
            return;
        }
        for (Object row : rows)
        {
            String code = readField(row, "platecolorcode");
            if (code == null || code.trim().isEmpty())
            {
                code = readField(row, "plateColorCode");
            }
            if (code == null || code.trim().isEmpty())
            {
                code = readField(row, "plateColor");
            }
            if (code == null || code.trim().isEmpty())
            {
                code = readField(row, "platecolor");
            }
            if (code == null || code.trim().isEmpty())
            {
                writeField(row, "plateColorName", "");
                continue;
            }
            com.ruoyi.manager.service.bigscreen.BigScreenDictService.PlateColorResult color =
                    bigScreenDictService.resolvePlateColor(code);
            writeField(row, "plateColorName", color.getName());
            if (!color.isKnown() && !color.getName().isEmpty())
            {
                writeField(row, "plateColorMark", "UNKNOWN");
            }
        }
    }

    private String readField(Object bean, String fieldName)
    {
        if (bean == null)
        {
            return null;
        }
        try
        {
            java.lang.reflect.Field field = findField(bean.getClass(), fieldName);
            if (field == null)
            {
                return null;
            }
            field.setAccessible(true);
            Object value = field.get(bean);
            return value == null ? null : String.valueOf(value);
        }
        catch (Exception e)
        {
            return null;
        }
    }

    private void writeField(Object bean, String fieldName, String value)
    {
        if (bean == null)
        {
            return;
        }
        try
        {
            java.lang.reflect.Field field = findField(bean.getClass(), fieldName);
            if (field == null)
            {
                return;
            }
            field.setAccessible(true);
            field.set(bean, value);
        }
        catch (Exception ignored)
        {
            // 字段不存在/类型不匹配时忽略，不影响列表返回
        }
    }

    private java.lang.reflect.Field findField(Class<?> type, String fieldName)
    {
        Class<?> current = type;
        while (current != null && current != Object.class)
        {
            try
            {
                return current.getDeclaredField(fieldName);
            }
            catch (NoSuchFieldException e)
            {
                current = current.getSuperclass();
            }
        }
        return null;
    }

    private void checkBusinessCode(String endpoint, Map<String, Object> response)
    {
        if (response == null)
        {
            // api 返回 2xx 空体时不能当成成功：调用方会 NPE，绕过契约错误码与 legacy 降级
            throw new ApiClientException(ApiErrorCode.CONTRACT_VIOLATION, endpoint,
                    "api 返回空响应体: " + endpoint);
        }
        Object code = response.get("code");
        if (code == null)
        {
            return;
        }
        int value;
        try
        {
            value = Integer.parseInt(String.valueOf(code));
        }
        catch (NumberFormatException e)
        {
            return;
        }
        if (value != 200)
        {
            Object message = response.get("message");
            throw businessException(endpoint, value, message);
        }
    }

    /**
     * api 业务码 → 后端稳定错误码。
     */
    private ApiClientException businessException(String endpoint, int value, Object message)
    {
        ApiErrorCode code;
        if (value == 400 || value == 422)
        {
            code = ApiErrorCode.INVALID_ARGUMENT;
        }
        else if (value == 401)
        {
            code = ApiErrorCode.UNAUTHORIZED;
        }
        else if (value == 403)
        {
            code = ApiErrorCode.FORBIDDEN;
        }
        else if (value == 404)
        {
            code = ApiErrorCode.NOT_FOUND;
        }
        else if (value == 409)
        {
            code = ApiErrorCode.INVALID_ARGUMENT;
        }
        else if (value == 429)
        {
            code = ApiErrorCode.RATE_LIMITED;
        }
        else if (value >= 500)
        {
            code = ApiErrorCode.UPSTREAM_ERROR;
        }
        else
        {
            code = ApiErrorCode.CONTRACT_VIOLATION;
        }
        String text = message == null ? "" : String.valueOf(message);
        if (code == ApiErrorCode.NOT_FOUND)
        {
            text = "exportStatus".equals(endpoint) ? "导出任务不存在或已过期" : "api 导出契约不可用";
        }
        return new ApiClientException(code, endpoint,
                "api 业务错误码: " + value + " msg=" + text, 200, String.valueOf(value), null);
    }
}
