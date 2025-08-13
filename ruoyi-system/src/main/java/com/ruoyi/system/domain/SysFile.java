package com.ruoyi.system.domain;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.databind.annotation.JsonSerialize;
import com.fasterxml.jackson.databind.ser.std.ToStringSerializer;
import com.ruoyi.common.annotation.Excel;

import java.util.Date;

/**
 * 文件管理对象 sys_file
 *
 * @author ruoyi
 * @date 2021-07-29
 */
public class SysFile {
    private static final long serialVersionUID = 1L;

    /**
     * 编号
     */
    @JsonSerialize(using = ToStringSerializer.class)
    private Long id;

    /**
     * 文件名称
     */
    @Excel(name = "文件名称")
    private String fileName;

    /**
     * 上传包名
     */
    @Excel(name = "上传包名")
    private String bucketName;

    /**
     * 上传文件名称
     */
    @Excel(name = "上传文件名称")
    private String original;

    /**
     * 文件类型
     */
    @Excel(name = "文件类型")
    private String type;

    /**
     * 文件大小
     */
    @Excel(name = "文件大小")
    private Long fileSize;

    /** 业务类型 */
    @Excel(name = "业务类型")
    private String bussType;

    /** 业务名称  供应商代理证时间 */
    @Excel(name = "业务名称")
    private String bussName;

    /** 创建时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Date createTime;
    /**
     * $column.columnComment
     */
    @Excel(name = "文件大小")
    private String createUser;

    /** 更新时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private Date updateTime;
    /**
     * $column.columnComment
     */
    @Excel(name = "文件大小")
    private String updateUser;

    /**
     * $column.columnComment
     */
    private String delFlag;

    /**
     * 所属租户
     */
    @Excel(name = "所属租户")
    private Long tenantId;


    /**
     * 文件名称
     */
    @Excel(name = "文件s")
    private String files;

    /**
     * 创建人姓名
     */
    private String createUserName;

    public String getFiles() {
        return files;
    }

    public void setFiles(String files) {
        this.files = files;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getId() {
        return id;
    }

    public void setFileName(String fileName) {
        this.fileName = fileName;
    }

    public String getFileName() {
        return fileName;
    }

    public void setBucketName(String bucketName) {
        this.bucketName = bucketName;
    }

    public String getBucketName() {
        return bucketName;
    }

    public void setOriginal(String original) {
        this.original = original;
    }

    public String getOriginal() {
        return original;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getType() {
        return type;
    }

    public void setFileSize(Long fileSize) {
        this.fileSize = fileSize;
    }

    public Long getFileSize() {
        return fileSize;
    }

    public void setCreateUser(String createUser) {
        this.createUser = createUser;
    }

    public String getCreateUser() {
        return createUser;
    }

    public void setUpdateUser(String updateUser) {
        this.updateUser = updateUser;
    }

    public String getUpdateUser() {
        return updateUser;
    }

    public void setDelFlag(String delFlag) {
        this.delFlag = delFlag;
    }

    public String getDelFlag() {
        return delFlag;
    }

    public void setTenantId(Long tenantId) {
        this.tenantId = tenantId;
    }

    public Long getTenantId() {
        return tenantId;
    }

    public Date getCreateTime() {
        return createTime;
    }

    public void setCreateTime(Date createTime) {
        this.createTime = createTime;
    }

    public Date getUpdateTime() {
        return updateTime;
    }

    public void setUpdateTime(Date updateTime) {
        this.updateTime = updateTime;
    }

    public String getBussType() {
        return bussType;
    }

    public void setBussType(String bussType) {
        this.bussType = bussType;
    }

    public String getBussName() {
        return bussName;
    }

    public void setBussName(String bussName) {
        this.bussName = bussName;
    }

    public String getCreateUserName() {
        return createUserName;
    }

    public void setCreateUserName(String createUserName) {
        this.createUserName = createUserName;
    }
}
