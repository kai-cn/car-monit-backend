package com.ruoyi.common.core.exception;

/**
 * 业务异常类
 * <p>
 * 【设计目的】
 * 在业务代码中主动抛出可预期的异常（如用户不存在、余额不足等）
 * 区别于系统级异常（NullPointerException等），业务异常属于正常业务流程分支
 * </p>
 *
 * <p>【使用示例】</p>
 * <pre>
 * if (user == null) {
 *     throw new BusinessException("用户不存在");
 * }
 *
 * if (order.getStatus() != 1) {
 *     throw new BusinessException(400, "订单状态不允许此操作", true);
 * }
 * </pre>
 *
 * @author ruoyi
 */
public class BusinessException extends RuntimeException {

    private static final long serialVersionUID = 1L;

    /** 状态码（用于区分不同业务场景，默认400） */
    private int code = 400;

    /** 是否需要发送告警通知（默认false，不发送） */
    private boolean alert = false;

    /**
     * 构造方法（只有消息）
     *
     * @param message 异常消息
     */
    public BusinessException(String message) {
        super(message);
    }

    /**
     * 构造方法（状态码 + 消息）
     *
     * @param code    状态码
     * @param message 消息
     */
    public BusinessException(int code, String message) {
        super(message);
        this.code = code;
    }

    /**
     * 构造方法（完整信息：状态码 + 消息 + 是否告警）
     *
     * @param code    状态码
     * @param message 消息
     * @param alert   是否触发告警（通知到企业微信/钉钉等）
     */
    public BusinessException(int code, String message, boolean alert) {
        super(message);
        this.code = code;
        this.alert = alert;
    }

    /**
     * 构造方法（消息 + 原始异常）
     *
     * @param message 消息
     * @param cause   原始异常
     */
    public BusinessException(String message, Throwable cause) {
        super(message, cause);
    }

    // ===================== Getter =====================

    public int getCode() { return code; }
    public boolean isAlert() { return alert; }
}
