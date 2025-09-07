package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.domain.entity.SysDictData;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.manager.domain.CarAduitFree;
import com.ruoyi.manager.domain.CarConfimFree;
import com.ruoyi.manager.domain.CarExceptRecord;
import com.ruoyi.manager.domain.vo.bigscreen.CarStatisticsVO;
import com.ruoyi.manager.mapper.CarConfimFreeMapper;
import com.ruoyi.manager.service.ICarAduitFreeService;
import com.ruoyi.manager.service.ICarConfimFreeService;
import com.ruoyi.manager.service.ICarExceptRecordService;
import com.ruoyi.system.service.ISysDictDataService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.CollectionUtils;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
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
        List<String> exceptIdList = Arrays.asList(exceptIds.split(","));
        List<CarConfimFree> list = carConfimFreeMapper.selectCarConfimFreeByExceptIds(exceptIdList);
        if (null != list && list.size() > 0) {
            return AjaxResult.error("请勿重复补缴！");
        }

        if (CommonUtil.isNotBlank(carConfimFree.getId())) {
            // 修改
            carConfimFreeMapper.updateById(carConfimFree);
        } else {
            // 新增 主键
            carConfimFreeMapper.insert(carConfimFree);
        }

        // 修改明细
        List<CarAduitFree> carAduitFreeList = carConfimFree.getCarAduitFreeList();
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
        int count = carConfimFreeMapper.deleteCarConfimFreeByIds(ids);
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
    public List<CarStatisticsVO> getCarStatistics() {
        // 逃费类型
        SysDictData sysDictData = new SysDictData();
        sysDictData.setDictType("escaped_type");
        List<SysDictData> dictDataList = sysDictDataService.selectDictDataList(sysDictData);
        List<CarStatisticsVO> list = carConfimFreeMapper.getCarStatistics();
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
    public BigDecimal getCarConfirm() {
        return carConfimFreeMapper.getCarConfirm();
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

        if(CollectionUtils.isEmpty(carExceptRecordList)){
            return AjaxResult.error("异常车辆流水不存在！");
        }

        List<String> carNoList = carExceptRecordList.stream().map(CarExceptRecord::getCarNo).distinct().collect(Collectors.toList());
        if(carNoList.size() > 1){
            return AjaxResult.error("请勿选择多辆车！");
        }

        List<String> exceptIdList = Arrays.asList(exceptIds.split(","));
        List<CarConfimFree> list = carConfimFreeMapper.selectCarConfimFreeByExceptIds(exceptIdList);
        if (null != list && list.size() > 0) {
            return AjaxResult.error("请勿重复补缴！");
        }

        CarExceptRecord CarExceptRecordRtn = carExceptRecordList.get(0);

        carConfimFree.setCarId(CarExceptRecordRtn.getCarId());
        carConfimFree.setCarNo(CarExceptRecordRtn.getCarNo());
        carConfimFree.setCarType(CarExceptRecordRtn.getCarType());
        carConfimFree.setCarVehicle(CarExceptRecordRtn.getCarVehicle());
        carConfimFree.setExceptIds(exceptIds);


        return AjaxResult.success(carConfimFree);
    }
}
