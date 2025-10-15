package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.ZdataTrailFitting;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 车辆出入口拟合轨迹Mapper接口
 *
 * @author ruoyi
 * @date 2025-10-15
 */
@Repository
public interface ZdataTrailFittingMapper extends BaseMapper<ZdataTrailFitting> {
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
