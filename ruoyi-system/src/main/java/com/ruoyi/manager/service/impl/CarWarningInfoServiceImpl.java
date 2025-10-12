package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
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
        return carWarningInfoMapper.selectCarWarningInfoById(id);
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
            // 所属收费站编码
            if (CommonUtil.isNotBlank(param.getTollCode())){
                if (devCodes.indexOf(param.getTollCode()) == -1){
                    addFlag = false;
                }
            }
            // 门架编号
            if (CommonUtil.isNotBlank(param.getGantryCode())){
                if (devCodes.indexOf(param.getGantryCode()) == -1){
                    addFlag = false;
                }
            }
            // 服务区编码
            if (CommonUtil.isNotBlank(param.getFwqbm())){
                if (devCodes.indexOf(param.getFwqbm()) == -1){
                    addFlag = false;
                }
            }
            // 所属路线编码
            if (CommonUtil.isNotBlank(param.getRoadCode())){
                if (devCodes.indexOf(param.getRoadCode()) == -1){
                    addFlag = false;
                }
            }

            // 所属路段编码
            if (CommonUtil.isNotBlank(param.getSectionCode())){
                if (devCodes.indexOf(param.getSectionCode()) == -1){
                    addFlag = false;
                }
            }

            // 逃费类型
            if (CommonUtil.isNotBlank(param.getEscapedType())){
                if (CommonUtil.isNull(rtn.getEscapedType()).indexOf(param.getEscapedType()) == -1){
                    addFlag = false;
                }
            }
            // 车牌号
            if (CommonUtil.isNotBlank(param.getCarNoQuery())){
                if (CommonUtil.isNull(rtn.getCarNo()).indexOf(param.getCarNoQuery()) == -1){
                    addFlag = false;
                }
            }
            if (addFlag){
                rtnlist.add(rtn);
            }
        }
        return rtnlist;
    }


}
