package com.ruoyi.integration.api;

/**
 * 轻量滑动窗口熔断器：连续失败达到阈值后打开，冷却后半开探测。
 *
 * <p>只统计基础设施类失败（超时/网络/5xx），4xx 与契约缺失不计入，避免把“接口未上线”误判为故障。</p>
 *
 * @author car-monit-backend-java-v3
 */
public class CircuitBreaker
{
    public enum State
    {
        CLOSED, OPEN, HALF_OPEN
    }

    private final int failureThreshold;

    private final long openMillis;

    private final int halfOpenPermits;

    private State state = State.CLOSED;

    private int consecutiveFailures;

    private long openedAt;

    private int halfOpenInFlight;

    public CircuitBreaker(int failureThreshold, long openMillis, int halfOpenPermits)
    {
        this.failureThreshold = Math.max(1, failureThreshold);
        this.openMillis = Math.max(1000L, openMillis);
        this.halfOpenPermits = Math.max(1, halfOpenPermits);
    }

    public synchronized boolean allowRequest()
    {
        if (state == State.CLOSED)
        {
            return true;
        }
        if (state == State.OPEN)
        {
            if (System.currentTimeMillis() - openedAt >= openMillis)
            {
                state = State.HALF_OPEN;
                halfOpenInFlight = 0;
            }
            else
            {
                return false;
            }
        }
        if (halfOpenInFlight < halfOpenPermits)
        {
            halfOpenInFlight++;
            return true;
        }
        return false;
    }

    public synchronized void onSuccess()
    {
        state = State.CLOSED;
        consecutiveFailures = 0;
        halfOpenInFlight = 0;
        openedAt = 0L;
    }

    public synchronized void onFailure()
    {
        consecutiveFailures++;
        if (state == State.HALF_OPEN)
        {
            open();
            return;
        }
        if (consecutiveFailures >= failureThreshold)
        {
            open();
        }
    }

    public synchronized State getState()
    {
        return state;
    }

    private void open()
    {
        state = State.OPEN;
        openedAt = System.currentTimeMillis();
        halfOpenInFlight = 0;
    }
}
