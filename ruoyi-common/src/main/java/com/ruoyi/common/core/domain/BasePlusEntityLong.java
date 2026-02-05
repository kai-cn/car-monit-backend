package com.ruoyi.common.core.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;
import lombok.experimental.Accessors;

import java.io.Serializable;
import java.sql.Timestamp;

/**
 * Entity基类
 *
 * @author ruoyi
 */
@Data
@Accessors(chain = true)
public class BasePlusEntityLong implements Serializable,CustomClass{


    private static final long serialVersionUID = 1L;

    /**
     * 主键：雪花算法
     */
    @TableId(value = "id", type = IdType.ASSIGN_ID)
    private String id;

    /**
     * 创建人所在单位或科室
     */
    private Long epsId;

    /**
     * 删除标志（0存在 1删除）
     */
    @TableLogic(value = "0", delval = "1")
    @TableField(value = "del_flag", select = false)
    private String delFlag;

    /**
     * 创建人
     */
    private Long createBy;

    /**
     * 创建时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Timestamp createTime;

    /**
     * 更新人
     */
    private Long updateBy;

    /**
     * 更新时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Timestamp updateTime;

    /**
     * 排序
     */
    private Integer sort;

    /**
     * 租户
     */
    private Long tenantId;

}
