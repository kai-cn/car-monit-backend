package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.base.domain.TrailBo;
import com.ruoyi.base.domain.TrailInfo;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.manager.domain.CarWarningInfo;
import com.ruoyi.manager.domain.CarWhiteInfo;
import com.ruoyi.manager.domain.vo.bigscreen.CarLocationParam;
import com.ruoyi.manager.mapper.CarWarningInfoMapper;
import com.ruoyi.manager.service.ICarWarningInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

/**
 * 预警车辆Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class CarWarningInfoServiceImpl extends ServiceImpl<CarWarningInfoMapper, CarWarningInfo> implements ICarWarningInfoService {

    @Autowired
    private CarWarningInfoMapper carWarningInfoMapper;

    @Autowired
    private RedisCache redisCache;

    /**
     * 查询预警车辆
     *
     * @param id 预警车辆ID
     * @return 预警车辆
     */
    @Override
    public CarWarningInfo selectCarWarningInfoById(String id) {
        CarWarningInfo rtn = carWarningInfoMapper.selectCarWarningInfoById(id);
        if (rtn !=null){
           String carNo = CommonUtil.isNull(rtn.getCarNo());
            String nextKey = Constants.car_history_trail + carNo;
            // 当前进入门架的时间-----------------------
            String gantryStationId = CommonUtil.isNull(rtn.getGantryStationId());


            List<TrailInfo> trailInfoList = redisCache.getCacheObject(nextKey);
            List<TrailBo> nextBoList = new ArrayList<>();
            if (null != trailInfoList && trailInfoList.size() > 0) {
                List<List<TrailBo>> cylylist = new ArrayList<>();
                // 找到下一个位置
                for (TrailInfo trailInfo : trailInfoList) {
                    List<TrailBo> trailList = trailInfo.getTrailList();
                    // 循环轨迹
                    if (null != trailList && trailList.size() > 0) {
                        for (int yy = 0; yy < trailList.size(); yy++) {
                            TrailBo trailBo = trailList.get(yy);
                            String curDevCode = CommonUtil.isNull(trailBo.getDevCode());
                            if (gantryStationId.equals(curDevCode)) {
                                cylylist.add(trailList);
                            }
                        }
                    }
                }

                // 循环cylylist
                for (List<TrailBo> list : cylylist) {
                    for (TrailBo trailBo : list) {
                        if("ServiceAreaCapture".equals(trailBo.getStateType())){

                        }
                    }
                }


            }

        }
        return rtn;
    }

    /**
     * 查询预警车辆列表
     *
     * @param carWarningInfo 预警车辆
     * @return 预警车辆
     */
    @Override
    public List<CarWarningInfo> selectCarWarningInfoList(CarWarningInfo carWarningInfo) {
        return carWarningInfoMapper.selectCarWarningInfoList(carWarningInfo);
    }


    /**
     * 新增或者修改预警车辆
     *
     * @param carWarningInfo 预警车辆
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarWarningInfo(CarWarningInfo carWarningInfo)
    {
        Long userId = 1L;
        if (CommonUtil.isNotBlank(carWarningInfo.getId()))
        {
            carWarningInfo.setUpdateBy(userId); // 更新人
            carWarningInfo.setUpdateTime(DateUtils.getTimestamp()); // 更新时间
            // 修改
            carWarningInfoMapper.updateById(carWarningInfo);
        }
        else
        {
            carWarningInfo.setDelFlag("0");
            carWarningInfo.setCreateBy(userId); // 创建人
            carWarningInfo.setCreateTime(DateUtils.getTimestamp()); // 创建时间
            carWarningInfo.setUpdateBy(userId); // 更新人
            carWarningInfo.setUpdateTime(DateUtils.getTimestamp()); // 更新时间
            // 新增 主键
            carWarningInfoMapper.insert(carWarningInfo);
        }
        return AjaxResult.success("操作成功！",carWarningInfo.getId());
    }

    /**
     * 批量删除预警车辆
     *
     * @param ids 需要删除的预警车辆ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarWarningInfoByIds(String[] ids)
    {
        int count = carWarningInfoMapper.deleteCarWarningInfoByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除预警车辆信息
     *
     * @param id 预警车辆ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarWarningInfoById(String id)
    {
        int count = carWarningInfoMapper.deleteCarWarningInfoById(id);
        return AjaxResult.success(count);
    }





    /**
     * 批量删除预警车辆
     *
     * @param idList
     * @return 结果
     */
    public AjaxResult deleteCarWarningInfoByUUid(List<String> idList){
        if (null !=idList && idList.size() > 0){
            carWarningInfoMapper.deleteCarWarningInfoByUUid(idList);
        }
        return AjaxResult.success();
    }

    /**
     * 跟新缓存
     */
    public void updateRedisWarningList() {
        CarWhiteInfo carWhiteInfo = new CarWhiteInfo();
        // 查询在线的
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd");
        String formattedDate = sdf.format(new Date());
        CarWarningInfo carWarningInfo = new CarWarningInfo();
        carWarningInfo.setTrackId(formattedDate);
        List<CarWarningInfo> list = carWarningInfoMapper.selectCarWarningInfoListLimit100(carWarningInfo);
        redisCache.setCacheObject(Constants.car_warning_list, list);

    }


    /**
     * 从缓存拿到carlist
     */
    public List<CarWarningInfo> getRedisCarWarningList() {
        List<CarWarningInfo> list = null;
        Object obj = redisCache.getCacheObject(Constants.car_warning_list);
        if (null != obj) {
            list = (List) obj;
        } else {
            // 查询在线的
            SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd");
            String formattedDate = sdf.format(new Date());
            CarWarningInfo carWarningInfo = new CarWarningInfo();
            carWarningInfo.setTrackId(formattedDate);
            list = carWarningInfoMapper.selectCarWarningInfoListLimit100(carWarningInfo);
            redisCache.setCacheObject(Constants.car_warning_list, list);
        }
        return list;
    }

    @Override
    public List<CarWarningInfo> selectCarWarningInfoListLimit100(CarLocationParam param) {
        List<CarWarningInfo> rtnlist = new ArrayList<>();

        List<CarWarningInfo> list = this.getRedisCarWarningList();
        for (CarWarningInfo rtn : list) {
            String devCodes = CommonUtil.isNull(rtn.getTrackNames());
            boolean addFlag = true;
            // 所属路线编码
            addFlag = CommonUtil.isExitsStr(devCodes,param.getRoadCode());
            if(!addFlag){
                continue;
            }

            // 所属路段编码
            addFlag = CommonUtil.isExitsStr(devCodes,param.getSectionCode());
            if(!addFlag){
                continue;
            }

            // 所属收费站编码
            addFlag = CommonUtil.isExitsStr(devCodes,param.getTollCode());
            if(!addFlag){
                continue;
            }
            // 门架编号
            addFlag = CommonUtil.isExitsStr(devCodes,param.getGantryCode());
            if(!addFlag){
                continue;
            }

            // 服务区编码
            addFlag = CommonUtil.isExitsStr(devCodes,param.getFwqbm());
            if(!addFlag){
                continue;
            }

            // 逃费类型
            addFlag = CommonUtil.isExitsStr(rtn.getEscapedType(),param.getEscapedType());
            if(!addFlag){
                continue;
            }

            // 车牌号
            addFlag = CommonUtil.isExitsStr(rtn.getCarNo(),param.getCarNoQuery());
            if(!addFlag){
                continue;
            }


            if (addFlag){
                rtnlist.add(rtn);
            }
        }
        return rtnlist;
    }


}
