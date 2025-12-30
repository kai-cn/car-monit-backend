package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.domain.CarConfimFree;
import com.ruoyi.manager.domain.CarInfo;
import com.ruoyi.manager.domain.vo.PCCarStatisticsDetailVO;
import com.ruoyi.manager.domain.vo.PCCarStatisticsVO;
import com.ruoyi.manager.domain.vo.bigscreen.CarStatisticsVO;
import com.ruoyi.manager.mapper.CarConfimFreeMapper;
import com.ruoyi.manager.mapper.CarExceptRecordMapper;
import com.ruoyi.manager.domain.CarExceptRecord;
import com.ruoyi.manager.service.ICarExceptRecordService;
import com.ruoyi.manager.service.ICarInfoService;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 异常车辆流水Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class CarExceptRecordServiceImpl extends ServiceImpl<CarExceptRecordMapper, CarExceptRecord> implements ICarExceptRecordService {

    @Autowired
    private CarExceptRecordMapper carExceptRecordMapper;

    @Autowired
    private CarConfimFreeMapper carConfimFreeMapper;
    
    @Autowired
    private ICarInfoService carInfoService;
    

    /**
     * 查询异常车辆流水
     *
     * @param id 异常车辆流水ID
     * @return 异常车辆流水
     */
    @Override
    public CarExceptRecord selectCarExceptRecordById(String id) {
        return carExceptRecordMapper.selectCarExceptRecordById(id);
    }

    /**
     * 查询异常车辆流水列表
     *
     * @param carExceptRecord 异常车辆流水
     * @return 异常车辆流水
     */
    @Override
    public List<CarExceptRecord> selectCarExceptRecordList(CarExceptRecord carExceptRecord) {
        return carExceptRecordMapper.selectCarExceptRecordList(carExceptRecord);
    }


    /**
     * 新增或者修改异常车辆流水
     *
     * @param carExceptRecord 异常车辆流水
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarExceptRecord(CarExceptRecord carExceptRecord)
    {
        // 判断区间是否重复
        if (null != carExceptRecord.getInTime() && (null != carExceptRecord.getOutTime())) {
            int countTimeNum = carExceptRecordMapper.isExitsTime(carExceptRecord);
            if (countTimeNum > 0){
                return  AjaxResult.error("录入区间时间重复！");
            }
        }

        if (CommonUtil.isNotBlank(carExceptRecord.getId()))
        {
            // 修改
            carExceptRecordMapper.updateById(carExceptRecord);
        }
        else
        {
            carExceptRecord.setStatus("0");
            // 新增 主键
            carExceptRecordMapper.insert(carExceptRecord);
        }





        return AjaxResult.success("操作成功！",carExceptRecord.getId());
    }

    /**
     * 批量删除异常车辆流水
     *
     * @param ids 需要删除的异常车辆流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarExceptRecordByIds(String[] ids)
    {
        // 判断是否有补缴记录----------------
        int count = 0;
        if (null != ids && ids.length > 0) {
            List<String> exceptIdList = new ArrayList<>();
            for (String str : ids) {
                exceptIdList.add(str);
            }
            List<CarConfimFree> carConfimFreelist = carConfimFreeMapper.selectCarConfimFreeByExceptIds(exceptIdList);
            if (null != carConfimFreelist && carConfimFreelist.size() > 0) {
                return AjaxResult.error("删除失败，车辆异常流水已补缴！");
            }
            count = carExceptRecordMapper.deleteCarExceptRecordByIds(ids);
        }

        return AjaxResult.success(count);
    }

    @Override
    public void updateStatusByExceptId(List<String> exceptIdList, String status) {
        carExceptRecordMapper.updateStatusByExceptId(exceptIdList, status);
    }

    /**
     * 删除异常车辆流水信息
     *
     * @param id 异常车辆流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarExceptRecordById(String id)
    {
        int count = carExceptRecordMapper.deleteCarExceptRecordById(id);
        return AjaxResult.success(count);
    }

    /**
     * 批量删除异常车辆流水：根据车俩删除异常流水
     *
     * @param fkId
     * @return 结果
     */
    public AjaxResult deleteCarExceptRecordByCarId(String fkId){
        int count = carExceptRecordMapper.deleteCarExceptRecordByCarId(fkId);
        return AjaxResult.success(count);
    }

    /**
     * 根据车牌号统计
     *
     * @param carExceptRecord  车牌号
     * @return 异常车辆流水
     */
    public CarExceptRecord exceptRecordCount(CarExceptRecord carExceptRecord){
        return carExceptRecordMapper.exceptRecordCount(carExceptRecord);
    }

    @Override
    public PCCarStatisticsVO buildPCCarStatisticsVO(List<String> ids, String escapedType) {
        PCCarStatisticsVO vo = new PCCarStatisticsVO();
        List<CarStatisticsVO> carStatisticsVOList = carExceptRecordMapper.buildPCCarStatisticsVO(ids, escapedType);
        Map<String, CarStatisticsVO> voMap = carStatisticsVOList.stream().collect(Collectors.toMap(CarStatisticsVO::getEscapedType, v -> v));
        CarStatisticsVO vo1 = voMap.get("10");
        CarStatisticsVO vo2 = voMap.get("20");
        CarStatisticsVO vo3 = voMap.get("30");
        CarStatisticsVO vo4 = voMap.get("40");
        CarStatisticsVO vo5 = voMap.get("50");
        Integer totalNum = 0;
        BigDecimal totalAmount = BigDecimal.ZERO;
        if(vo1 != null) {
            if(vo1.getNumber() != null) {
                totalNum += vo1.getNumber();
                vo.setEscapedType10Num(vo1.getNumber());
            }
            if(vo1.getEscapedAmount() != null) {
                totalAmount = totalAmount.add(vo1.getEscapedAmount());
                vo.setEscapedType10Amount(vo1.getEscapedAmount());
            }
        }
        if(vo2 != null) {
            if(vo2.getNumber() != null) {
                totalNum += vo2.getNumber();
                vo.setEscapedType20Num(vo2.getNumber());
            }
            if(vo2.getEscapedAmount() != null) {
                totalAmount = totalAmount.add(vo2.getEscapedAmount());
                vo.setEscapedType20Amount(vo2.getEscapedAmount());
            }
        }
        if(vo3 != null) {
            if(vo3.getNumber() != null) {
                totalNum += vo3.getNumber();
                vo.setEscapedType30Num(vo3.getNumber());
            }
            if(vo3.getEscapedAmount() != null) {
                totalAmount = totalAmount.add(vo3.getEscapedAmount());
                vo.setEscapedType30Amount(vo3.getEscapedAmount());
            }
        }
        if(vo4 != null) {
            if(vo4.getNumber() != null) {
                totalNum += vo4.getNumber();
                vo.setEscapedType40Num(vo4.getNumber());
            }
            if(vo4.getEscapedAmount() != null) {
                totalAmount = totalAmount.add(vo4.getEscapedAmount());
                vo.setEscapedType40Amount(vo4.getEscapedAmount());
            }
        }
        if(vo5 != null) {
            if(vo5.getNumber() != null) {
                totalNum += vo5.getNumber();
                vo.setEscapedType50Num(vo5.getNumber());
            }
            if(vo5.getEscapedAmount() != null) {
                totalAmount = totalAmount.add(vo5.getEscapedAmount());
                vo.setEscapedType50Amount(vo5.getEscapedAmount());
            }
        }
        vo.setTotalNum(totalNum);
        vo.setTotalAmount(totalAmount);
        return vo;
    }

    @Override
    public List<PCCarStatisticsDetailVO> buildPCCarStatisticsVODetail(List<String> ids, String escapedType) {
        List<PCCarStatisticsDetailVO>  carStatisticsVOList =  carExceptRecordMapper.buildPCCarStatisticsVODetail(ids, escapedType);
        return carStatisticsVOList;
    }

    @Override
    public String getConfirmId(String id) {
        List<CarConfimFree> carConfimFreeList = carConfimFreeMapper.selectCarConfimFreeByExceptIds(Collections.singletonList(id));
        if(CollectionUtils.isNotEmpty(carConfimFreeList)){
            return carConfimFreeList.get(0).getId();
        }
        return "-1";
    }


    /**
     * 统计车辆逃费类型
     *
     * @param carExceptRecord  车牌号
     * @return 异常车辆流水
     */
    @Override
    public void saveCarExcept(CarExceptRecord carExceptRecord){
        List<CarExceptRecord>  list = carExceptRecordMapper.exceptRecordList(carExceptRecord);
        List<CarInfo> updatalist = new ArrayList<CarInfo>();
        List<CarInfo> carList = carInfoService.selectCarInfoList(new CarInfo());
        Map<String, CarInfo> carMap = new HashMap<>();
        for (CarInfo carRtn : carList) {
            carMap.put(CommonUtil.isNull(carRtn.getCarNo()),carRtn);
        }
        for (CarExceptRecord carExceptRecord1 : list) {
            CarInfo uptcarInfo = new CarInfo();
            String carNo = CommonUtil.isNull(carExceptRecord1.getCarNo());
            
            if (CommonUtil.isNotBlank(carNo)){
                if (carMap.containsKey(carNo)) {
                    CarInfo carInfo = carMap.get(carNo);
                    uptcarInfo.setId(carInfo.getId());
                    uptcarInfo.setEscapedType(carExceptRecord1.getEscapedType());
                    uptcarInfo.setEscapedAmount(carExceptRecord1.getExceptAmount());
                    updatalist.add(uptcarInfo);
                }
            }
        }
        if (updatalist.size() > 0){
            carInfoService.updateBatchById(updatalist);
        }
        
        
        
        
        
        
        
        
        
        
        
        
        
    }
}
