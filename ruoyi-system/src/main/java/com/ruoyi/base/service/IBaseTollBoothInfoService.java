package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.BaseTollBoothInfo;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 收费所基础信息Service接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
public interface IBaseTollBoothInfoService extends IService<BaseTollBoothInfo> {
    /**
     * 查询收费所基础信息
     *
     * @param agentPk 收费所基础信息ID
     * @return 收费所基础信息
     */
    BaseTollBoothInfo selectBaseTollBoothInfoById(String agentPk);

    /**
     * 查询收费所基础信息列表
     *
     * @param baseTollBoothInfo 收费所基础信息
     * @return 收费所基础信息集合
     */
    List<BaseTollBoothInfo> selectBaseTollBoothInfoList(BaseTollBoothInfo baseTollBoothInfo);


    /**
     * 新增或者修改收费所基础信息
     *
     * @param baseTollBoothInfo 收费所基础信息
     * @return 结果
     */
    AjaxResult saveBaseTollBoothInfo(BaseTollBoothInfo baseTollBoothInfo);

    /**
     * 批量删除收费所基础信息
     *
     * @param agentPks 需要删除的收费所基础信息ID
     * @return 结果
     */
    AjaxResult deleteBaseTollBoothInfoByIds(String[] agentPks);

}
