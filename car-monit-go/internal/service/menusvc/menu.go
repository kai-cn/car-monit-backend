// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysMenuServiceImpl.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/system/SysMenuMapper.xml
// 类/职责: 菜单树查询与前端路由（RouterVo）构建
// 对应 Go 文件: internal/service/menusvc/menu.go
package menusvc

import (
	"context"
	"strings"

	"gorm.io/gorm"

	"car-monit-go/internal/model"
)

// UserConstants 中与路由构建相关的常量。
// JAVA 对照: com/ruoyi/common/constant/UserConstants.java:40-58
const (
	NoFrame    = "1"
	TypeDir    = "M"
	TypeMenu   = "C"
	Layout     = "Layout"
	ParentView = "ParentView"
)

type Service struct {
	db *gorm.DB
}

func New(db *gorm.DB) *Service { return &Service{db: db} }

// SelectMenuTreeByUserId 对应 SysMenuServiceImpl.selectMenuTreeByUserId。
func (s *Service) SelectMenuTreeByUserId(ctx context.Context, userID int64) ([]*model.SysMenu, error) {
	var menus []*model.SysMenu
	var err error
	if userID == 1 {
		// JAVA 对照: SysMenuMapper.xml:50-54 selectMenuTreeAll
		err = s.db.WithContext(ctx).Raw(`
			select distinct m.menu_id, m.parent_id, m.menu_name, m.path, m.component, m.visible,
			       m.status, ifnull(m.perms,'') as perms, m.is_frame, m.is_cache, m.menu_type,
			       m.icon, m.order_num, m.create_time
			from sys_menu m
			where m.menu_type in ('M', 'C') and m.status = 0
			order by m.parent_id, m.order_num`).Scan(&menus).Error
	} else {
		// JAVA 对照: SysMenuMapper.xml:75-84 selectMenuTreeByUserId
		err = s.db.WithContext(ctx).Raw(`
			select distinct m.menu_id, m.parent_id, m.menu_name, m.path, m.component, m.visible,
			       m.status, ifnull(m.perms,'') as perms, m.is_frame, m.is_cache, m.menu_type,
			       m.icon, m.order_num, m.create_time
			from sys_menu m
			left join sys_role_menu rm on m.menu_id = rm.menu_id
			left join sys_user_role ur on rm.role_id = ur.role_id
			left join sys_role ro on ur.role_id = ro.role_id
			left join sys_user u on ur.user_id = u.user_id
			where u.user_id = ? and m.menu_type in ('M', 'C') and m.status = 0 and ro.status = 0
			order by m.parent_id, m.order_num`, userID).Scan(&menus).Error
	}
	if err != nil {
		return nil, err
	}
	return GetChildPerms(menus, 0), nil
}

// BuildMenus 对应 SysMenuServiceImpl.buildMenus。
func (s *Service) BuildMenus(menus []*model.SysMenu) []*model.RouterVo {
	routers := make([]*model.RouterVo, 0, len(menus))
	for _, menu := range menus {
		router := &model.RouterVo{
			Hidden:    model.Str(menu.Visible) == "1",
			Name:      routeName(menu),
			Path:      routerPath(menu),
			Component: component(menu),
			Meta: &model.Meta{
				Title:   model.Str(menu.MenuName),
				Icon:    model.Str(menu.Icon),
				NoCache: model.Str(menu.IsCache) == "1",
			},
		}
		cMenus := menu.Children
		if len(cMenus) > 0 && TypeDir == model.Str(menu.MenuType) {
			router.AlwaysShow = true
			router.Redirect = "noRedirect"
			router.Children = s.BuildMenus(cMenus)
		} else if isMenuFrame(menu) {
			router.Meta = nil
			children := &model.RouterVo{
				Path:      model.Str(menu.Path),
				Component: model.Str(menu.Component),
				Name:      capitalize(model.Str(menu.Path)),
				Meta: &model.Meta{
					Title:   model.Str(menu.MenuName),
					Icon:    model.Str(menu.Icon),
					NoCache: model.Str(menu.IsCache) == "1",
				},
			}
			router.Children = []*model.RouterVo{children}
		}
		routers = append(routers, router)
	}
	return routers
}

// GetChildPerms 对应 SysMenuServiceImpl.getChildPerms：按父节点递归装配 children。
func GetChildPerms(list []*model.SysMenu, parentID int64) []*model.SysMenu {
	out := make([]*model.SysMenu, 0)
	for _, t := range list {
		if t.ParentID == parentID {
			recursionFn(list, t)
			out = append(out, t)
		}
	}
	return out
}

func recursionFn(list []*model.SysMenu, t *model.SysMenu) {
	childList := getChildList(list, t)
	t.Children = childList
	for _, child := range childList {
		if len(getChildList(list, child)) > 0 {
			recursionFn(list, child)
		}
	}
}

func getChildList(list []*model.SysMenu, t *model.SysMenu) []*model.SysMenu {
	out := make([]*model.SysMenu, 0)
	for _, n := range list {
		if n.ParentID == t.MenuID {
			out = append(out, n)
		}
	}
	return out
}

// BuildMenuTree 对应 SysMenuServiceImpl.buildMenuTree。
func BuildMenuTree(menus []*model.SysMenu) []*model.SysMenu {
	ids := make(map[int64]struct{}, len(menus))
	for _, m := range menus {
		ids[m.MenuID] = struct{}{}
	}
	out := make([]*model.SysMenu, 0)
	for _, menu := range menus {
		if _, hasParent := ids[menu.ParentID]; !hasParent {
			recursionFn(menus, menu)
			out = append(out, menu)
		}
	}
	if len(out) == 0 {
		return menus
	}
	return out
}

// JAVA 对照: SysMenuServiceImpl.getRouteName:319-326
func routeName(menu *model.SysMenu) string {
	if isMenuFrame(menu) {
		return ""
	}
	return capitalize(model.Str(menu.Path))
}

// JAVA 对照: SysMenuServiceImpl.getRouterPath:334-349
func routerPath(menu *model.SysMenu) string {
	if menu.ParentID == 0 && TypeDir == model.Str(menu.MenuType) && NoFrame == model.Str(menu.IsFrame) {
		return "/" + model.Str(menu.Path)
	}
	if isMenuFrame(menu) {
		return "/"
	}
	return model.Str(menu.Path)
}

// JAVA 对照: SysMenuServiceImpl.getComponent:357-369
func component(menu *model.SysMenu) string {
	comp := Layout
	if model.Str(menu.Component) != "" && !isMenuFrame(menu) {
		comp = model.Str(menu.Component)
	} else if model.Str(menu.Component) == "" && isParentView(menu) {
		comp = ParentView
	}
	return comp
}

// JAVA 对照: SysMenuServiceImpl.isMenuFrame:377-381
func isMenuFrame(menu *model.SysMenu) bool {
	return menu.ParentID == 0 && TypeMenu == model.Str(menu.MenuType) && model.Str(menu.IsFrame) == NoFrame
}

// JAVA 对照: SysMenuServiceImpl.isParentView:389-392
func isParentView(menu *model.SysMenu) bool {
	return menu.ParentID != 0 && TypeDir == model.Str(menu.MenuType)
}

// capitalize 对应 org.apache.commons.lang3.StringUtils.capitalize。
func capitalize(s string) string {
	if s == "" {
		return s
	}
	return strings.ToUpper(s[:1]) + s[1:]
}
