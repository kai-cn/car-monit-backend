package com.ruoyi.common.core.domain;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.ruoyi.common.core.context.TraceContext;

import java.io.Serializable;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * 监控增强版统一响应包装类
 * <p>
 * 【设计目的】
 * 1. 统一所有API接口的响应格式，确保前后端契约一致
 * 2. 将TraceId、请求耗时、时间戳等监控信息内嵌到响应中
 * 3. 支持成功/失败/警告等多种状态码
 * </p>
 *
 * <p>【响应格式】</p>
 * <pre>
 * {
 *   "code": 200,           // 状态码（200=成功,500=失败,401=未授权等）
 *   "message": "操作成功",  // 消息描述
 *   "data": {...},         // 业务数据（可为空）
 *   "traceId": "tid-xxx",  // 链路追踪ID
 *   "timestamp": 1717820000000, // 响应时间戳
 *   "datetime": "2024-06-08 10:00:00"  // 人类可读时间
 * }
 * </pre>
 *
 * <p>【使用示例】</p>
 * <pre>
 * return MonitorResponse.success(userList);
 * return MonitorResponse.fail("操作失败");
 * return MonitorResponse.build(401, "未授权", null);
 * </pre>
 *
 * @author ruoyi
 */
@JsonInclude(JsonInclude.Include.NON_NULL) // null字段不序列化到JSON
public class MonitorResponse<T> implements Serializable {

    private static final long serialVersionUID = 1L;

    // ===================== 状态码常量 =====================

    /** 成功状态码 */
    public static final int CODE_SUCCESS = 200;

    /** 失败状态码（通用） */
    public static final int CODE_FAIL = 500;

    /** 参数校验失败 */
    public static final int CODE_VALIDATE_ERROR = 400;

    /** 未授权 */
    public static final int CODE_UNAUTHORIZED = 401;

    /** 资源不存在 */
    public static final int CODE_NOT_FOUND = 404;

    // ===================== 响应字段 =====================

    /** 响应状态码 */
    private int code;

    /** 响应消息 */
    private String message;

    /** 业务数据 */
    private T data;

    /** 链路追踪ID（非业务，用于问题定位） */
    private String traceId;

    /** 响应时间戳（毫秒） */
    private long timestamp;

    /** 人类可读的时间格式 */
    private String datetime;

    /** 请求执行耗时（毫秒，由AOP切面填充） */
    private Long cost;

    // ===================== 构造方法 =====================

    /**
     * 默认私有构造方法（禁止直接new）
     * 统一通过静态工厂方法创建实例，确保所有必要字段都已填充
     */
    private MonitorResponse() {
        this.timestamp = System.currentTimeMillis();
        this.datetime = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date());
        this.traceId = TraceContext.getTraceId();
    }

    // ===================== 静态工厂方法（对外API） =====================

    /**
     * 成功响应（无数据）
     */
    public static <T> MonitorResponse<T> success() {
        MonitorResponse<T> response = new MonitorResponse<T>();
        response.setCode(CODE_SUCCESS);
        response.setMessage("操作成功");
        return response;
    }

    /**
     * 成功响应（携带业务数据）
     *
     * @param data 业务数据
     */
    public static <T> MonitorResponse<T> success(T data) {
        MonitorResponse<T> response = new MonitorResponse<T>();
        response.setCode(CODE_SUCCESS);
        response.setMessage("操作成功");
        response.setData(data);
        return response;
    }

    /**
     * 成功响应（自定义消息）
     *
     * @param message 消息
     * @param data    业务数据
     */
    public static <T> MonitorResponse<T> success(String message, T data) {
        MonitorResponse<T> response = new MonitorResponse<T>();
        response.setCode(CODE_SUCCESS);
        response.setMessage(message);
        response.setData(data);
        return response;
    }

    /**
     * 失败响应（通用）
     *
     * @param message 失败消息
     */
    public static <T> MonitorResponse<T> fail(String message) {
        MonitorResponse<T> response = new MonitorResponse<T>();
        response.setCode(CODE_FAIL);
        response.setMessage(message);
        return response;
    }

    /**
     * 失败响应（自定义状态码）
     *
     * @param code    状态码
     * @param message 消息
     */
    public static <T> MonitorResponse<T> fail(int code, String message) {
        MonitorResponse<T> response = new MonitorResponse<T>();
        response.setCode(code);
        response.setMessage(message);
        return response;
    }

    /**
     * 通用构建方法（最灵活，用于所有其他场景）
     *
     * @param code    状态码
     * @param message 消息
     * @param data    业务数据
     */
    public static <T> MonitorResponse<T> build(int code, String message, T data) {
        MonitorResponse<T> response = new MonitorResponse<T>();
        response.setCode(code);
        response.setMessage(message);
        response.setData(data);
        return response;
    }

    // ===================== 便利方法 =====================

    /**
     * 判断当前响应是否成功
     * 【设计】成功的判断标准是 code == 200
     */
    public boolean isSuccess() {
        return this.code == CODE_SUCCESS;
    }

    /**
     * 设置请求耗时（由AOP切面调用填充）
     *
     * @param costMs 耗时（毫秒）
     */
    public MonitorResponse<T> withCost(long costMs) {
        this.cost = costMs;
        return this;
    }

    // ===================== Getter/Setter =====================

    public int getCode() { return code; }
    public void setCode(int code) { this.code = code; }

    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }

    public T getData() { return data; }
    public void setData(T data) { this.data = data; }

    public String getTraceId() { return traceId; }
    public void setTraceId(String traceId) { this.traceId = traceId; }

    public long getTimestamp() { return timestamp; }
    public void setTimestamp(long timestamp) { this.timestamp = timestamp; }

    public String getDatetime() { return datetime; }
    public void setDatetime(String datetime) { this.datetime = datetime; }

    public Long getCost() { return cost; }
    public void setCost(Long cost) { this.cost = cost; }

    /**
     * 重写toString，便于日志输出
     */
    @Override
    public String toString() {
        return "MonitorResponse{" +
                "code=" + code +
                ", message='" + message + '\'' +
                ", data=" + (data == null ? "null" : data.getClass().getSimpleName()) +
                ", traceId='" + traceId + '\'' +
                ", datetime='" + datetime + '\'' +
                '}';
    }
}
