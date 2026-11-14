package com.ruoyi.system.domain;

import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.annotation.Excel.ColumnType;
import com.ruoyi.common.core.domain.BaseEntity;
import org.apache.commons.lang3.builder.ToStringBuilder;
import org.apache.commons.lang3.builder.ToStringStyle;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/**
 * 参数配置表 sys_config
 * 
 * @author ruoyi
 */
public class SysUtil extends BaseEntity
{
    //业务类型
    private String bussType;

    //编码code
    private String bussCode;

    //表名
    private String tbsName;

    //查询条件
    private String queryCondtion;

    //查询数量
    private Integer countNum;

    public String getBussType() {
        return bussType;
    }

    public void setBussType(String bussType) {
        this.bussType = bussType;
    }

    public String getBussCode() {
        return bussCode;
    }

    public void setBussCode(String bussCode) {
        this.bussCode = bussCode;
    }

    public String getTbsName() {
        return tbsName;
    }

    public void setTbsName(String tbsName) {
        this.tbsName = tbsName;
    }

    public String getQueryCondtion() {
        return queryCondtion;
    }

    public void setQueryCondtion(String queryCondtion) {
        this.queryCondtion = queryCondtion;
    }

    public Integer getCountNum() {
        return countNum;
    }

    public void setCountNum(Integer countNum) {
        this.countNum = countNum;
    }
}
