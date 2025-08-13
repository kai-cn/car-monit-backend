package com.ruoyi.common.utils;

import com.ruoyi.common.core.domain.BaseUuidEntity;
import com.ruoyi.common.enums.BusinessStatusEnum;

/**
 * @author gl
 * @description 初始化通用字段工具类
 * @date 2022-03-01
 */

public class ModelUtil {

    private ModelUtil() {}

    /**
     * 初始化创建实体 通用字段
     * @param entity
     */
    public static void initCreateCommonField(BaseUuidEntity entity) {
        Long userId = SecurityUtils.getUserId();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();

        entity.setDelFlag(BusinessStatusEnum.NO_DELETE.getCodeString());
        entity.setCreateBy(userId);
        entity.setCreateTime(curDate);
        entity.setUpdateBy(userId);
        entity.setUpdateTime(curDate);
        entity.setEpsId(SecurityUtils.getEpsId());
        entity.setTenantId(SecurityUtils.getTenantId());
    }

    /**
     * 初始化 更新实体 通用字段
     * @param entity
     */
    public static void initUpdateCommonField(BaseUuidEntity entity) {
        Long userId = SecurityUtils.getUserId();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();

        entity.setUpdateBy(userId);
        entity.setUpdateTime(curDate);
    }

}