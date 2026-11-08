package com.ruoyi.manager.domain.vo.bigscreen;

/**
 * 按车辆聚合的补缴次数（用于消除 exceptRecordList 的 N+1 查询）。
 *
 * @author car-monit-backend-java-v3
 */
public class CarIdCountVO
{
    private String carId;

    private Long cnt;

    public String getCarId()
    {
        return carId;
    }

    public void setCarId(String carId)
    {
        this.carId = carId;
    }

    public Long getCnt()
    {
        return cnt;
    }

    public void setCnt(Long cnt)
    {
        this.cnt = cnt;
    }
}
