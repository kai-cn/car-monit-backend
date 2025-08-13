package com.ruoyi.system.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.system.domain.SysUpgradeInfo;

import java.util.List;

/**
 * 系统升级信息Service接口
 *
 * @author ruoyi
 * @date 2022-01-10
 */
public interface ISysUpgradeInfoService {
    /**
     * 查询系统升级信息
     *
     * @param id 系统升级信息ID
     * @return 系统升级信息
     */
    SysUpgradeInfo selectSysUpgradeInfoById(String id);

    /**
     * 查询系统升级信息列表
     *
     * @param sysUpgradeInfo 系统升级信息
     * @return 系统升级信息集合
     */
    List<SysUpgradeInfo> selectSysUpgradeInfoList(SysUpgradeInfo sysUpgradeInfo);

    /**
     * 新增或者修改系统升级信息
     *
     * @param sysUpgradeInfo 系统升级信息
     * @return 结果
     */
    AjaxResult saveSysUpgradeInfo(SysUpgradeInfo sysUpgradeInfo);

    /**
     * 批量删除系统升级信息
     *
     * @param ids 需要删除的系统升级信息ID
     * @return 结果
     */
    AjaxResult deleteSysUpgradeInfoByIds(String[] ids);

    /**
     * com.ruoyi.notice.service.ISysUpgradeInfoService
     * com.ruoyi.notice.service.ISysUpgradeInfoService
     * 删除系统升级信息信息
     *
     * @param id 系统升级信息ID
     * @return 结果
     */
    AjaxResult deleteSysUpgradeInfoById(String id);

    /**
     * 获取最新的更新日志
     *
     * @param sysUpgradeInfo
     * @return
     */
    SysUpgradeInfo selectSysUpgradeInfoNewest(SysUpgradeInfo sysUpgradeInfo);
}
