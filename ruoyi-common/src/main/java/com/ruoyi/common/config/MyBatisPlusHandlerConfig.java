package com.ruoyi.common.config;

import com.baomidou.mybatisplus.core.handlers.MetaObjectHandler;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.SecurityUtils;
import org.apache.ibatis.reflection.MetaObject;
import org.springframework.stereotype.Component;

import java.util.Objects;

/**
 * @Description:
 * @Author HuangJun
 * @Date 2024/5/22 10:12
 * @Return
 */
@Component
public class MyBatisPlusHandlerConfig implements MetaObjectHandler {
    @Override
    public void insertFill(MetaObject metaObject) {
        if (Objects.nonNull(metaObject)) {
            // 获取创建人字段
            Object createTime = getFieldValByName("createTime", metaObject);
            // 如果创建人为空，则自动填充当前登录用户（这里假设当前登录用户存储在ThreadLocal中）
            if (createTime == null) {
                java.sql.Timestamp curDate = DateUtils.getTimestamp();
                this.setFieldValByName("createTime", curDate, metaObject);
            }

            // 获取创建人字段
            Object createBy = getFieldValByName("createBy", metaObject);
            // 如果创建人为空，则自动填充当前登录用户（这里假设当前登录用户存储在ThreadLocal中）
            if (createBy == null) {
                //获取当前用户id
                Long userId = SecurityUtils.getUserId();
                if (Objects.nonNull(userId)){
                    this.setFieldValByName("createBy", userId, metaObject);
                }
            }

            Object epsId = getFieldValByName("epsId", metaObject);
            // 如果创建人为空，则自动填充当前登录用户（这里假设当前登录用户存储在ThreadLocal中）
            if (epsId == null) {
                //获取当前用户id
                Long userId = SecurityUtils.getEpsId();
                if (Objects.nonNull(userId)){
                    this.setFieldValByName("epsId", userId, metaObject);
                }
            }

            Object tenantId = getFieldValByName("tenantId", metaObject);
            // 如果创建人为空，则自动填充当前登录用户（这里假设当前登录用户存储在ThreadLocal中）
            if (epsId == null) {
                //获取当前用户id
                Long userId = SecurityUtils.getTenantId();
                if (Objects.nonNull(userId)){
                    this.setFieldValByName("tenantId", userId, metaObject);
                }
            }

        }
    }

    @Override
    public void updateFill(MetaObject metaObject) {
        if (Objects.nonNull(metaObject)) {
            // 获取创建人字段
            Object updateTime = getFieldValByName("updateTime", metaObject);
            // 如果创建人为空，则自动填充当前登录用户（这里假设当前登录用户存储在ThreadLocal中）
            if (updateTime == null) {
                java.sql.Timestamp curDate = DateUtils.getTimestamp();
                this.setFieldValByName("updateTime", curDate, metaObject);
            }

            // 获取创建人字段
            Object updateBy = getFieldValByName("updateBy", metaObject);
            // 如果创建人为空，则自动填充当前登录用户（这里假设当前登录用户存储在ThreadLocal中）
            if (updateBy == null) {
                //获取当前用户id
                Long userId = SecurityUtils.getUserId();
                if (Objects.nonNull(userId)){
                    this.setFieldValByName("updateBy", userId, metaObject);
                }
            }
        }
    }
}
