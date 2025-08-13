package com.ruoyi.system.domain;

import lombok.Data;
import org.apache.commons.lang3.builder.ToStringBuilder;
import org.apache.commons.lang3.builder.ToStringStyle;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BaseUuidEntity;

/**
 * 用户常用菜单对象 sys_index_menu
 * 
 * @author ruoyi
 * @date 2021-08-20
 */
@Data
public class SysIndexMenu extends BaseUuidEntity
{
    /** 用户ID */
    @Excel(name = "用户ID")
    private Long userId;

    /** 菜单ID */
    @Excel(name = "菜单ID")
    private Long menuId;

    //菜单名称")
    private String menuName;

    
    //一级菜单名称
    private String menuName1;

    
    //二级菜单名称
    private String menuName2;

    
    //三级菜单名称
    private String menuName3;


    
    //多个菜单ids
    private String menuIds;


    
    //菜单地址
    private String menuUrl;
}
