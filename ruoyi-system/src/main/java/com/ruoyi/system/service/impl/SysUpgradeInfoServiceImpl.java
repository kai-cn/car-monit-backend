package com.ruoyi.system.service.impl;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.system.domain.SysUpgradeInfo;
import com.ruoyi.system.mapper.SysUpgradeInfoMapper;
import com.ruoyi.system.service.ISysUpgradeInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 系统升级信息Service业务层处理
 *
 * @author ruoyi
 * @date 2022-01-10
 */
@Service
public class SysUpgradeInfoServiceImpl implements ISysUpgradeInfoService {
    @Autowired
    private SysUpgradeInfoMapper sysUpgradeInfoMapper;

    /**
     * 查询系统升级信息
     *
     * @param id 系统升级信息ID
     * @return 系统升级信息
     */
    @Override
    public SysUpgradeInfo selectSysUpgradeInfoById(String id) {
        return sysUpgradeInfoMapper.selectSysUpgradeInfoById(id);
    }

    /**
     * 查询系统升级信息列表
     *
     * @param sysUpgradeInfo 系统升级信息
     * @return 系统升级信息
     */
    @Override
    public List<SysUpgradeInfo> selectSysUpgradeInfoList(SysUpgradeInfo sysUpgradeInfo) {
        return sysUpgradeInfoMapper.selectSysUpgradeInfoList(sysUpgradeInfo);
    }

    /**
     * 新增或者修改系统升级信息
     *
     * @param sysUpgradeInfo 系统升级信息
     * @return 结果
     */
    public AjaxResult saveSysUpgradeInfo(SysUpgradeInfo sysUpgradeInfo) {
        Long userId = SecurityUtils.getUserId();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();
        if (StringUtils.isNotEmpty(sysUpgradeInfo.getId())) {
            // 修改
            sysUpgradeInfo.setUpdateBy(userId); // 更新人
            sysUpgradeInfo.setUpdateTime(curDate); // 更新时间
            sysUpgradeInfoMapper.updateSysUpgradeInfo(sysUpgradeInfo);
        } else {
            // 新增
            sysUpgradeInfo.setId(StringUtils.getUUID()); // 主键
            sysUpgradeInfo.setDelFlag("0");
            sysUpgradeInfo.setEpsId(SecurityUtils.getEpsId()); // 当前人所在的部门
            sysUpgradeInfo.setTenantId(SecurityUtils.getTenantId()); // 当前租户
            sysUpgradeInfo.setCreateBy(userId); // 创建人
            sysUpgradeInfo.setCreateTime(curDate); // 创建时间
            sysUpgradeInfo.setUpdateBy(userId); // 更新人
            sysUpgradeInfo.setUpdateTime(curDate); // 更新时间
            sysUpgradeInfoMapper.insertSysUpgradeInfo(sysUpgradeInfo);
        }
        return AjaxResult.success("操作成功！", sysUpgradeInfo.getId());
    }


    /**
     * 批量删除系统升级信息
     *
     * @param ids 需要删除的系统升级信息ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteSysUpgradeInfoByIds(String[] ids) {
        int count = sysUpgradeInfoMapper.deleteSysUpgradeInfoByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除系统升级信息信息
     *
     * @param id 系统升级信息ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteSysUpgradeInfoById(String id) {
        int count = sysUpgradeInfoMapper.deleteSysUpgradeInfoById(id);
        return AjaxResult.success(count);
    }

    /**
     * 获取最新的更新日志
     *
     * @param sysUpgradeInfo
     * @return
     */
    @Override
    public SysUpgradeInfo selectSysUpgradeInfoNewest(SysUpgradeInfo sysUpgradeInfo) {
        return sysUpgradeInfoMapper.selectSysUpgradeInfoNewest(sysUpgradeInfo);
    }
}
