package com.ruoyi.common.core.domain.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.annotation.Excel.ColumnType;
import com.ruoyi.common.annotation.Excel.Type;
import com.ruoyi.common.annotation.Excels;
import com.ruoyi.common.core.domain.BaseEntity;
import org.apache.commons.lang3.builder.ToStringBuilder;
import org.apache.commons.lang3.builder.ToStringStyle;

import java.util.Date;
import java.util.List;

/**
 * 用户对象 sys_user
 *
 * @author ruoyi
 */
public class SysUser extends BaseEntity {
    private static final long serialVersionUID = 1L;

    /**
     * 用户ID
     */
    @Excel(name = "用户序号", cellType = ColumnType.NUMERIC, prompt = "用户编号")
    private Long userId;

    @Excel(name = "用户编码", cellType = ColumnType.NUMERIC, prompt = "用户编码")
    private Long userNo;

    /**
     * 部门ID
     */
    @Excel(name = "部门编号", type = Type.IMPORT)
    private Long deptId;

    /**
     * 用户账号
     */
    @Excel(name = "登录名称")
    private String userName;

    /**
     * 用户昵称
     */
    @Excel(name = "用户名称")
    private String nickName;

    /**
     * 用户类型（1机构用户2专家3供应商）
     *
     */
    @Excel(name = "用户类型", readConverterExp = "1=机构用户2专家3供应商")
    private String userType;

    /**
     * 用户邮箱
     */
    @Excel(name = "用户邮箱")
    private String email;

    /**
     * 手机号码
     */
    @Excel(name = "手机号码")
    private String phonenumber;

    /**
     * 用户性别
     */
    @Excel(name = "用户性别", readConverterExp = "0=男,1=女,2=未知")
    private String sex;

    /**
     * 用户头像
     */
    private String avatar;

    /**
     * 密码
     */
    private String password;

    /**
     * 确认密码
     */
    private String confirmPassword;

    /**
     * 盐加密
     */
    private String salt;

    /**
     * 帐号状态（0正常 1停用）
     */
    @Excel(name = "帐号状态", readConverterExp = "0=正常,1=停用")
    private String status;


    /**
     * 删除标志（0代表存在 2代表删除）
     */
    private String delFlag;

    /**
     * 最后登录IP
     */
    @Excel(name = "最后登录IP", type = Type.EXPORT)
    private String loginIp;

    /**
     * 最后登录时间
     */
    @Excel(name = "最后登录时间", width = 30, dateFormat = "yyyy-MM-dd HH:mm:ss", type = Type.EXPORT)
    private Date loginDate;

    /**
     * 证书编号
     */
    @Excel(name = "证书Id")
    private String certId;


    /**
     * 证书实体编号
     */
    @Excel(name = "证书实体Id")
    private String certEntityId;


    /**
     * 业务id
     * 1. 当 userType = 2, 也就是 专家 时, bussId 表示专家id(base_experts表里面的id)
     * 2. 当 userType = 3, 也就是 供应商 时, bussId 表示供应商注册id(base_supplier表里面的id)
     */
    @Excel(name = "业务id")
    private String bussId;

    /**
     * 业务名称
     */
    @Excel(name = "业务名称")
    private String bussName;

    /**
     * 单位名称
     */
    @Excel(name = "单位名称")
    private String epsName;

    /**
     * 租户单位id
     */
    @Excel(name = "租户单位id")
    private Long tenantId;

    /**
     * 租户单位名称
     */
    @Excel(name = "租户单位名称")
    private String tenantName;

    public String getTenantName() {
        return tenantName;
    }

    public void setTenantName(String tenantName) {
        this.tenantName = tenantName;
    }

    /**
     * 单位名称
     */
    @Excel(name = "角色编码")
    private String roleCode;


    /**
     * 部门对象
     */
    @Excels({
            @Excel(name = "部门名称", targetAttr = "deptName", type = Type.EXPORT),
            @Excel(name = "部门负责人", targetAttr = "leader", type = Type.EXPORT)
    })
    private SysDept dept;

    /**
     * 角色对象
     */
    private List<SysRole> roles;

    /**
     * 角色组
     */
    private Long[] roleIds;

    /**
     * 岗位组
     */
    private Long[] postIds;

    /**
     * 标志
     */
    private String flag;

    private String dataId;

    /**
     * 部门对应的code
     */
    private String subCode;

    /**
     * 查询条件-用户昵称
     */
    private String queryNickName;

    /**
     * 是否排除自己
     */
    private Boolean excludeSelf;

    /**
     * 需要排除的数据集合
     */
    private Long excludeId;

    /**
     * 是否是总公司的人员
     * true => 是
     * false | null => 不是
     */
    private Boolean headOffice;

    /**
     * 是否是采购经理
     * true => 是
     * false | null => 不是
     */
    private Boolean procurementManager;

    /**
     * 部门名称
     */
    private String deptName;

    /**
     * 密码判断flag
     */
    private int pjFlag;


    /**
     * 用户签名图片文件id
     **/
    private String imageId;


    public String getImageId() {
        return imageId;
    }

    public void setImageId(String imageId) {
        this.imageId = imageId;
    }

    public int getPjFlag() {
        return pjFlag;
    }

    public void setPjFlag(int pjFlag) {
        this.pjFlag = pjFlag;
    }

    public String getDeptName() {
        return deptName;
    }

    public void setDeptName(String deptName) {
        this.deptName = deptName;
    }

    public Boolean getHeadOffice() {
        return headOffice;
    }

    public void setHeadOffice(Boolean headOffice) {
        this.headOffice = headOffice;
    }

    public Boolean getProcurementManager() {
        return procurementManager;
    }

    public void setProcurementManager(Boolean procurementManager) {
        this.procurementManager = procurementManager;
    }

    public String getQueryNickName() {
        return queryNickName;
    }

    public void setQueryNickName(String queryNickName) {
        this.queryNickName = queryNickName;
    }

    public Boolean getExcludeSelf() {
        return excludeSelf;
    }

    public void setExcludeSelf(Boolean excludeSelf) {
        this.excludeSelf = excludeSelf;
    }

    public Long getExcludeId() {
        return excludeId;
    }

    public void setExcludeId(Long excludeId) {
        this.excludeId = excludeId;
    }

    public String getFlag() {
        return flag;
    }

    public void setFlag(String flag) {
        this.flag = flag;
    }

    public SysUser() {

    }

    public String getDataId() {
        return dataId;
    }

    public void setDataId(String dataId) {
        this.dataId = dataId;
    }

    public SysUser(Long userId) {
        this.userId = userId;
    }

    public Long getUserId() {
        return userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public boolean isAdmin() {
        return isAdmin(this.userId);
    }

    public static boolean isAdmin(Long userId) {
        return userId != null && 1L == userId;
    }

    public Long getDeptId() {
        return deptId;
    }

    public void setDeptId(Long deptId) {
        this.deptId = deptId;
    }

    /* @Size(min = 0, max = 30, message = "用户昵称长度不能超过30个字符")*/
    public String getNickName() {
        return nickName;
    }

    public void setNickName(String nickName) {
        this.nickName = nickName;
    }

    /*  @NotBlank(message = "用户账号不能为空")
      @Size(min = 0, max = 30, message = "用户账号长度不能超过30个字符")*/
    public String getUserName() {
        return userName;
    }

    public void setUserName(String userName) {
        this.userName = userName;
    }

    /*    @Email(message = "邮箱格式不正确")
        @Size(min = 0, max = 50, message = "邮箱长度不能超过50个字符")*/
    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    /* @Size(min = 0, max = 11, message = "手机号码长度不能超过11个字符")*/
    public String getPhonenumber() {
        return phonenumber;
    }

    public void setPhonenumber(String phonenumber) {
        this.phonenumber = phonenumber;
    }

    public String getSex() {
        return sex;
    }

    public void setSex(String sex) {
        this.sex = sex;
    }

    public String getAvatar() {
        return avatar;
    }

    public void setAvatar(String avatar) {
        this.avatar = avatar;
    }

    @JsonIgnore
    @JsonProperty
    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getSalt() {
        return salt;
    }

    public void setSalt(String salt) {
        this.salt = salt;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getDelFlag() {
        return delFlag;
    }

    public void setDelFlag(String delFlag) {
        this.delFlag = delFlag;
    }

    public String getLoginIp() {
        return loginIp;
    }

    public void setLoginIp(String loginIp) {
        this.loginIp = loginIp;
    }

    public Date getLoginDate() {
        return loginDate;
    }

    public void setLoginDate(Date loginDate) {
        this.loginDate = loginDate;
    }

    public SysDept getDept() {
        return dept;
    }

    public void setDept(SysDept dept) {
        this.dept = dept;
    }

    public List<SysRole> getRoles() {
        return roles;
    }

    public void setRoles(List<SysRole> roles) {
        this.roles = roles;
    }

    public Long[] getRoleIds() {
        return roleIds;
    }

    public void setRoleIds(Long[] roleIds) {
        this.roleIds = roleIds;
    }

    public Long[] getPostIds() {
        return postIds;
    }

    public void setPostIds(Long[] postIds) {
        this.postIds = postIds;
    }

    public String getCertId() {
        return certId;
    }

    public void setCertId(String certId) {
        this.certId = certId;
    }

    public String getCertEntityId() {
        return certEntityId;
    }

    public void setCertEntityId(String certEntityId) {
        this.certEntityId = certEntityId;
    }

    @Override
    public String toString() {
        return new ToStringBuilder(this, ToStringStyle.MULTI_LINE_STYLE)
                .append("userId", getUserId())
                .append("deptId", getDeptId())
                .append("userName", getUserName())
                .append("nickName", getNickName())
                .append("email", getEmail())
                .append("phonenumber", getPhonenumber())
                .append("sex", getSex())
                .append("avatar", getAvatar())
                .append("password", getPassword())
                .append("salt", getSalt())
                .append("status", getStatus())
                .append("delFlag", getDelFlag())
                .append("loginIp", getLoginIp())
                .append("loginDate", getLoginDate())
                .append("createBy", getCreateBy())
                .append("createTime", getCreateTime())
                .append("updateBy", getUpdateBy())
                .append("updateTime", getUpdateTime())
                .append("remark", getRemark())
                .append("dept", getDept())
                .toString();
    }

    public String getBussId() {
        return bussId;
    }

    public void setBussId(String bussId) {
        this.bussId = bussId;
    }

    public String getBussName() {
        return bussName;
    }

    public void setBussName(String bussName) {
        this.bussName = bussName;
    }

    public String getEpsName() {
        return epsName;
    }

    public void setEpsName(String epsName) {
        this.epsName = epsName;
    }

    public Long getTenantId() {
        return tenantId;
    }

    public void setTenantId(Long tenantId) {
        this.tenantId = tenantId;
    }


    public String getUserType() {
        return userType;
    }

    public void setUserType(String userType) {
        this.userType = userType;
    }

    public String getRoleCode() {
        return roleCode;
    }

    public void setRoleCode(String roleCode) {
        this.roleCode = roleCode;
    }

    public String getSubCode() {
        return subCode;
    }

    public void setSubCode(String subCode) {
        this.subCode = subCode;
    }

    public Long getUserNo() {
        return userNo;
    }

    public void setUserNo(Long userNo) {
        this.userNo = userNo;
    }

    public String getConfirmPassword() {
        return confirmPassword;
    }

    public void setConfirmPassword(String confirmPassword) {
        this.confirmPassword = confirmPassword;
    }
}
