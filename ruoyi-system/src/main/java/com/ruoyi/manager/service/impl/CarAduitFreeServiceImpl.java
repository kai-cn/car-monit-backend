package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.domain.vo.CarConfimFreeQueryRo;
import com.ruoyi.manager.domain.vo.PCIncomeStaticsVO;
import com.ruoyi.manager.domain.vo.bigscreen.CarStatisticsVO;
import com.ruoyi.manager.domain.vo.bigscreen.IncomeStatisticParam;
import com.ruoyi.manager.domain.vo.bigscreen.incomeStatisticVO;
import com.ruoyi.manager.mapper.CarAduitFreeMapper;
import com.ruoyi.manager.domain.CarAduitFree;
import com.ruoyi.manager.service.ICarAduitFreeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;

/**
 * 补缴处理Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-28
 */
@Service
public class CarAduitFreeServiceImpl extends ServiceImpl<CarAduitFreeMapper, CarAduitFree> implements ICarAduitFreeService {

    @Autowired
    private CarAduitFreeMapper carAduitFreeMapper;

    /**
     * 查询补缴处理
     *
     * @param id 补缴处理ID
     * @return 补缴处理
     */
    @Override
    public CarAduitFree selectCarAduitFreeById(String id) {
        return carAduitFreeMapper.selectCarAduitFreeById(id);
    }

    /**
     * 查询补缴处理列表
     *
     * @param carAduitFree 补缴处理
     * @return 补缴处理
     */
    @Override
    public List<CarAduitFree> selectCarAduitFreeList(CarAduitFree carAduitFree) {
        return carAduitFreeMapper.selectCarAduitFreeList(carAduitFree);
    }


    /**
     * 新增或者修改补缴处理
     *
     * @param carAduitFree 补缴处理
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarAduitFree(CarAduitFree carAduitFree)
    {
        if (CommonUtil.isNotBlank(carAduitFree.getId()))
        {
            // 修改
            carAduitFreeMapper.updateById(carAduitFree);
        }
        else
        {
            // 新增 主键
            carAduitFreeMapper.insert(carAduitFree);
        }
        return AjaxResult.success("操作成功！",carAduitFree.getId());
    }

    /**
     * 批量删除补缴处理
     *
     * @param ids 需要删除的补缴处理ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarAduitFreeByIds(String[] ids)
    {
        int count = carAduitFreeMapper.deleteCarAduitFreeByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除补缴处理信息
     *
     * @param id 补缴处理ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarAduitFreeById(String id)
    {
        int count = carAduitFreeMapper.deleteCarAduitFreeById(id);
        return AjaxResult.success(count);
    }

    /**
     * 批量删除补缴处理
     *
     * @param fkId 补交ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarAduitFreeByConfirmId(String fkId) {
        int count = 0;
        if (CommonUtil.isNotBlank(fkId)) {
            count = carAduitFreeMapper.deleteCarAduitFreeByConfirmId(fkId);
        }
        return AjaxResult.success(count);
    }


    @Override
    public CarStatisticsVO getCarAudit(IncomeStatisticParam param) {
        return carAduitFreeMapper.getCarAudit(param);
    }

    @Override
    public List<incomeStatisticVO> incomeStatistic(IncomeStatisticParam param) {
        return carAduitFreeMapper.incomeStatistic(param);
    }

    @Override
    public Integer selectAuditCount(IncomeStatisticParam param) {
        return carAduitFreeMapper.selectAuditCount(param);
    }

    @Override
    public List<PCIncomeStaticsVO> getPCIncomeStatics(CarConfimFreeQueryRo queryRo) {
        return carAduitFreeMapper.PCIncomeStatics(queryRo);
    }
}
