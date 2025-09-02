package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.CarInfo;
import com.ruoyi.manager.domain.vo.bigscreen.CarInfoVO;
import com.ruoyi.manager.domain.vo.bigscreen.CarLocationParam;
import com.ruoyi.manager.domain.vo.bigscreen.CarLocationVO;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 车辆信息Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Repository
public interface CarInfoMapper extends BaseMapper<CarInfo> {
    /**
     * 查询车辆信息
     *
     * @param id 车辆信息ID
     * @return 车辆信息
     */
    CarInfo selectCarInfoById(String id);

    /**
     * 查询车辆信息列表
     *
     * @param carInfo 车辆信息
     * @return 车辆信息集合
     */
    List<CarInfo> selectCarInfoList(CarInfo carInfo);

    /**
     * 批量删除车辆信息
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteCarInfoByIds(String[] ids);


    /**
     * 判断车牌号是否重复
     *
     * @param carInfo 车辆信息
     * @return 车辆信息集合
     */
    int isExitsCar(CarInfo carInfo);

    /**
     * 删除车辆信息
     *
     * @param id 车辆信息ID
     * @return 结果
     */
    int deleteCarInfoById(String id);

    List<CarLocationVO> getCarLocation(CarLocationParam carInfo);

    List<CarInfoVO> selectCarVoList();
}
