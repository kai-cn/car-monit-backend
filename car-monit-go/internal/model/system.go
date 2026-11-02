// JAVA 对照: com/ruoyi/common/core/domain/entity/*.java
// JAVA 对照: com/ruoyi/system/src/main/java/com/ruoyi/system/domain/*.java
// 类/职责: 系统模块领域模型 — sys_user / sys_role / sys_menu / sys_dept / sys_post /
//
//	sys_dict_type / sys_dict_data / sys_config / sys_notice / sys_oper_log /
//	sys_logininfor 及关联表
//
// 对应 Go 文件: internal/model/system.go
//
// DIFF: Java 的实体由 MyBatis-Plus 按驼峰-下划线映射；Go 用显式 gorm column 标签 + TableName。
// DIFF: Java 的 Long 包装类型可为 null；可空列用 *int64/*string 表达，清单见 docs/PROGRESS.md §3.5。
package model

import (
	"encoding/json"
	"strconv"

	"car-monit-go/internal/web"
)

// ---------------------------------------------------------------------------
// sys_user
// JAVA 对照: com/ruoyi/common/core/domain/entity/SysUser.java:21-270
// ---------------------------------------------------------------------------
type SysUser struct {
	BaseEntity
	UserID             int64            `json:"userId" gorm:"column:user_id;primaryKey;autoIncrement"`
	UserNo             *int64           `json:"userNo" gorm:"column:user_no"`
	DeptID             int64            `json:"deptId" gorm:"column:dept_id"`
	UserName           *string          `json:"userName" gorm:"column:user_name"`
	NickName           *string          `json:"nickName" gorm:"column:nick_name"`
	UserType           *string          `json:"userType" gorm:"column:user_type"`
	Email              *string          `json:"email" gorm:"column:email"`
	Phonenumber        *string          `json:"phonenumber" gorm:"column:phonenumber"`
	Sex                *string          `json:"sex" gorm:"column:sex"`
	Avatar             *string          `json:"avatar" gorm:"column:avatar"`
	Password           *string          `json:"-" gorm:"column:password"`
	ConfirmPassword    *string          `json:"confirmPassword" gorm:"-"`
	Salt               *string          `json:"salt" gorm:"column:salt"`
	Status             *string          `json:"status" gorm:"column:status"`
	DelFlag            *string          `json:"delFlag" gorm:"column:del_flag"`
	LoginIP            *string          `json:"loginIp" gorm:"column:login_ip"`
	LoginDate          *web.ISODateTime `json:"loginDate" gorm:"column:login_date"`
	CertID             *string          `json:"certId" gorm:"column:cert_id"`
	CertEntityID       *string          `json:"certEntityId" gorm:"column:cert_entity_id"`
	BussID             *string          `json:"bussId" gorm:"column:buss_id"`
	BussName           *string          `json:"bussName" gorm:"column:buss_name"`
	EpsName            *string          `json:"epsName" gorm:"column:eps_name"`
	TenantID           *int64           `json:"tenantId" gorm:"column:tenant_id"`
	TenantName         *string          `json:"tenantName" gorm:"column:tenant_name"`
	RoleCode           *string          `json:"roleCode" gorm:"column:role_code"`
	Dept               *SysDept         `json:"dept" gorm:"-"`
	Roles              []*SysRole       `json:"roles" gorm:"-"`
	RoleIDs            []int64          `json:"roleIds" gorm:"-"`
	PostIDs            []int64          `json:"postIds" gorm:"-"`
	Flag               *string          `json:"flag" gorm:"-"`
	DataID             *string          `json:"dataId" gorm:"-"`
	SubCode            *string          `json:"subCode" gorm:"column:sub_code"`
	QueryNickName      *string          `json:"queryNickName" gorm:"-"`
	ExcludeSelf        *bool            `json:"excludeSelf" gorm:"-"`
	ExcludeID          *int64           `json:"excludeId" gorm:"-"`
	HeadOffice         *bool            `json:"headOffice" gorm:"-"`
	ProcurementManager *bool            `json:"procurementManager" gorm:"-"`
	DeptName           *string          `json:"deptName" gorm:"column:dept_name"`
	PjFlag             int              `json:"pjFlag" gorm:"-"`
	ImageID            *string          `json:"imageId" gorm:"column:image_id"`
}

func (SysUser) TableName() string { return "sys_user" }

func (u *SysUser) IsAdmin() bool { return u != nil && u.UserID == 1 }

// MarshalJSON 复刻 Jackson 把 isAdmin() 也序列化成 "admin" 属性的行为。
func (u SysUser) MarshalJSON() ([]byte, error) {
	type alias SysUser
	return json.Marshal(struct {
		alias
		Admin bool `json:"admin"`
	}{alias: alias(u), Admin: u.UserID == 1})
}

// ---------------------------------------------------------------------------
// sys_role
// JAVA 对照: com/ruoyi/common/core/domain/entity/SysRole.java:17-61
// ---------------------------------------------------------------------------
type SysRole struct {
	BaseEntity
	RoleID            int64   `json:"roleId" gorm:"column:role_id;primaryKey;autoIncrement"`
	RoleName          *string `json:"roleName" gorm:"column:role_name"`
	RoleKey           *string `json:"roleKey" gorm:"column:role_key"`
	RoleSort          *string `json:"roleSort" gorm:"column:role_sort"`
	DataScope         *string `json:"dataScope" gorm:"column:data_scope"`
	MenuCheckStrictly bool    `json:"menuCheckStrictly" gorm:"column:menu_check_strictly"`
	DeptCheckStrictly bool    `json:"deptCheckStrictly" gorm:"column:dept_check_strictly"`
	Status            *string `json:"status" gorm:"column:status"`
	DelFlag           *string `json:"delFlag" gorm:"column:del_flag"`
	Flag              bool    `json:"flag" gorm:"-"`
	MenuIDs           []int64 `json:"menuIds" gorm:"-"`
	DeptIDs           []int64 `json:"deptIds" gorm:"-"`
}

func (SysRole) TableName() string { return "sys_role" }

func (r *SysRole) IsAdmin() bool { return r != nil && r.RoleID == 1 }

// MarshalJSON 复刻 Jackson 把 isAdmin() 也序列化成 "admin" 属性的行为。
func (r SysRole) MarshalJSON() ([]byte, error) {
	type alias SysRole
	return json.Marshal(struct {
		alias
		Admin bool `json:"admin"`
	}{alias: alias(r), Admin: r.RoleID == 1})
}

// ---------------------------------------------------------------------------
// sys_menu
// JAVA 对照: com/ruoyi/common/core/domain/entity/SysMenu.java:17-64
// ---------------------------------------------------------------------------
type SysMenu struct {
	BaseEntity
	MenuID     int64      `json:"menuId" gorm:"column:menu_id;primaryKey;autoIncrement"`
	MenuName   *string    `json:"menuName" gorm:"column:menu_name"`
	ParentName *string    `json:"parentName" gorm:"-"`
	ParentID   int64      `json:"parentId" gorm:"column:parent_id"`
	OrderNum   *string    `json:"orderNum" gorm:"column:order_num"`
	Path       *string    `json:"path" gorm:"column:path"`
	Component  *string    `json:"component" gorm:"column:component"`
	IsFrame    *string    `json:"isFrame" gorm:"column:is_frame"`
	IsCache    *string    `json:"isCache" gorm:"column:is_cache"`
	MenuType   *string    `json:"menuType" gorm:"column:menu_type"`
	Visible    *string    `json:"visible" gorm:"column:visible"`
	Status     *string    `json:"status" gorm:"column:status"`
	Perms      *string    `json:"perms" gorm:"column:perms"`
	Icon       *string    `json:"icon" gorm:"column:icon"`
	Children   []*SysMenu `json:"children" gorm:"-"`
}

func (SysMenu) TableName() string { return "sys_menu" }

// MarshalJSON 复刻 SysMenu.children 初始化为 ArrayList 的行为（Jackson 恒输出数组）。
func (m SysMenu) MarshalJSON() ([]byte, error) {
	type alias SysMenu
	if m.Children == nil {
		m.Children = []*SysMenu{}
	}
	return json.Marshal(alias(m))
}

// Meta 对应 SysMenuServiceImpl.buildMenus 中的 meta 结构。
type Meta struct {
	Title   string `json:"title"`
	Icon    string `json:"icon"`
	NoCache bool   `json:"noCache"`
	Link    string `json:"link,omitempty"`
}

// RouterVo 对应 com/ruoyi/system/domain/vo/RouterVo.java。
type RouterVo struct {
	Name       string      `json:"name,omitempty"`
	Path       string      `json:"path"`
	Hidden     bool        `json:"hidden"`
	Redirect   string      `json:"redirect,omitempty"`
	Component  string      `json:"component"`
	Query      string      `json:"query,omitempty"`
	AlwaysShow bool        `json:"alwaysShow,omitempty"`
	Meta       *Meta       `json:"meta,omitempty"`
	Children   []*RouterVo `json:"children,omitempty"`
}

// ---------------------------------------------------------------------------
// sys_dept
// JAVA 对照: com/ruoyi/common/core/domain/entity/SysDept.java:18-124
// ---------------------------------------------------------------------------
type SysDept struct {
	BaseEntity
	DeptID      int64      `json:"deptId" gorm:"column:dept_id;primaryKey;autoIncrement"`
	ParentID    *int64     `json:"parentId" gorm:"column:parent_id"`
	Ancestors   *string    `json:"ancestors" gorm:"column:ancestors"`
	DeptName    *string    `json:"deptName" gorm:"column:dept_name"`
	OrderNum    *string    `json:"orderNum" gorm:"column:order_num"`
	LeaderID    *int64     `json:"leaderId" gorm:"column:leader_id"`
	Leader      *string    `json:"leader" gorm:"column:leader"`
	FgldID      *int64     `json:"fgldId" gorm:"column:fgld_id"`
	FgldName    *string    `json:"fgldName" gorm:"column:fgld_name"`
	BankName    *string    `json:"bankName" gorm:"column:bank_name"`
	Account     *string    `json:"account" gorm:"column:account"`
	SocialCode  *string    `json:"socialCode" gorm:"column:social_code"`
	PostalCode  *string    `json:"postalCode" gorm:"column:postal_code"`
	Address     *string    `json:"address" gorm:"column:address"`
	Phone       *string    `json:"phone" gorm:"column:phone"`
	Email       *string    `json:"email" gorm:"column:email"`
	Status      *string    `json:"status" gorm:"column:status"`
	IsZbzg      *string    `json:"isZbzg" gorm:"column:is_zbzg"`
	IsUint      *string    `json:"isUint" gorm:"column:is_uint"`
	TreeLeavel  *int       `json:"treeLeavel" gorm:"column:tree_leavel"`
	SubCode     *string    `json:"subCode" gorm:"column:sub_code"`
	DeptJc      *string    `json:"deptJc" gorm:"column:dept_jc"`
	DelFlag     *string    `json:"delFlag" gorm:"column:del_flag"`
	ParentName  *string    `json:"parentName" gorm:"-"`
	Children    []*SysDept `json:"children" gorm:"-"`
	TenantID    *int64     `json:"tenantId" gorm:"column:tenant_id"`
	Flag        *string    `json:"flag" gorm:"column:flag"`
	DataID      *string    `json:"dataId" gorm:"-"`
	DeptSubCode *string    `json:"deptSubCode" gorm:"-"`
}

func (SysDept) TableName() string { return "sys_dept" }

// MarshalJSON 复刻 SysDept.children 初始化为 ArrayList 的行为（Jackson 恒输出数组）。
func (d SysDept) MarshalJSON() ([]byte, error) {
	type alias SysDept
	if d.Children == nil {
		d.Children = []*SysDept{}
	}
	return json.Marshal(alias(d))
}

// ---------------------------------------------------------------------------
// sys_post
// JAVA 对照: com/ruoyi/system/src/main/java/com/ruoyi/system/domain/SysPost.java:16-41
// ---------------------------------------------------------------------------
type SysPost struct {
	BaseEntity
	PostID   int64   `json:"postId" gorm:"column:post_id;primaryKey;autoIncrement"`
	PostCode *string `json:"postCode" gorm:"column:post_code"`
	PostName *string `json:"postName" gorm:"column:post_name"`
	PostSort *string `json:"postSort" gorm:"column:post_sort"`
	Status   *string `json:"status" gorm:"column:status"`
	Flag     bool    `json:"flag" gorm:"-"`
}

func (SysPost) TableName() string { return "sys_post" }

// ---------------------------------------------------------------------------
// sys_dict_type / sys_dict_data
// JAVA 对照: SysDictType.java:17-35; SysDictData.java:18-54
// ---------------------------------------------------------------------------
type SysDictType struct {
	BaseEntity
	DictID   int64   `json:"dictId" gorm:"column:dict_id;primaryKey;autoIncrement"`
	DictName *string `json:"dictName" gorm:"column:dict_name"`
	DictType *string `json:"dictType" gorm:"column:dict_type"`
	Status   *string `json:"status" gorm:"column:status"`
}

func (SysDictType) TableName() string { return "sys_dict_type" }

type SysDictData struct {
	BaseEntity
	DictCode  int64   `json:"dictCode" gorm:"column:dict_code;primaryKey;autoIncrement"`
	DictSort  int64   `json:"dictSort" gorm:"column:dict_sort"`
	DictLabel *string `json:"dictLabel" gorm:"column:dict_label"`
	DictValue *string `json:"dictValue" gorm:"column:dict_value"`
	DictType  *string `json:"dictType" gorm:"column:dict_type"`
	CssClass  *string `json:"cssClass" gorm:"column:css_class"`
	ListClass *string `json:"listClass" gorm:"column:list_class"`
	IsDefault *string `json:"isDefault" gorm:"column:is_default"`
	Status    *string `json:"status" gorm:"column:status"`
}

// MarshalJSON 复刻 SysDictData.isDefault() 派生出的 "default" 属性。
func (d SysDictData) MarshalJSON() ([]byte, error) {
	type alias SysDictData
	isDefault := d.IsDefault != nil && *d.IsDefault == "Y"
	return json.Marshal(struct {
		alias
		Default bool `json:"default"`
	}{alias: alias(d), Default: isDefault})
}

func (SysDictData) TableName() string { return "sys_dict_data" }

// ---------------------------------------------------------------------------
// sys_config / sys_notice
// JAVA 对照: SysConfig.java:16-38; SysNotice.java:15-60
// ---------------------------------------------------------------------------
type SysConfig struct {
	BaseEntity
	ConfigID    int64   `json:"configId" gorm:"column:config_id;primaryKey;autoIncrement"`
	ConfigName  *string `json:"configName" gorm:"column:config_name"`
	ConfigKey   *string `json:"configKey" gorm:"column:config_key"`
	ConfigValue *string `json:"configValue" gorm:"column:config_value"`
	ConfigType  *string `json:"configType" gorm:"column:config_type"`
}

func (SysConfig) TableName() string { return "sys_config" }

type SysNotice struct {
	BaseEntity
	NoticeID      int64   `json:"noticeId" gorm:"column:notice_id;primaryKey;autoIncrement"`
	NoticeTitle   *string `json:"noticeTitle" gorm:"column:notice_title"`
	NoticeType    *string `json:"noticeType" gorm:"column:notice_type"`
	NoticeContent *string `json:"noticeContent" gorm:"column:notice_content"`
	Status        *string `json:"status" gorm:"column:status"`
	BussID        *string `json:"bussId" gorm:"column:buss_id"`
	BussName      *string `json:"bussName" gorm:"column:buss_name"`
	TenantID      int64   `json:"tenantId" gorm:"column:tenant_id"`
}

func (SysNotice) TableName() string { return "sys_notice" }

// ---------------------------------------------------------------------------
// sys_oper_log / sys_logininfor
// JAVA 对照: SysOperLog.java:14-83; SysLogininfor.java:14-53
// ---------------------------------------------------------------------------
type SysOperLog struct {
	BaseEntity
	OperID        int64         `json:"operId" gorm:"column:oper_id;primaryKey;autoIncrement"`
	Title         *string       `json:"title" gorm:"column:title"`
	BusinessType  int           `json:"businessType" gorm:"column:business_type"`
	BusinessTypes []int         `json:"businessTypes" gorm:"-"`
	Method        *string       `json:"method" gorm:"column:method"`
	RequestMethod *string       `json:"requestMethod" gorm:"column:request_method"`
	OperatorType  int           `json:"operatorType" gorm:"column:operator_type"`
	OperName      *string       `json:"operName" gorm:"column:oper_name"`
	DeptName      *string       `json:"deptName" gorm:"column:dept_name"`
	OperURL       *string       `json:"operUrl" gorm:"column:oper_url"`
	OperIP        *string       `json:"operIp" gorm:"column:oper_ip"`
	OperLocation  *string       `json:"operLocation" gorm:"column:oper_location"`
	OperParam     *string       `json:"operParam" gorm:"column:oper_param"`
	JSONResult    *string       `json:"jsonResult" gorm:"column:json_result"`
	Status        int           `json:"status" gorm:"column:status"`
	ErrorMsg      *string       `json:"errorMsg" gorm:"column:error_msg"`
	OperTime      *web.DateTime `json:"operTime" gorm:"column:oper_time"`
}

func (SysOperLog) TableName() string { return "sys_oper_log" }

type SysLogininfor struct {
	BaseEntity
	InfoID        int64         `json:"infoId" gorm:"column:info_id;primaryKey;autoIncrement"`
	UserName      *string       `json:"userName" gorm:"column:user_name"`
	Status        *string       `json:"status" gorm:"column:status"`
	IPAddr        *string       `json:"ipaddr" gorm:"column:ipaddr"`
	LoginLocation *string       `json:"loginLocation" gorm:"column:login_location"`
	Browser       *string       `json:"browser" gorm:"column:browser"`
	OS            *string       `json:"os" gorm:"column:os"`
	Msg           *string       `json:"msg" gorm:"column:msg"`
	LoginTime     *web.DateTime `json:"loginTime" gorm:"column:login_time"`
}

func (SysLogininfor) TableName() string { return "sys_logininfor" }

// SysUserOnline 对应 com ruoyi.system.domain.SysUserOnline（非表实体，Redis 派生）。
type SysUserOnline struct {
	TokenID       string `json:"tokenId"`
	SessionID     string `json:"sessionId"`
	DeptName      string `json:"deptName"`
	UserName      string `json:"userName"`
	IPAddr        string `json:"ipaddr"`
	LoginLocation string `json:"loginLocation"`
	Browser       string `json:"browser"`
	OS            string `json:"os"`
	LoginTime     int64  `json:"loginTime"`
}

// ---------------------------------------------------------------------------
// 关联表
// ---------------------------------------------------------------------------
type SysUserRole struct {
	UserID int64 `json:"userId" gorm:"column:user_id;primaryKey"`
	RoleID int64 `json:"roleId" gorm:"column:role_id;primaryKey"`
}

func (SysUserRole) TableName() string { return "sys_user_role" }

type SysUserPost struct {
	UserID int64 `json:"userId" gorm:"column:user_id;primaryKey"`
	PostID int64 `json:"postId" gorm:"column:post_id;primaryKey"`
}

func (SysUserPost) TableName() string { return "sys_user_post" }

type SysRoleMenu struct {
	RoleID int64 `json:"roleId" gorm:"column:role_id;primaryKey"`
	MenuID int64 `json:"menuId" gorm:"column:menu_id;primaryKey"`
}

func (SysRoleMenu) TableName() string { return "sys_role_menu" }

type SysRoleDept struct {
	RoleID int64 `json:"roleId" gorm:"column:role_id;primaryKey"`
	DeptID int64 `json:"deptId" gorm:"column:dept_id;primaryKey"`
}

func (SysRoleDept) TableName() string { return "sys_role_dept" }

// ---------------------------------------------------------------------------
// 其他业务系统表
// ---------------------------------------------------------------------------
// SysIndexMenu 对应 sys_index_menu（extends BaseUuidEntity）。
//
// DIFF: Java 的 id 是 String（UUID 生成），而本库该列是 bigint AUTO_INCREMENT；
// 只有 insertSysIndexMenu（不写 id）能正常落库，saveSysIndexMenu 的新增分支
// 会把 UUID 写进 bigint 列并在 MySQL 严格模式下报错 —— 与 Java 行为一致。
type SysIndexMenu struct {
	BaseUUID
	UserID    *int64  `json:"userId" gorm:"column:user_id"`
	MenuID    *int64  `json:"menuId" gorm:"column:menu_id"`
	MenuName  *string `json:"menuName" gorm:"column:menu_name"`
	MenuName1 *string `json:"menuName1" gorm:"-"`
	MenuName2 *string `json:"menuName2" gorm:"column:menu_name2"`
	MenuName3 *string `json:"menuName3" gorm:"-"`
	MenuIDs   *string `json:"menuIds" gorm:"-"`
	MenuURL   *string `json:"menuUrl" gorm:"column:menu_url"`
}

func (SysIndexMenu) TableName() string { return "sys_index_menu" }

type SysFile struct {
	ID             int64         `json:"-" gorm:"column:id;primaryKey;autoIncrement"`
	FileName       *string       `json:"fileName" gorm:"column:file_name"`
	BucketName     *string       `json:"bucketName" gorm:"column:bucket_name"`
	Original       *string       `json:"original" gorm:"column:original"`
	Type           *string       `json:"type" gorm:"column:type"`
	FileSize       int64         `json:"fileSize" gorm:"column:file_size"`
	BussType       *string       `json:"bussType" gorm:"column:buss_type"`
	BussName       *string       `json:"bussName" gorm:"column:buss_name"`
	CreateTime     *web.DateTime `json:"createTime" gorm:"column:create_time"`
	CreateUser     *string       `json:"createUser" gorm:"column:create_user"`
	UpdateTime     *web.DateTime `json:"updateTime" gorm:"column:update_time"`
	UpdateUser     *string       `json:"updateUser" gorm:"column:update_user"`
	DelFlag        *string       `json:"delFlag" gorm:"column:del_flag"`
	TenantID       *int64        `json:"tenantId" gorm:"column:tenant_id"`
	Files          *string       `json:"files" gorm:"-"`
	CreateUserName *string       `json:"createUserName" gorm:"column:create_user_name"`
}

func (SysFile) TableName() string { return "sys_file" }

// MarshalJSON 复刻 SysFile.id 上的 @JsonSerialize(using = ToStringSerializer.class)，
// 并保持 Java 字段声明顺序（encoding/json 的内嵌结构体会把外层的 id 挪到最后）。
func (f SysFile) MarshalJSON() ([]byte, error) {
	return json.Marshal(struct {
		ID             string        `json:"id"`
		FileName       *string       `json:"fileName"`
		BucketName     *string       `json:"bucketName"`
		Original       *string       `json:"original"`
		Type           *string       `json:"type"`
		FileSize       int64         `json:"fileSize"`
		BussType       *string       `json:"bussType"`
		BussName       *string       `json:"bussName"`
		CreateTime     *web.DateTime `json:"createTime"`
		CreateUser     *string       `json:"createUser"`
		UpdateTime     *web.DateTime `json:"updateTime"`
		UpdateUser     *string       `json:"updateUser"`
		DelFlag        *string       `json:"delFlag"`
		TenantID       *int64        `json:"tenantId"`
		Files          *string       `json:"files"`
		CreateUserName *string       `json:"createUserName"`
	}{
		ID:             strconv.FormatInt(f.ID, 10),
		FileName:       f.FileName,
		BucketName:     f.BucketName,
		Original:       f.Original,
		Type:           f.Type,
		FileSize:       f.FileSize,
		BussType:       f.BussType,
		BussName:       f.BussName,
		CreateTime:     f.CreateTime,
		CreateUser:     f.CreateUser,
		UpdateTime:     f.UpdateTime,
		UpdateUser:     f.UpdateUser,
		DelFlag:        f.DelFlag,
		TenantID:       f.TenantID,
		Files:          f.Files,
		CreateUserName: f.CreateUserName,
	})
}

// SysUpgradeInfo 对应 sys_upgrade_info（extends BaseUuidEntity）。
// 本地基线库没有这张表；DDL 以 Java 实体/映射为准（id 为字符串主键）。
type SysUpgradeInfo struct {
	BaseUUID
	Ver      *string `json:"ver" gorm:"column:ver"`
	Info     *string `json:"info" gorm:"column:info"`
	BackCol1 *string `json:"backCol1" gorm:"column:back_col1"`
}

func (SysUpgradeInfo) TableName() string { return "sys_upgrade_info" }

// ---------------------------------------------------------------------------
// 登录相关 DTO
// JAVA 对照: com/ruoyi/common/core/domain/model/LoginBody.java
// JAVA 对照: com/ruoyi/common/core/domain/model/LoginUser.java:16-76
// ---------------------------------------------------------------------------
type LoginBody struct {
	Username string `json:"username"`
	Password string `json:"password"`
	Code     string `json:"code"`
	UUID     string `json:"uuid"`
}

type LoginUser struct {
	Token         string   `json:"token"`
	SessionID     string   `json:"sessionId"`
	LoginTime     int64    `json:"loginTime"`
	ExpireTime    int64    `json:"expireTime"`
	IPAddr        string   `json:"ipaddr"`
	LoginLocation string   `json:"loginLocation"`
	Browser       string   `json:"browser"`
	OS            string   `json:"os"`
	Permissions   []string `json:"permissions"`
	User          *SysUser `json:"user"`
}

func (l *LoginUser) Username() string {
	if l == nil || l.User == nil {
		return ""
	}
	return Str(l.User.UserName)
}

func (l *LoginUser) UserID() int64 {
	if l == nil || l.User == nil {
		return 0
	}
	return l.User.UserID
}

func (l *LoginUser) IsAdmin() bool { return l != nil && l.User != nil && l.User.IsAdmin() }

func (l *LoginUser) HasPermission(perm string) bool {
	if l == nil {
		return false
	}
	for _, p := range l.Permissions {
		if p == "*:*:*" || p == perm {
			return true
		}
	}
	return false
}

// RegisterBody 对应 com/ruoyi/common/core/domain/model/RegisterBody.java。
type RegisterBody struct {
	Username string `json:"username"`
	Password string `json:"password"`
	Code     string `json:"code"`
	UUID     string `json:"uuid"`
}
