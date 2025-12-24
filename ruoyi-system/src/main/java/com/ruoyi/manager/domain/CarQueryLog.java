package com.ruoyi.manager.domain;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BasePlusEntity;
import com.ruoyi.common.core.domain.Custom;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.experimental.Accessors;

/**
 * 查询日志对象 car_query_log
 *
 * @author fzq
 * @date 2025-12-22
 */
@Data
@TableName("car_query_log")
@Accessors(chain = true)
@EqualsAndHashCode(callSuper = false)
public class CarQueryLog extends BasePlusEntity implements Custom {

    /** 用户ID */
    @Excel(name = "用户ID")
    private String userId;

    /** 用户名称 */
    @Excel(name = "用户名称")
    private String userName;

    /** 用户IP */
    @Excel(name = "用户IP")
    private String userIp;

    /** 模块菜单(1轨迹单2门架拍识3门架交易流水) */
    @Excel(name = "模块菜单(1轨迹单2门架拍识3门架交易流水)")
    private String modelType;

    /** 模块功能(1查看2导出) */
    @Excel(name = "模块功能(1查看2导出)")
    private String menuPoint;

    /** 查询条件 */
    @Excel(name = "查询条件")
    private String queryCondition;

    /** 备用字段1 */
    private String backCol1;

    /** 备用字段2 */
    private String backCol2;

    /** 状态（0正常1停用） */
    private String status;

    /** 备注 */
    @Excel(name = "备注")
    private String remark;


    // 时间查询 :入口时间
    @TableField(exist = false)
    private String applyTime1;


    @TableField(exist = false)
    private String applyTime2;

}
