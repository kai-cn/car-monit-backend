package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarQueryLog;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 查询日志Service接口
 *
 * @author fzq
 * @date 2025-12-22
 */
public interface ICarQueryLogService extends IService<CarQueryLog> {
    /**
     * 查询查询日志
     *
     * @param id 查询日志ID
     * @return 查询日志
     */
    CarQueryLog selectCarQueryLogById(String id);

    /**
     * 查询查询日志列表
     *
     * @param carQueryLog 查询日志
     * @return 查询日志集合
     */
    List<CarQueryLog> selectCarQueryLogList(CarQueryLog carQueryLog);


    /**
     * 新增或者修改查询日志
     *
     * @param carQueryLog 查询日志
     * @return 结果
     */
    AjaxResult saveCarQueryLog(CarQueryLog carQueryLog);

    /**
     * 批量删除查询日志
     *
     * @param ids 需要删除的查询日志ID
     * @return 结果
     */
    AjaxResult deleteCarQueryLogByIds(String[] ids);

}
