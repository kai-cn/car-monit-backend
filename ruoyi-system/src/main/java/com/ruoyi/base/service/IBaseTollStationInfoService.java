package com.ruoyi.base.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.BaseTollStationInfo;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 收费站基础信息Service接口
 *
 * @author ruoyi
 * @date 2025-08-26
 */
public interface IBaseTollStationInfoService extends IService<BaseTollStationInfo> {
    /**
     * 查询收费站基础信息
     *
     * @param id 收费站基础信息ID
     * @return 收费站基础信息
     */
    BaseTollStationInfo selectBaseTollStationInfoById(String id);

    /**
     * 查询收费站基础信息列表
     *
     * @param baseTollStationInfo 收费站基础信息
     * @return 收费站基础信息集合
     */
    List<BaseTollStationInfo> selectBaseTollStationInfoList(BaseTollStationInfo baseTollStationInfo);


    /**
     * 新增或者修改收费站基础信息
     *
     * @param baseTollStationInfo 收费站基础信息
     * @return 结果
     */
    AjaxResult saveBaseTollStationInfo(BaseTollStationInfo baseTollStationInfo);

    /**
     * 批量删除收费站基础信息
     *
     * @param ids 需要删除的收费站基础信息ID
     * @return 结果
     */
    AjaxResult deleteBaseTollStationInfoByIds(String[] ids);

}
