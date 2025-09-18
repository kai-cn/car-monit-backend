package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.manager.domain.CarInfo;
import com.ruoyi.manager.domain.vo.bigscreen.CarInfoVO;
import com.ruoyi.manager.domain.vo.bigscreen.CarLocationParam;
import com.ruoyi.manager.domain.vo.bigscreen.CarLocationVO;
import com.ruoyi.manager.mapper.CarInfoMapper;
import com.ruoyi.manager.service.ICarInfoService;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

/**
 * 车辆信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class CarInfoServiceImpl extends ServiceImpl<CarInfoMapper, CarInfo> implements ICarInfoService {


    @Autowired
    private RedisCache redisCache;


    @Autowired
    private CarInfoMapper carInfoMapper;

    /**
     * 查询车辆信息
     *
     * @param id 车辆信息ID
     * @return 车辆信息
     */
    @Override
    public CarInfo selectCarInfoById(String id) {
        return carInfoMapper.selectCarInfoById(id);
    }

    /**
     * 查询车辆信息列表
     *
     * @param carInfo 车辆信息
     * @return 车辆信息
     */
    @Override
    public List<CarInfo> selectCarInfoList(CarInfo carInfo) {
        return carInfoMapper.selectCarInfoList(carInfo);
    }


    /**
     * 新增或者修改车辆信息
     *
     * @param carInfo 车辆信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarInfo(CarInfo carInfo)
    {
        carInfo.setCarNo(CommonUtil.isNull(carInfo.getCarNo())); //去掉空格
        // 判断车牌号是否重复
        int countNum = carInfoMapper.isExitsCar(carInfo);
        if (countNum > 0){
            return AjaxResult.error("车牌号存在重复，请确定！");
        }

        if (CommonUtil.isNotBlank(carInfo.getId()))
        {
            // 修改
            carInfoMapper.updateById(carInfo);
        }
        else
        {
            carInfo.setId(StringUtils.getUUID()); // 主键
            // 新增 主键
            carInfoMapper.insert(carInfo);
        }
        this.updateRedisCarList();
        return AjaxResult.success("操作成功！",carInfo.getId());
    }

    /**
     * 批量删除车辆信息
     *
     * @param ids 需要删除的车辆信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarInfoByIds(String[] ids)
    {
        int count = carInfoMapper.deleteCarInfoByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除车辆信息信息
     *
     * @param id 车辆信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarInfoById(String id)
    {
        int count = carInfoMapper.deleteCarInfoById(id);
        this.updateRedisCarList();
        return AjaxResult.success(count);
    }


    /**
     * 导入
     *
     * @param list
     * @return
     */
    public AjaxResult doImport(List<CarInfo> list) {
        if (null != list && list.size() > 0) {
            List<CarInfo> addlist = new ArrayList<CarInfo>();
            List<CarInfo> updatalist = new ArrayList<CarInfo>();
            for (CarInfo carInfo : list) {
                if (CommonUtil.isNotBlank(carInfo.getId())){
                    updatalist.add(carInfo);
                }else{
                    carInfo.setId(StringUtils.getUUID()); // 主键
                    addlist.add(carInfo);
                }
            }

            // 新增
            if (addlist.size() > 0) {
                this.saveBatch(addlist);
            }
            // 修改
            if (updatalist.size() > 0) {
                this.updateBatchById(updatalist);
            }
        }
        this.updateRedisCarList();
        return AjaxResult.success();
    }

    /**
     * 地图 ；车俩地图描点
     */
    @Override
    public List<CarLocationVO> carLocation(CarLocationParam carInfo) {
        List<CarLocationVO> carLocation = carInfoMapper.getCarLocation(carInfo);
        if(CollectionUtils.isNotEmpty(carLocation)) {
            for (CarLocationVO carLocationVO : carLocation) {
                if(CommonUtil.isNotBlank(carLocationVO.getLonStr())) {
                    carLocationVO.setLon(new BigDecimal(carLocationVO.getLonStr()));
                }
                if(CommonUtil.isNotBlank(carLocationVO.getLatStr())) {
                    carLocationVO.setLat(new BigDecimal(carLocationVO.getLatStr()));
                }
            }
        }
        return carLocation;
    }

    /**
     * 地图：重点车辆库统计 前10条
     * @return
     */
    @Override
    public List<CarInfoVO> selectCarVoList() {
        return carInfoMapper.selectCarVoList();
    }

    /**
     * 跟新缓存
     */
    public void updateRedisCarList() {
        CarInfo carInfoQuery = new CarInfo();
        List<CarInfo> list = carInfoMapper.selectCarInfoList(carInfoQuery);
        redisCache.setCacheObject(Constants.car_list, list);
    }


    /**
     * 从缓存拿到carlist
     */
    public List<CarInfo> getRedisCarList() {
        List<CarInfo> list = null;
        Object obj = redisCache.getCacheObject(Constants.car_list);
        if (null != obj) {
            list = (List) obj;
        } else {
            CarInfo carInfo = new CarInfo();
            list = carInfoMapper.selectCarInfoList(carInfo);
            redisCache.setCacheObject(Constants.car_list, list);
        }
        return list;
    }


}
