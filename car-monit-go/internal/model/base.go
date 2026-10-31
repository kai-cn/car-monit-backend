// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/BaseEntity.java
// 类/职责: 实体基类 — 创建人/创建时间/更新人/更新时间/备注/查询参数
// 对应 Go 文件: internal/model/base.go
//
// DIFF: Java 的 Date 用 @JsonFormat 输出 "yyyy-MM-dd HH:mm:ss"，
// Go 用 web.DateTime 承担；searchValue 标 @JsonIgnore，因此 json:"-"。
// DIFF: Jackson 默认输出 null，Go 的 string 零值是 ""；前端对二者等价，差异记录在 docs/COMPATIBILITY.md。
package model

import "car-monit-go/internal/web"

// BaseEntity 对应 com.ruoyi.common.core.domain.BaseEntity。
type BaseEntity struct {
	SearchValue string         `json:"-" gorm:"-"`
	CreateBy    *string        `json:"createBy" gorm:"column:create_by"`
	CreateTime  *web.DateTime  `json:"createTime" gorm:"column:create_time"`
	UpdateBy    *string        `json:"updateBy" gorm:"column:update_by"`
	UpdateTime  *web.DateTime  `json:"updateTime" gorm:"column:update_time"`
	Remark      *string        `json:"remark" gorm:"column:remark"`
	Params      map[string]any `json:"params,omitempty" gorm:"-"`
}

// BaseUUID 对应 com.ruoyi.common.core.domain.BaseUuidEntity。
// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/BaseUuidEntity.java
//
// DIFF: Java 的 audit 字段是 Long（非 null），本工程用指针保留 null 语义；
// id 在 Java 是 String（bigint 主键由 MyBatis 自动转字符串），这里同样是 *string。
type BaseUUID struct {
	ID          *string        `json:"id" gorm:"column:id"`
	EpsID       *int64         `json:"epsId" gorm:"column:eps_id"`
	DelFlag     *string        `json:"delFlag" gorm:"column:del_flag"`
	CreateBy    *int64         `json:"createBy" gorm:"column:create_by"`
	CreateTime  *web.DateTime  `json:"createTime" gorm:"column:create_time"`
	UpdateBy    *int64         `json:"updateBy" gorm:"column:update_by"`
	UpdateTime  *web.DateTime  `json:"updateTime" gorm:"column:update_time"`
	Sort        *int64         `json:"sort" gorm:"column:sort"`
	Remark      *string        `json:"remark" gorm:"column:remark"`
	TenantID    *int64         `json:"tenantId" gorm:"column:tenant_id"`
	DeptSubCode *string        `json:"deptSubCode" gorm:"column:dept_sub_code"`
	Flag        *string        `json:"flag" gorm:"-"`
	SearchValue *string        `json:"searchValue" gorm:"-"`
	Params      map[string]any `json:"params" gorm:"-"`
}

// TreeSelect 对应 com.ruoyi.common.core.domain.TreeSelect。
type TreeSelect struct {
	ID       int64         `json:"id"`
	Label    string        `json:"label"`
	Children []*TreeSelect `json:"children,omitempty"`
}

// AuditTimeFields 为需要审计字段的插入语句提供统一取值。
func (b *BaseEntity) SetCreate(by string) {
	now := web.Now()
	b.CreateBy = &by
	b.CreateTime = &now
	b.UpdateBy = &by
	b.UpdateTime = &now
}

func (b *BaseEntity) SetUpdate(by string) {
	now := web.Now()
	b.UpdateBy = &by
	b.UpdateTime = &now
}

// Str 取可空字符串的值（nil -> ""）。
func Str(s *string) string {
	if s == nil {
		return ""
	}
	return *s
}

// Ptr 生成可空字符串指针。
func Ptr(s string) *string { return &s }

// Bool 取可空布尔值（nil -> false）。
func Bool(b *bool) bool { return b != nil && *b }

// Int64Val 取可空 int64（nil -> 0）。
func Int64Val(v *int64) int64 {
	if v == nil {
		return 0
	}
	return *v
}

// IntVal 取可空 int（nil -> 0）。
func IntVal(v *int) int {
	if v == nil {
		return 0
	}
	return *v
}

// Int64Ptr 生成可空 int64 指针。
func Int64Ptr(v int64) *int64 { return &v }

// IntPtr 生成可空 int 指针。
func IntPtr(v int) *int { return &v }

// BoolPtr 生成可空布尔指针。
func BoolPtr(v bool) *bool { return &v }
