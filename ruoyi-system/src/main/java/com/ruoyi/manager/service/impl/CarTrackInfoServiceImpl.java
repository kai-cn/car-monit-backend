package com.ruoyi.manager.service.impl;


import com.alibaba.fastjson2.JSON;
import com.alibaba.fastjson2.JSONObject;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowProvcaptureAddcode;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowStationcaptureAddcode;
import com.ruoyi.base.domain.OdsSzdnProvinceBorderVehicleWeightNewstructure;
import com.ruoyi.base.service.forest.HttpSysUtilApiService;
import com.ruoyi.common.constant.HttpStatus;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.domain.CarInfo;
import com.ruoyi.manager.domain.CarTrackInfo;
import com.ruoyi.manager.domain.vo.CarParaVO;
import com.ruoyi.manager.domain.vo.CarVO;
import com.ruoyi.manager.domain.vo.TrailBo;
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
import java.util.Map;

/**
 * 车辆行驶轨迹Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class CarTrackInfoServiceImpl extends ServiceImpl<CarTrackInfoMapper, CarTrackInfo> implements ICarTrackInfoService {


    public static final String BORDER_WEIGHING_CAPTURE = "BorderWeighingCapture";
    public static final String GANTRY_CAPTURE = "GantryCapture";
    public static final String PROV_CAPTURE = "ProvCapture";
    public static final String SERVICE_AREA_CAPTURE = "ServiceAreaCapture";
    public static final String STATION_CAPTURE = "StationCapture";


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
    @Transactional(rollbackFor = Exception.class)
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
        if (responseCode == HttpStatus.SUCCESS) {
            JSONObject dataJosn = jsonObject.getJSONObject("data");
            if (null !=dataJosn){
                Map<String, List<TrailBo>> mapCar = (Map) dataJosn;
                for (Map.Entry<String, List<TrailBo>> entry : mapCar.entrySet()) {
                    String carNo = entry.getKey();
                    List<TrailBo> josnList = entry.getValue();
                    if (null != josnList && josnList.size() > 0) {
                        //---------------有轨迹 ：根据车俩实时状态
                        for (TrailBo trailBo : josnList) {
                            String pointFlag = CommonUtil.isNull(trailBo.getPointFlag()); // 是否有值 O否 1是
                            String stateType = CommonUtil.isNull(trailBo.getStateType());  // 流水来源类型标识:可作为维度字段，用于回溯数据来源、确定查找目标表
                            String ipType = CommonUtil.isNull(trailBo);

                            //--------------------- 抓拍对象
                            if (pointFlag.equals("1")){
                                switch (stateType) {
                                    case BORDER_WEIGHING_CAPTURE:
                                        // 省界称重
                                        OdsSzdnProvinceBorderVehicleWeightNewstructure  borderWeighingCaptureBO = trailBo.getBorderWeighingCaptureBO();
                                        break;
                                    case GANTRY_CAPTURE:
                                        // 门架抓拍

                                        break;
                                    case PROV_CAPTURE:
                                        // 省界抓拍

                                        break;
                                    case SERVICE_AREA_CAPTURE:
                                        // 服务区抓拍
                                        break;
                                    case STATION_CAPTURE:
                                        // 收费站抓拍

                                        break;
                                }

                            }
                        }
                    }else{
                        // 跟新车俩-----------------------
                    }


                }
            }
        }
        return AjaxResult.success(jsonObject);


    }

    /**
     * 可疑车俩
     *
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult syncSuspiciousCar() {
        CarParaVO carParaVO = new CarParaVO();
        // 调用接口
        JSONObject jsonObject = httpSysUtilApiService.syncSuspiciousCar(carParaVO);
        return AjaxResult.success(jsonObject);
    }

}
