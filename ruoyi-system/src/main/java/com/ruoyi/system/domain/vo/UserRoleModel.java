package com.ruoyi.system.domain.vo;

import lombok.Data;

/**
 * 用户和角色关联 sys_user_role
 *
 * @author ruoyi
 */
@Data
public class UserRoleModel {
    /**
     * 用户ID
     */
    private String userId;

    /**
     * 用户名称
     */
    private String userName;
}
