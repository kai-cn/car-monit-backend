package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.ZdataTrailFitting;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 车辆出入口拟合轨迹Service接口
 *
 * @author ruoyi
 * @date 2025-10-15
 */
public interface IZdataTrailFittingService extends IService<ZdataTrailFitting> {
    /**
     * 查询车辆出入口拟合轨迹
     *
     * @param cid 车辆出入口拟合轨迹ID
     * @return 车辆出入口拟合轨迹
     */
    ZdataTrailFitting selectZdataTrailFittingById(String cid);

    /**
     * 查询车辆出入口拟合轨迹列表
     *
     * @param zdataTrailFitting 车辆出入口拟合轨迹
     * @return 车辆出入口拟合轨迹集合
     */
    List<ZdataTrailFitting> selectZdataTrailFittingList(ZdataTrailFitting zdataTrailFitting);




}
