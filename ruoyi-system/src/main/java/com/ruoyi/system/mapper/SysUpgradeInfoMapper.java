package com.ruoyi.system.mapper;


import com.ruoyi.system.domain.SysUpgradeInfo;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 系统升级信息Mapper接口
 *
 * @author ruoyi
 * @date 2022-01-10
 */
@Repository
public interface SysUpgradeInfoMapper {
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
     * 新增系统升级信息
     *
     * @param sysUpgradeInfo 系统升级信息
     * @return 结果
     */
    int insertSysUpgradeInfo(SysUpgradeInfo sysUpgradeInfo);

    /**
     * 修改系统升级信息
     *
     * @param sysUpgradeInfo 系统升级信息
     * @return 结果
     */
    int updateSysUpgradeInfo(SysUpgradeInfo sysUpgradeInfo);

    /**
     * 删除系统升级信息
     *
     * @param id 系统升级信息ID
     * @return 结果
     */
    int deleteSysUpgradeInfoById(String id);

    /**
     * 批量删除系统升级信息
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteSysUpgradeInfoByIds(String[] ids);

    /**
     * 获取最新的更新日志
     * @param sysUpgradeInfo
     * @return
     */
    SysUpgradeInfo selectSysUpgradeInfoNewest(SysUpgradeInfo sysUpgradeInfo);

}
