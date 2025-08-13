package com.ruoyi.system.domain;

import com.ruoyi.common.core.domain.BaseUuidEntity;
import lombok.Data;

/**
 * 系统升级信息对象 sys_upgrade_info
 *
 * @author ruoyi
 * @date 2022-01-10
 */
@Data
public class SysUpgradeInfo extends BaseUuidEntity {
    /**
     * 版本
     */
    private String ver;

    /**
     * 更新信息
     */
    private String info;

    /**
     * 备用字段1
     */
    private String backCol1;
}
