package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.domain.entity.SysDictData;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.manager.domain.CarAduitFree;
import com.ruoyi.manager.domain.CarConfimFree;
import com.ruoyi.manager.domain.CarExceptRecord;
import com.ruoyi.manager.domain.CarSuspicious;
import com.ruoyi.manager.domain.vo.CarConfimFreeQueryRo;
import com.ruoyi.manager.domain.vo.PCCarStatisticsDetailVO;
import com.ruoyi.manager.domain.vo.PCCarStatisticsVO;
import com.ruoyi.manager.domain.vo.bigscreen.CarStatisticsVO;
import com.ruoyi.manager.domain.vo.bigscreen.IncomeStatisticParam;
import com.ruoyi.manager.mapper.CarConfimFreeMapper;
import com.ruoyi.manager.mapper.CarSuspiciousMapper;
import com.ruoyi.manager.service.ICarAduitFreeService;
import com.ruoyi.manager.service.ICarConfimFreeService;
import com.ruoyi.manager.service.ICarExceptRecordService;
import com.ruoyi.system.service.ISysDictDataService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.CollectionUtils;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 确认补缴Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-28
 */
@Service
public class CarConfimFreeServiceImpl extends ServiceImpl<CarConfimFreeMapper, CarConfimFree> implements ICarConfimFreeService {

    @Autowired
    private CarConfimFreeMapper carConfimFreeMapper;
    @Autowired
    private ISysDictDataService sysDictDataService;

    @Autowired
    private ICarAduitFreeService carAduitFreeService;

    @Autowired
    private ICarExceptRecordService carExceptRecordService;

    @Autowired
    private CarSuspiciousMapper carSuspiciousMapper;


    /**
     * 查询确认补缴
     *
     * @param id 确认补缴ID
     * @return 确认补缴
     */
    @Override
    public CarConfimFree selectCarConfimFreeById(String id) {
        CarConfimFree carConfimFree = carConfimFreeMapper.selectCarConfimFreeById(id);

        if (null != carConfimFree && CommonUtil.isNotBlank(carConfimFree.getId())){
            // 通过异常IDS查询异常列表
            String exceptIds = CommonUtil.deleteEnd(carConfimFree.getExceptIds());
            if (CommonUtil.isNotBlank(exceptIds)){
                CarExceptRecord carExceptRecord = new CarExceptRecord();
                carExceptRecord.setExceptIds(exceptIds);
                List<CarExceptRecord> carExceptRecordList = carExceptRecordService.selectCarExceptRecordList(carExceptRecord);
                carConfimFree.setCarExceptRecordList(carExceptRecordList);

                BigDecimal totalAmount = BigDecimal.ZERO;
                BigDecimal chargeAmount = BigDecimal.ZERO;
                BigDecimal difAmount = BigDecimal.ZERO;
                for (CarExceptRecord record : carExceptRecordList) {
                    if (null != record.getDifAmount()){
                        difAmount = difAmount.add(record.getDifAmount());
                    }
                }
                // 判断大于0
                if (difAmount.compareTo(BigDecimal.ZERO) != 0) {
                    difAmount = difAmount.setScale(2, RoundingMode.HALF_UP);
                }
                carConfimFree.setDifAmount(difAmount);

            }

            // 处理
            CarAduitFree carAduitFree = new CarAduitFree();
            carAduitFree.setConfirmId(id);
            List<CarAduitFree> carAduitFreeList = carAduitFreeService.selectCarAduitFreeList(carAduitFree);
            carConfimFree.setCarAduitFreeList(carAduitFreeList);
        }
        return carConfimFree;
    }

    /**
     * 查询确认补缴列表
     *
     * @param carConfimFree 确认补缴
     * @return 确认补缴
     */
    @Override
    public List<CarConfimFree> selectCarConfimFreeList(CarConfimFree carConfimFree) {
        return carConfimFreeMapper.selectCarConfimFreeList(carConfimFree);
    }


    /**
     * 新增或者修改确认补缴
     *
     * @param carConfimFree 确认补缴
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarConfimFree(CarConfimFree carConfimFree) {

        String exceptIds = CommonUtil.deleteEnd(carConfimFree.getExceptIds());
        if(CommonUtil.isBlank(exceptIds)){
            return AjaxResult.error("请选择车辆异常流水！");
        }
        List<String> exceptIdList = Arrays.asList(exceptIds.split(","));

        if (CommonUtil.isBlank(carConfimFree.getId())) {
            List<CarConfimFree> carConfimFreelist = carConfimFreeMapper.selectCarConfimFreeByExceptIds(exceptIdList);
            if (null != carConfimFreelist && carConfimFreelist.size() > 0) {
                return AjaxResult.error("车辆补缴单已追缴，请勿重复补缴！");
            }
        }

        // 修改异常车俩核实状态
        CarExceptRecord carExceptRecord = new CarExceptRecord();
        carExceptRecord.setExceptIds(exceptIds);
        List<CarExceptRecord> carExceptRecordList = carExceptRecordService.selectCarExceptRecordList(carExceptRecord);

        BigDecimal difAmount = BigDecimal.ZERO;
        for (CarExceptRecord record : carExceptRecordList) {
            if (null != record.getDifAmount()){
                difAmount = difAmount.add(record.getDifAmount());
            }
        }
        // 判断大于0
        if (difAmount.compareTo(BigDecimal.ZERO) != 0) {
            difAmount = difAmount.setScale(2, RoundingMode.HALF_UP);
        }



        // 修改明细
        BigDecimal processingAmount = BigDecimal.ZERO;
        String escapedTypes = "";
        List<CarAduitFree> carAduitFreeList = carConfimFree.getCarAduitFreeList();
        if (null != carAduitFreeList && carAduitFreeList.size() > 0) {
            // 将处理金额进行累加
            processingAmount = carAduitFreeList.stream()
                    .map(CarAduitFree::getAmount)
                    .filter(Objects::nonNull)
                    .reduce(BigDecimal.ZERO, BigDecimal::add);
            carConfimFree.setAduitAmount(processingAmount);

            escapedTypes = carExceptRecordList.stream().map(CarExceptRecord::getEscapedType).collect(Collectors.joining(","));
            carConfimFree.setEscapedTypes(escapedTypes);

        }


        // 判断金额是否一致
        BigDecimal amount =  BigDecimal.ZERO;
        BigDecimal aduitAmount =  BigDecimal.ZERO;

        if (null != carConfimFree.getAmount()) {
            amount = carConfimFree.getAmount();
        }

        if (null != carConfimFree.getAduitAmount()) {
            aduitAmount = carConfimFree.getAduitAmount();
        }






        String comfimFreeType = CommonUtil.isNull(carConfimFree.getComfimFreeType());

        if (!comfimFreeType.equals("waibu")){
            BigDecimal yzNum = (amount.add(aduitAmount)).setScale(2, RoundingMode.HALF_UP);
            if (yzNum.compareTo(difAmount) == 0) {
            }else{
                return AjaxResult.error("录入信息的拆分金额和处理信息的拆分金额合计不等于逃费金额！");
            }
        }


        if (CommonUtil.isNotBlank(carConfimFree.getId())) {
            // 修改
            carConfimFreeMapper.updateById(carConfimFree);
        } else {
            carConfimFree.setStatus("0");
            if (comfimFreeType.equals("waibu")){
                carConfimFree.setStatus("1");
            }
            // 新增 主键
            carConfimFreeMapper.insert(carConfimFree);
        }


        if (comfimFreeType.equals("waibu")){
            //  外部补缴------------------------
            // 修改异常流水状态
            carExceptRecordService.updateStatusByExceptId(exceptIdList, "1");


            for (CarExceptRecord ex : carExceptRecordList){
                if (CommonUtil.isNotBlank(ex.getCarId())){
                    CarSuspicious exupdatebo = new CarSuspicious();
                    exupdatebo.setId(ex.getCarId());
                    exupdatebo.setStatus("1");
                    carSuspiciousMapper.updateById(exupdatebo);
                }
            }
        }else{
            // 内部补缴------------------------
            if (null != carAduitFreeList && carAduitFreeList.size() > 0) {
                // 先删除
                carAduitFreeService.deleteCarAduitFreeByConfirmId(carConfimFree.getId());
                // 后新增
                carAduitFreeList.forEach(item -> {
                    item.setConfirmId(carConfimFree.getId());
                    item.setCarId(carConfimFree.getCarNo());
                    item.setCarType(carConfimFree.getCarType());
                    item.setCarVehicle(carConfimFree.getCarVehicle());
                    item.setCarNo(carConfimFree.getCarNo());
                    item.setDelFlag("0");
                    item.setCreateTime(DateUtils.getTimestamp());
                    item.setUpdateTime(DateUtils.getTimestamp());
                });
                this.carAduitFreeService.saveBatch(carAduitFreeList);

                // 更新补缴状态
               /* int comparison = carConfimFree.getAmount().compareTo(processingAmount);
                String status = comparison == 0 ? "2" : comparison > 0 ? "1" : "0";*/

                // 修改异常流水状态
                carExceptRecordService.updateStatusByExceptId(exceptIdList, "1");

                for (CarExceptRecord ex : carExceptRecordList){
                    if (CommonUtil.isNotBlank(ex.getCarId())){
                        CarSuspicious exupdatebo = new CarSuspicious();
                        exupdatebo.setId(ex.getCarId());
                        exupdatebo.setStatus("1");
                        carSuspiciousMapper.updateById(exupdatebo);
                    }
                }
            }
        }

        return AjaxResult.success("操作成功！", carConfimFree.getId());
    }

    /**
     * 批量删除确认补缴
     *
     * @param ids 需要删除的确认补缴ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarConfimFreeByIds(String[] ids) {
        // 通过ids 查询
        int count = 0;
        if (null != ids && ids.length > 0) {

            String exceptIds = "";
            for (String id : ids) {
                CarConfimFree carConfimFree = carConfimFreeMapper.selectCarConfimFreeById(id);
                if (null != carConfimFree && CommonUtil.isNotBlank(carConfimFree.getExceptIds())) {
                    exceptIds += CommonUtil.deleteEnd(carConfimFree.getExceptIds())+",";
                }

                // 删除明细-----------
                carAduitFreeService.deleteCarAduitFreeByConfirmId(id);
            }
            exceptIds = CommonUtil.deleteEnd(exceptIds);
            if (CommonUtil.isNotBlank(exceptIds)) {
                List<String> exceptIdList = Arrays.asList(exceptIds.split(","));
                // 修改异常流水状态
                carExceptRecordService.updateStatusByExceptId(exceptIdList, "0");
            }
            // 删除流水
            count = carConfimFreeMapper.deleteCarConfimFreeByIds(ids);
        }

        return AjaxResult.success(count);
    }

    /**
     * 删除确认补缴信息
     *
     * @param id 确认补缴ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarConfimFreeById(String id) {
        int count = carConfimFreeMapper.deleteCarConfimFreeById(id);
        return AjaxResult.success(count);
    }

    @Override
    public List<CarStatisticsVO> getCarStatistics(IncomeStatisticParam param) {
        // 逃费类型
        SysDictData sysDictData = new SysDictData();
        sysDictData.setDictType("escaped_type");
        List<SysDictData> dictDataList = sysDictDataService.selectDictDataList(sysDictData);
        List<CarStatisticsVO> list = carConfimFreeMapper.getCarStatistics(param);
        Map<String, CarStatisticsVO> voMap = list.stream().collect(Collectors.toMap(CarStatisticsVO::getEscapedType, v -> v));
        List<CarStatisticsVO> res = new ArrayList<>();
        dictDataList.forEach((item) -> {
            CarStatisticsVO vo = new CarStatisticsVO();
            res.add(vo);
            vo.setEscapedType(item.getDictValue());
            vo.setEscapedTypeName(item.getDictLabel());
            CarStatisticsVO vo1 = voMap.get(vo.getEscapedType());
            if (vo1 != null) {
                vo.setNumber(vo1.getNumber());
                vo.setEscapedAmount(vo1.getEscapedAmount());
            }
        });
        return res;
    }

    @Override
    public CarStatisticsVO getCarConfirm(IncomeStatisticParam param) {
        return carConfimFreeMapper.getCarConfirm(param);
    }

    @Override
    public String selectOrgId(String carId, String id) {
        return carConfimFreeMapper.selectOrgId(carId, id);
    }

    /**
     * 查询确认补缴
     *
     * @param exceptIds
     * @return 确认补缴
     */
    public AjaxResult selectCarConfimFreeByExceptIds(String exceptIds) {

        CarConfimFree carConfimFree = new CarConfimFree();

        exceptIds = CommonUtil.deleteEnd(exceptIds); // 去掉空格
        if(CommonUtil.isBlank(exceptIds)){
            return AjaxResult.error("请选择车辆异常流水！");
        }

        // 通过异常IDS查询异常列表
        CarExceptRecord carExceptRecord = new CarExceptRecord();
        carExceptRecord.setExceptIds(exceptIds);
        List<CarExceptRecord> carExceptRecordList = carExceptRecordService.selectCarExceptRecordList(carExceptRecord);
        carConfimFree.setCarExceptRecordList(carExceptRecordList);

        if(null !=carExceptRecordList && carExceptRecordList.size() > 0){
        }else{
            return AjaxResult.error("异常车辆流水不存在！");
        }

        List<String> carNoList = carExceptRecordList.stream().map(CarExceptRecord::getCarNo).distinct().collect(Collectors.toList());
        if(carNoList.size() > 1){
            return AjaxResult.error("请勿选择多辆车！");
        }

        List<Long> epsList = carExceptRecordList.stream().map(CarExceptRecord::getEpsId).distinct().collect(Collectors.toList());
        if(epsList.size() > 1){
            return AjaxResult.error("选择的异常流水存在多个录入单位，请确认！");
        }else{
            if (epsList.size() > 0){
                carConfimFree.setOrgId(epsList.get(0)+"");  // 录入单位
            }
        }


        List<String> exceptIdList = Arrays.asList(exceptIds.split(","));
        List<CarConfimFree> list = carConfimFreeMapper.selectCarConfimFreeByExceptIds(exceptIdList);
        if (null != list && list.size() > 0) {
            return AjaxResult.error("车辆补缴单已追缴，请勿重复补缴！");
        }

        CarExceptRecord CarExceptRecordRtn = carExceptRecordList.get(0);

        carConfimFree.setCarId(CarExceptRecordRtn.getCarId());
        carConfimFree.setCarNo(CarExceptRecordRtn.getCarNo());
        carConfimFree.setCarType(CarExceptRecordRtn.getCarType());
        carConfimFree.setCarVehicle(CarExceptRecordRtn.getCarVehicle());
        carConfimFree.setExceptIds(exceptIds);


        // -------------- 应交金额
        BigDecimal totalAmount = BigDecimal.ZERO;
        BigDecimal chargeAmount = BigDecimal.ZERO;
        BigDecimal difAmount = BigDecimal.ZERO;

        BigDecimal tempCfAmount = BigDecimal.ZERO;

        for (CarExceptRecord record : carExceptRecordList) {
            if (null != record.getDifAmount()){
                difAmount = difAmount.add(record.getDifAmount());
            }
        }

        BigDecimal bite = new BigDecimal("0.3");
        tempCfAmount = difAmount.multiply(bite);

        // 判断大于0
        if (difAmount.compareTo(BigDecimal.ZERO) != 0) {
            difAmount = difAmount.setScale(2, RoundingMode.HALF_UP);
        }
        carConfimFree.setDifAmount(difAmount);

        carConfimFree.setBackCol1(bite+"");
        carConfimFree.setAmount(tempCfAmount.setScale(2, RoundingMode.HALF_UP));

        return AjaxResult.success(carConfimFree);
    }

    /**
     * 查询确认补缴列表
     *
     * @param carConfimFree 确认补缴
     * @return 确认补缴集合
     */
    public CarConfimFree listCount(CarConfimFree carConfimFree){
        return  carConfimFreeMapper.listCount(carConfimFree);
    }

    @Override
    public List<PCCarStatisticsVO> getPCCarStatistics(CarConfimFreeQueryRo queryRo) {
        List<PCCarStatisticsVO> res = new ArrayList<>();

        List<CarConfimFree> confimFreeList =  baseMapper.getPCCarStatistics(queryRo);
        // 根据
        List<String> deptList = new ArrayList<>();
        Map<String, String> deptMap = new HashMap<>();
        Map<String, CarConfimFree> exceptMap = new HashMap<>();
        for (CarConfimFree carConfimFree : confimFreeList) {
            String epsId = CommonUtil.isNull(carConfimFree.getEpsId()); // 单位
            String orgName = CommonUtil.isNull(carConfimFree.getOrgName()); // 单位
            String escapedType = CommonUtil.isNull(carConfimFree.getEscapedType()); // 逃费类型
            if (CommonUtil.isNotBlank(epsId) && CommonUtil.isNotBlank(orgName)) {
                if (!deptMap.containsKey(orgName)) {
                    deptList.add(orgName);
                    deptMap.put(orgName, orgName);
                }
                exceptMap.put(orgName + escapedType, carConfimFree);
            }
        }

        for (String org : deptList) {
            PCCarStatisticsVO pcCarStatisticsVO = new PCCarStatisticsVO();
            pcCarStatisticsVO.setOrgName(org);

            int totalNum = 0;
            BigDecimal totalAmount = BigDecimal.ZERO;

            String escapedType = "10";
            if (exceptMap.containsKey(org + escapedType)) {
                CarConfimFree rtnConfimFree = exceptMap.get(org + escapedType);
                pcCarStatisticsVO.setEscapedType10Num(rtnConfimFree.getNumber());
                pcCarStatisticsVO.setEscapedType10Amount(rtnConfimFree.getEscapedAmount());

                totalNum = totalNum + rtnConfimFree.getNumber();
                totalAmount = totalAmount.add(rtnConfimFree.getEscapedAmount());
            }


            escapedType = "20";
            if (exceptMap.containsKey(org + escapedType)) {
                CarConfimFree rtnConfimFree = exceptMap.get(org + escapedType);
                pcCarStatisticsVO.setEscapedType20Num(rtnConfimFree.getNumber());
                pcCarStatisticsVO.setEscapedType20Amount(rtnConfimFree.getEscapedAmount());

                totalNum = totalNum + rtnConfimFree.getNumber();
                totalAmount = totalAmount.add(rtnConfimFree.getEscapedAmount());
            }

            escapedType = "30";
            if (exceptMap.containsKey(org + escapedType)) {
                CarConfimFree rtnConfimFree = exceptMap.get(org + escapedType);
                pcCarStatisticsVO.setEscapedType30Num(rtnConfimFree.getNumber());
                pcCarStatisticsVO.setEscapedType30Amount(rtnConfimFree.getEscapedAmount());

                totalNum = totalNum + rtnConfimFree.getNumber();
                totalAmount = totalAmount.add(rtnConfimFree.getEscapedAmount());
            }

            escapedType = "40";
            if (exceptMap.containsKey(org + escapedType)) {
                CarConfimFree rtnConfimFree = exceptMap.get(org + escapedType);
                pcCarStatisticsVO.setEscapedType40Num(rtnConfimFree.getNumber());
                pcCarStatisticsVO.setEscapedType40Amount(rtnConfimFree.getEscapedAmount());

                totalNum = totalNum + rtnConfimFree.getNumber();
                totalAmount = totalAmount.add(rtnConfimFree.getEscapedAmount());
            }

            escapedType = "50";
            if (exceptMap.containsKey(org + escapedType)) {
                CarConfimFree rtnConfimFree = exceptMap.get(org + escapedType);
                pcCarStatisticsVO.setEscapedType50Num(rtnConfimFree.getNumber());
                pcCarStatisticsVO.setEscapedType50Amount(rtnConfimFree.getEscapedAmount());

                totalNum = totalNum + rtnConfimFree.getNumber();
                totalAmount = totalAmount.add(rtnConfimFree.getEscapedAmount());
            }


            // 合计---------------
            pcCarStatisticsVO.setTotalNum(totalNum);
            pcCarStatisticsVO.setTotalAmount(totalAmount.setScale(2, RoundingMode.HALF_UP));

            res.add(pcCarStatisticsVO);
        }



        return res;

      /*  Map<String, List<String>> map = new HashMap<>(confimFreeList.size());
        if(!CollectionUtils.isEmpty(confimFreeList)) {
//            List<String> exceptIdList = new ArrayList<>();
            confimFreeList.forEach(item -> {
                String exceptIds = CommonUtil.deleteEnd(item.getExceptIds()); // 去掉空格
                String[] split = exceptIds.split(",");
                List<String> list = Arrays.asList(split);
//                exceptIdList.addAll(list);
                map.put(item.getOrgName(), list);
            });
//            List<CarExceptRecord> exceptRecordList = carExceptRecordService.listByIds(exceptIdList);
            *//*Map<String, CarExceptRecord> linkedHashMap = new LinkedHashMap<>(exceptRecordList.size());
            for (CarExceptRecord record : exceptRecordList) {
                linkedHashMap.put(record.getId(), record);
            }*//*

            for (CarConfimFree confimFree : confimFreeList) {
                List<String> ids = map.get(confimFree.getOrgName());
                PCCarStatisticsVO vo = carExceptRecordService.buildPCCarStatisticsVO(ids, queryRo.getEscapedType());
                vo.setOrgName(confimFree.getOrgName());
                List<PCCarStatisticsDetailVO> detailVOList = carExceptRecordService.buildPCCarStatisticsVODetail(ids, queryRo.getEscapedType());
                detailVOList = detailVOList.stream().peek(detailVO -> {
                    detailVO.setOrgName(confimFree.getOrgName());
                }).collect(Collectors.toList());
                vo.setDetailVOList(detailVOList);
                res.add(vo);
            }
            return res;
        }*/

    }

    @Override
    public List<CarConfimFree> selectConcernedList(CarConfimFree carConfimFree) {
        List<CarConfimFree> confimFreeList =  baseMapper.selectConcernedList(carConfimFree);
        return confimFreeList;
    }
}
