// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysMenuServiceImpl.java:64-419
// JAVA 对照: ruoyi-system/src/main/resources/mapper/system/SysMenuMapper.xml:29-198
// 类/职责: 菜单业务层 —— 列表（管理员/普通用户两套 SQL）/树/角色已选菜单/增删改/唯一性校验
// 对应 Go 文件: internal/modules/system/menu_service.go
//
// DIFF: Java 的 buildMenus/getChildPerms 已在 internal/service/menusvc 中实现（登录路由复用），
// 本文件只补充“管理端”查询与写入；树构建复用 menusvc.BuildMenuTree。
// DIFF: Java 的 SysMenu.children 初始化为 ArrayList，叶子节点序列化为 "children":[]；
// Go 的 model.SysMenu 使用 omitempty，叶子节点不输出 children（前端等价，见 COMPATIBILITY）。
package system

import (
	"context"
	"strings"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/model"
	"car-monit-go/internal/service/menusvc"
	"car-monit-go/internal/web"
)

// menuQuery 对应作为查询条件传入的 SysMenu。
type menuQuery struct {
	MenuName string
	Visible  string
	Status   string
}

func parseMenuQuery(c *gin.Context) menuQuery {
	return menuQuery{
		MenuName: queryStr(c, "menuName"),
		Visible:  queryStr(c, "visible"),
		Status:   queryStr(c, "status"),
	}
}

// menuSelectVo 对应 SysMenuMapper.xml:29-32 selectMenuVo。
const menuSelectVo = `
	select menu_id, menu_name, parent_id, order_num, path, component, is_frame, is_cache,
	       menu_type, visible, status, ifnull(perms,'') as perms, icon, create_time
	from sys_menu`

// menuTreeSelectVo 对应 selectMenuListByUserId 的列清单。
const menuTreeSelectVo = `
	select distinct m.menu_id, m.parent_id, m.menu_name, m.path, m.component, m.visible, m.status,
	       ifnull(m.perms,'') as perms, m.is_frame, m.is_cache, m.menu_type, m.icon, m.order_num, m.create_time
	from sys_menu m`

// where 复刻 selectMenuList / selectMenuListByUserId 的 <if> 条件；alias 为空表示无表别名。
func (q menuQuery) where(alias string) (string, []any) {
	p := ""
	if alias != "" {
		p = alias + "."
	}
	var sb strings.Builder
	args := make([]any, 0, 4)
	first := true
	and := func(cond string, v any) {
		if first {
			sb.WriteString(" where ")
			first = false
		} else {
			sb.WriteString(" and ")
		}
		sb.WriteString(cond)
		args = append(args, v)
	}
	if q.MenuName != "" {
		and(p+"menu_name like concat('%', ?, '%')", q.MenuName)
	}
	if q.Visible != "" {
		and(p+"visible = ?", q.Visible)
	}
	if q.Status != "" {
		and(p+"status = ?", q.Status)
	}
	return sb.String(), args
}

// selectMenuList 对应 SysMenuServiceImpl.selectMenuList(menu, userId)：
// 管理员走 selectMenuList，普通用户走 selectMenuListByUserId（按角色过滤）。
func (s *service) selectMenuList(ctx context.Context, q menuQuery, userID int64) ([]*model.SysMenu, error) {
	rows := make([]*model.SysMenu, 0)
	if userID == 1 {
		where, args := q.where("")
		err := s.db(ctx).Raw(menuSelectVo+where+" order by parent_id, order_num", args...).Scan(&rows).Error
		if err != nil {
			return nil, err
		}
		return rows, nil
	}
	where, args := q.where("m")
	sql := menuTreeSelectVo + `
		left join sys_role_menu rm on m.menu_id = rm.menu_id
		left join sys_user_role ur on rm.role_id = ur.role_id
		left join sys_role ro on ur.role_id = ro.role_id
		where ur.user_id = ?`
	allArgs := make([]any, 0, len(args)+1)
	allArgs = append(allArgs, userID)
	if where != "" {
		sql += " and " + strings.TrimPrefix(where, " where ")
		allArgs = append(allArgs, args...)
	}
	sql += " order by m.parent_id, m.order_num"
	if err := s.db(ctx).Raw(sql, allArgs...).Scan(&rows).Error; err != nil {
		return nil, err
	}
	return rows, nil
}

// selectMenuByID 对应 SysMenuMapper.selectMenuById。
func (s *service) selectMenuByID(ctx context.Context, menuID int64) (*model.SysMenu, error) {
	var m model.SysMenu
	if err := s.db(ctx).Raw(menuSelectVo+" where menu_id = ?", menuID).Scan(&m).Error; err != nil {
		return nil, err
	}
	if m.MenuID == 0 {
		return nil, nil
	}
	return &m, nil
}

// selectMenuListByRoleID 对应 SysMenuServiceImpl.selectMenuListByRoleId。
func (s *service) selectMenuListByRoleID(ctx context.Context, roleID int64) ([]int64, error) {
	strict := false
	role, err := s.selectRoleByID(ctx, roleID)
	if err != nil {
		return nil, err
	}
	if role != nil {
		strict = role.MenuCheckStrictly
	}
	sql := `select m.menu_id from sys_menu m
		left join sys_role_menu rm on m.menu_id = rm.menu_id
		where rm.role_id = ?`
	args := []any{roleID}
	if strict {
		sql += ` and m.menu_id not in (select m.parent_id from sys_menu m
			inner join sys_role_menu rm on m.menu_id = rm.menu_id and rm.role_id = ?)`
		args = append(args, roleID)
	}
	sql += " order by m.parent_id, m.order_num"
	ids := make([]int64, 0)
	if err := s.db(ctx).Raw(sql, args...).Scan(&ids).Error; err != nil {
		return nil, err
	}
	return ids, nil
}

// checkMenuNameUnique 对应 SysMenuMapper.checkMenuNameUnique：按 (menu_name, parent_id) 判重。
func (s *service) checkMenuNameUnique(ctx context.Context, menuName string, parentID int64) (*model.SysMenu, error) {
	var m model.SysMenu
	err := s.db(ctx).Raw(menuSelectVo+" where menu_name = ? and parent_id = ? limit 1", menuName, parentID).Scan(&m).Error
	if err != nil {
		return nil, err
	}
	if m.MenuID == 0 {
		return nil, nil
	}
	return &m, nil
}

// hasChildByMenuID 对应 SysMenuMapper.hasChildByMenuId。
func (s *service) hasChildByMenuID(ctx context.Context, menuID int64) (bool, error) {
	var n int64
	err := s.db(ctx).Raw("select count(1) from sys_menu where parent_id = ?", menuID).Scan(&n).Error
	return n > 0, err
}

// checkMenuExistRole 对应 SysRoleMenuMapper.checkMenuExistRole。
func (s *service) checkMenuExistRole(ctx context.Context, menuID int64) (bool, error) {
	var n int64
	err := s.db(ctx).Raw("select count(1) from sys_role_menu where menu_id = ?", menuID).Scan(&n).Error
	return n > 0, err
}

// buildMenuTreeSelect 对应 SysMenuServiceImpl.buildMenuTreeSelect。
func buildMenuTreeSelect(menus []*model.SysMenu) []*model.TreeSelect {
	trees := menusvc.BuildMenuTree(menus)
	out := make([]*model.TreeSelect, 0, len(trees))
	for _, m := range trees {
		out = append(out, menuTreeSelectNode(m))
	}
	return out
}

func menuTreeSelectNode(m *model.SysMenu) *model.TreeSelect {
	ts := &model.TreeSelect{ID: m.MenuID, Label: model.Str(m.MenuName)}
	if len(m.Children) > 0 {
		ts.Children = make([]*model.TreeSelect, 0, len(m.Children))
		for _, child := range m.Children {
			ts.Children = append(ts.Children, menuTreeSelectNode(child))
		}
	}
	return ts
}

// menuBody 对应 @RequestBody SysMenu。
type menuBody struct {
	MenuID    *int64  `json:"menuId"`
	ParentID  *int64  `json:"parentId"`
	MenuName  *string `json:"menuName"`
	OrderNum  *string `json:"orderNum"`
	Path      *string `json:"path"`
	Component *string `json:"component"`
	IsFrame   *string `json:"isFrame"`
	IsCache   *string `json:"isCache"`
	MenuType  *string `json:"menuType"`
	Visible   *string `json:"visible"`
	Status    *string `json:"status"`
	Perms     *string `json:"perms"`
	Icon      *string `json:"icon"`
	Remark    *string `json:"remark"`
}

// validate 对应 SysMenu 上的 @Validated 约束（GlobalExceptionHandler 取第一条错误）。
func (b *menuBody) validate() string {
	switch {
	case strings.TrimSpace(strOr(b.MenuName)) == "":
		return "菜单名称不能为空"
	case len([]rune(strOr(b.MenuName))) > 50:
		return "菜单名称长度不能超过50个字符"
	case strings.TrimSpace(strOr(b.OrderNum)) == "":
		return "显示顺序不能为空"
	case len([]rune(strOr(b.Path))) > 200:
		return "路由地址不能超过200个字符"
	case len([]rune(strOr(b.Component))) > 200:
		return "组件路径不能超过255个字符"
	case strings.TrimSpace(strOr(b.MenuType)) == "":
		return "菜单类型不能为空"
	case len([]rune(strOr(b.Perms))) > 100:
		return "权限标识长度不能超过100个字符"
	}
	return ""
}

// insertMenu 对应 SysMenuMapper.insertMenu 的动态列。
func (s *service) insertMenu(ctx context.Context, b *menuBody, createBy string) (int64, error) {
	cols := make([]string, 0, 16)
	vals := make([]any, 0, 16)
	add := func(col string, v any) {
		cols = append(cols, col)
		vals = append(vals, v)
	}
	if b.MenuID != nil && *b.MenuID != 0 {
		add("menu_id", *b.MenuID)
	}
	if b.ParentID != nil && *b.ParentID != 0 {
		add("parent_id", *b.ParentID)
	}
	if strOr(b.MenuName) != "" {
		add("menu_name", *b.MenuName)
	}
	if strOr(b.OrderNum) != "" {
		add("order_num", *b.OrderNum)
	}
	if strOr(b.Path) != "" {
		add("path", *b.Path)
	}
	if strOr(b.Component) != "" {
		add("component", *b.Component)
	}
	if strOr(b.IsFrame) != "" {
		add("is_frame", *b.IsFrame)
	}
	if strOr(b.IsCache) != "" {
		add("is_cache", *b.IsCache)
	}
	if strOr(b.MenuType) != "" {
		add("menu_type", *b.MenuType)
	}
	if b.Visible != nil {
		add("visible", *b.Visible)
	}
	if b.Status != nil {
		add("status", *b.Status)
	}
	if strOr(b.Perms) != "" {
		add("perms", *b.Perms)
	}
	if strOr(b.Icon) != "" {
		add("icon", *b.Icon)
	}
	if strOr(b.Remark) != "" {
		add("remark", *b.Remark)
	}
	if createBy != "" {
		add("create_by", createBy)
	}
	add("create_time", now())
	sql := "insert into sys_menu (" + strings.Join(cols, ", ") + ") values (" + placeholders(len(cols)) + ")"
	res := s.db(ctx).Exec(sql, vals...)
	return res.RowsAffected, res.Error
}

// updateMenu 对应 SysMenuMapper.updateMenu 的 <set> 分支。
func (s *service) updateMenu(ctx context.Context, b *menuBody, updateBy string) (int64, error) {
	if b.MenuID == nil {
		return 0, web.NewServiceError("菜单ID不能为空")
	}
	sets := make([]string, 0, 16)
	args := make([]any, 0, 18)
	strCol := func(col string, p *string, requireNonEmpty bool) {
		if p == nil {
			return
		}
		if requireNonEmpty && *p == "" {
			return
		}
		sets = append(sets, col+" = ?")
		args = append(args, *p)
	}
	strCol("menu_name", b.MenuName, true)
	if b.ParentID != nil {
		sets = append(sets, "parent_id = ?")
		args = append(args, *b.ParentID)
	}
	strCol("order_num", b.OrderNum, true)
	strCol("path", b.Path, true)
	strCol("component", b.Component, false)
	strCol("is_frame", b.IsFrame, true)
	strCol("is_cache", b.IsCache, true)
	strCol("menu_type", b.MenuType, true)
	strCol("visible", b.Visible, false)
	strCol("status", b.Status, false)
	strCol("perms", b.Perms, false)
	strCol("icon", b.Icon, true)
	strCol("remark", b.Remark, true)
	if updateBy != "" {
		sets = append(sets, "update_by = ?")
		args = append(args, updateBy)
	}
	sets = append(sets, "update_time = ?")
	args = append(args, now())
	args = append(args, *b.MenuID)
	res := s.db(ctx).Exec("update sys_menu set "+strings.Join(sets, ", ")+" where menu_id = ?", args...)
	return res.RowsAffected, res.Error
}

// deleteMenuByID 对应 SysMenuMapper.deleteMenuById（物理删除）。
func (s *service) deleteMenuByID(ctx context.Context, menuID int64) (int64, error) {
	res := s.db(ctx).Exec("delete from sys_menu where menu_id = ?", menuID)
	return res.RowsAffected, res.Error
}
