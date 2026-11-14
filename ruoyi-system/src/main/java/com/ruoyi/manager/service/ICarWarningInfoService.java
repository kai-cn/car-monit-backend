package com.ruoyi.manager.service;

import com.baomidou.mybatisplus.spring.service.IService;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarWarningInfo;
import com.ruoyi.manager.domain.vo.bigscreen.CarLocationParam;

import java.util.List;

/**
 * 预警车辆Service接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
public interface ICarWarningInfoService extends IService<CarWarningInfo> {
    /**
     * 查询预警车辆
     *
     * @param id 预警车辆ID
     * @return 预警车辆
     */
    CarWarningInfo selectCarWarningInfoById(String id);

    /**
     * 查询预警车辆列表
     *
     * @param carWarningInfo 预警车辆
     * @return 预警车辆集合
     */
    List<CarWarningInfo> selectCarWarningInfoList(CarWarningInfo carWarningInfo);


    /**
     * 新增或者修改预警车辆
     *
     * @param carWarningInfo 预警车辆
     * @return 结果
     */
    AjaxResult saveCarWarningInfo(CarWarningInfo carWarningInfo);

    /**
     * 批量删除预警车辆
     *
     * @param ids 需要删除的预警车辆ID
     * @return 结果
     */
    AjaxResult deleteCarWarningInfoByIds(String[] ids);

    /**
     * 预警大屏 100
     * @return
     */
    List<CarWarningInfo> selectCarWarningInfoListLimit100(CarLocationParam param);


    /**
     * 批量删除预警车辆
     *
     * @param idList
     * @return 结果
     */
    AjaxResult deleteCarWarningInfoByUUid(List<String> idList);


    /**
     * 跟新redis
     */
    void updateRedisWarningList();


    /**
     * 从缓存拿到carlist
     */
    List<CarWarningInfo> getRedisCarWarningList();


}
