package com.ruoyi.manager.service.impl;


import com.alibaba.fastjson2.JSONObject;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.base.service.forest.HttpSysUtilApiService;
import com.ruoyi.common.constant.HttpStatus;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.domain.CarInfo;
import com.ruoyi.manager.domain.CarTrackInfo;
import com.ruoyi.manager.domain.vo.CarParaVO;
import com.ruoyi.manager.domain.vo.CarVO;
import com.ruoyi.manager.mapper.CarTrackInfoMapper;
import com.ruoyi.manager.service.ICarInfoService;
import com.ruoyi.manager.service.ICarTrackInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

/**
 * 车辆行驶轨迹Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class CarTrackInfoServiceImpl extends ServiceImpl<CarTrackInfoMapper, CarTrackInfo> implements ICarTrackInfoService {

    @Autowired
    private CarTrackInfoMapper carTrackInfoMapper;

    @Autowired
    private ICarInfoService carInfoService;

    @Resource
    private HttpSysUtilApiService httpSysUtilApiService;

    /**
     * 查询车辆行驶轨迹
     *
     * @param id 车辆行驶轨迹ID
     * @return 车辆行驶轨迹
     */
    @Override
    public CarTrackInfo selectCarTrackInfoById(String id) {
        return carTrackInfoMapper.selectCarTrackInfoById(id);
    }

    /**
     * 查询车辆行驶轨迹列表
     *
     * @param carTrackInfo 车辆行驶轨迹
     * @return 车辆行驶轨迹
     */
    @Override
    public List<CarTrackInfo> selectCarTrackInfoList(CarTrackInfo carTrackInfo) {
        List<CarTrackInfo> list = carTrackInfoMapper.selectCarTrackInfoList(carTrackInfo);
        if (null != list && list.size() > 0) {
            for (CarTrackInfo rtn : list) {

                if (CommonUtil.isNotBlank(rtn.getLongitude())){
                    rtn.setLongitudeDec(new BigDecimal(rtn.getLongitude()));
                }

                if (CommonUtil.isNotBlank(rtn.getLatitude())){
                    rtn.setLatitudeDec(new BigDecimal(rtn.getLatitude()));
                }
            }
        }
        return list;
    }


    /**
     * 新增或者修改车辆行驶轨迹
     *
     * @param carTrackInfo 车辆行驶轨迹
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarTrackInfo(CarTrackInfo carTrackInfo)
    {
        if (CommonUtil.isNotBlank(carTrackInfo.getId()))
        {
            // 修改
            carTrackInfoMapper.updateById(carTrackInfo);
        }
        else
        {
            // 新增 主键
            carTrackInfoMapper.insert(carTrackInfo);
        }
        return AjaxResult.success("操作成功！",carTrackInfo.getId());
    }

    /**
     * 批量删除车辆行驶轨迹
     *
     * @param ids 需要删除的车辆行驶轨迹ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarTrackInfoByIds(String[] ids)
    {
        int count = carTrackInfoMapper.deleteCarTrackInfoByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除车辆行驶轨迹信息
     *
     * @param id 车辆行驶轨迹ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarTrackInfoById(String id)
    {
        int count = carTrackInfoMapper.deleteCarTrackInfoById(id);
        return AjaxResult.success(count);
    }


    /**
     * 轨迹同步
     *
     * @return 结果
     */
    public AjaxResult sync() {
        // 查询所有的车俩
        List<CarInfo> carList = carInfoService.getRedisCarList();
        List<CarVO> carVOList = new ArrayList<>();
        for (CarInfo rtn : carList) {
            CarVO tempVO = new CarVO();
            tempVO.setCarId(rtn.getId());
            tempVO.setCarNo(rtn.getCarNo());
            carVOList.add(tempVO);
        }
        CarParaVO carParaVO = new CarParaVO();
        carParaVO.setCarlist(carVOList);
        // 调用接口
        JSONObject jsonObject = httpSysUtilApiService.syncTrack(carParaVO);
        Integer responseCode = jsonObject.getInteger(AjaxResult.CODE_TAG);
        if (responseCode != HttpStatus.SUCCESS) {

        }
        return AjaxResult.success(jsonObject);


    }


}
