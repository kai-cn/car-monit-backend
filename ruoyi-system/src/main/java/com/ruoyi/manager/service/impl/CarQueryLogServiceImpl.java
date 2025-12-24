package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.domain.entity.SysUser;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.manager.domain.CarQueryLog;
import com.ruoyi.manager.mapper.CarQueryLogMapper;
import com.ruoyi.manager.service.ICarQueryLogService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 查询日志Service业务层处理
 *
 * @author fzq
 * @date 2025-12-22
 */
@Service
public class CarQueryLogServiceImpl extends ServiceImpl<CarQueryLogMapper, CarQueryLog> implements ICarQueryLogService {

    @Autowired
    private CarQueryLogMapper carQueryLogMapper;

    /**
     * 查询查询日志
     *
     * @param id 查询日志ID
     * @return 查询日志
     */
    @Override
    public CarQueryLog selectCarQueryLogById(String id) {
        return carQueryLogMapper.selectCarQueryLogById(id);
    }

    /**
     * 查询查询日志列表
     *
     * @param carQueryLog 查询日志
     * @return 查询日志
     */
    @Override
    public List<CarQueryLog> selectCarQueryLogList(CarQueryLog carQueryLog) {
        return carQueryLogMapper.selectCarQueryLogList(carQueryLog);
    }


    /**
     * 新增或者修改查询日志
     *
     * @param carQueryLog 查询日志
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarQueryLog(CarQueryLog carQueryLog)
    {
        if (CommonUtil.isNotBlank(carQueryLog.getId()))
        {
            // 修改
            carQueryLogMapper.updateById(carQueryLog);
        }
        else
        {
            // 新增 主键
            carQueryLogMapper.insert(carQueryLog);
        }
        return AjaxResult.success("操作成功！",carQueryLog.getId());
    }
    

    /**
     * 批量删除查询日志
     *
     * @param ids 需要删除的查询日志ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarQueryLogByIds(String[] ids)
    {
        int count = carQueryLogMapper.deleteCarQueryLogByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除查询日志信息
     *
     * @param id 查询日志ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarQueryLogById(String id)
    {
        int count = carQueryLogMapper.deleteCarQueryLogById(id);
        return AjaxResult.success(count);
    }


    /**
     * 查询、导出日志记录
     * @param queryCondition 日志实体类
     * @param modelType 模块菜单(1轨迹单2门架拍识3门架交易流水)
     * @param menuPiont 模块功能(1查看2导出)
     */
    public void queryLog(String queryCondition, String modelType, String menuPiont) {
        SysUser user = SecurityUtils.getLoginUser().getUser();
        CarQueryLog carQueryLog = new CarQueryLog();
        carQueryLog.setUserId(user.getUserId().toString());
        carQueryLog.setUserName(SecurityUtils.getUserRealName());
        carQueryLog.setUserIp(user.getLoginIp());
        carQueryLog.setModelType(modelType);
        carQueryLog.setMenuPoint(menuPiont);
        carQueryLog.setQueryCondition(queryCondition);
        this.saveCarQueryLog(carQueryLog);
    }




}
