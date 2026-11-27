// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/aspectj/DataScopeAspect.java:102-153
// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/annotation/DataScope.java
// 类/职责: @DataScope 数据权限过滤 —— 按当前登录用户角色拼接 dept_id/user_id 条件
// 对应 Go 文件: internal/modules/system/datascope.go
//
// DIFF: Java 用 AOP 在 Mapper 调用前把片段塞进 BaseEntity.params["dataScope"]，
// 由 MyBatis ${} 拼接（存在注入面）；Go 在构造 SQL 时直接返回参数化片段，
// 片段中只含占位符与整型角色/部门 ID，不再把字符串拼进 SQL。
package system

import (
	"fmt"
	"strings"

	"car-monit-go/internal/model"
)

const (
	dataScopeAll          = "1"
	dataScopeCustom       = "2"
	dataScopeDept         = "3"
	dataScopeDeptAndChild = "4"
	dataScopeSelf         = "5"
)

// dataScopeCond 对应 DataScopeAspect.dataScopeFilter：返回形如 " AND (...)" 的片段，
// 返回空串表示不加过滤（超级管理员或角色含“全部数据权限”）。
//
// deptAlias / userAlias 对应 @DataScope(deptAlias = "d", userAlias = "u")。
func dataScopeCond(lu *model.LoginUser, deptAlias, userAlias string) (string, []any) {
	if lu == nil || lu.User == nil || lu.User.IsAdmin() {
		return "", nil
	}
	user := lu.User
	var sb strings.Builder
	args := make([]any, 0, 4)
	for _, role := range user.Roles {
		if role == nil {
			continue
		}
		switch model.Str(role.DataScope) {
		case dataScopeAll:
			// Java: 命中“全部数据权限”后清空已累计的条件并跳出循环。
			return "", nil
		case dataScopeCustom:
			fmt.Fprintf(&sb, " OR %s.dept_id IN ( SELECT dept_id FROM sys_role_dept WHERE role_id = ? ) ", deptAlias)
			args = append(args, role.RoleID)
		case dataScopeDept:
			fmt.Fprintf(&sb, " OR %s.dept_id = ? ", deptAlias)
			args = append(args, user.DeptID)
		case dataScopeDeptAndChild:
			fmt.Fprintf(&sb,
				" OR %s.dept_id IN ( SELECT dept_id FROM sys_dept WHERE dept_id = ? or find_in_set( ? , ancestors ) )",
				deptAlias)
			args = append(args, user.DeptID, user.DeptID)
		case dataScopeSelf:
			if strings.TrimSpace(userAlias) != "" {
				fmt.Fprintf(&sb, " OR %s.user_id = ? ", userAlias)
				args = append(args, user.UserID)
			} else {
				// 数据权限为仅本人且没有 userAlias 别名时不查询任何数据。
				sb.WriteString(" OR 1=0 ")
			}
		}
	}
	cond := sb.String()
	if strings.TrimSpace(cond) == "" {
		return "", nil
	}
	// Java: " AND (" + sqlString.substring(4) + ")" —— 去掉首个 " OR "。
	return " AND (" + cond[4:] + ")", args
}
