// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/utils/poi/ExcelUtil.java:509-657,1383-1403
// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysUser.java（@Excel 列）
// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysRole.java（@Excel 列）
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/domain/SysPost.java（@Excel 列）
// 类/职责: 用户/角色/岗位的 Excel 导出与用户导入
// 对应 Go 文件: internal/modules/system/excel.go
//
// 关键映射: ExcelUtil.exportExcel(list, sheetName) -> 生成 xlsx 写入 download 目录，
// 返回 AjaxResult.success(filename)（Java 方法重载选中 success(String)，文件名在 msg）。
//
// DIFF: Java 用 POI 逐单元格样式；Go 用 excelize，只保证表头文案/列顺序/取值/文件名规则一致。
// DIFF: 日期单元格在 Go 侧写成格式化字符串（显示效果相同，类型为文本）。
package system

import (
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/google/uuid"
	"github.com/xuri/excelize/v2"

	"car-monit-go/internal/app"
	"car-monit-go/internal/model"
	"car-monit-go/internal/web"
)

// encodingFilename 对应 ExcelUtil.encodingFilename：UUID_工作表名.xlsx。
func encodingFilename(sheetName string) string {
	return uuid.NewString() + "_" + sheetName + ".xlsx"
}

// writeExcel 生成 xlsx 并写入 ruoyi.profile/download，返回文件名。
func writeExcel(a *app.App, sheetName string, headers []string, rows [][]any) (string, error) {
	f := excelize.NewFile()
	defer func() { _ = f.Close() }()

	if err := f.SetSheetName("Sheet1", sheetName); err != nil {
		return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	headerStyle, err := f.NewStyle(&excelize.Style{
		Font:      &excelize.Font{Bold: true},
		Alignment: &excelize.Alignment{Horizontal: "center", Vertical: "center"},
		Fill:      excelize.Fill{Type: "pattern", Pattern: 1, Color: []string{"D0D0D0"}},
	})
	if err != nil {
		return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	for i, h := range headers {
		cell, err := excelize.CoordinatesToCellName(i+1, 1)
		if err != nil {
			return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
		if err := f.SetCellValue(sheetName, cell, h); err != nil {
			return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
		if err := f.SetCellStyle(sheetName, cell, cell, headerStyle); err != nil {
			return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
		if col, err := excelize.ColumnNumberToName(i + 1); err == nil {
			_ = f.SetColWidth(sheetName, col, col, 18)
		}
	}
	for r, row := range rows {
		for i, v := range row {
			cell, err := excelize.CoordinatesToCellName(i+1, r+2)
			if err != nil {
				return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
			}
			if err := f.SetCellValue(sheetName, cell, v); err != nil {
				return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
			}
		}
	}

	filename := encodingFilename(sheetName)
	dir := a.Cfg.RuoYi.DownloadPath()
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	if err := f.SaveAs(filepath.Join(dir, filename)); err != nil {
		return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	return filename, nil
}

// excelDate 把 DateTime 格式化成 Java 的 yyyy-MM-dd HH:mm:ss；nil 输出空串。
func excelDate(dt any) string {
	switch d := dt.(type) {
	case *web.DateTime:
		if d == nil || d.IsZero() {
			return ""
		}
		return d.Format("2006-01-02 15:04:05")
	case *web.ISODateTime:
		if d == nil || d.IsZero() {
			return ""
		}
		return d.Format("2006-01-02 15:04:05")
	}
	return ""
}

// convertExp 对应 ExcelUtil.convertByExp：按 "0=正常,1=停用" 转换展示值，未命中返回原值。
func convertExp(value, exp string) string {
	if value == "" || exp == "" {
		return value
	}
	for _, item := range strings.Split(exp, ",") {
		kv := strings.SplitN(item, "=", 2)
		if len(kv) != 2 {
			continue
		}
		if kv[0] == value {
			return kv[1]
		}
	}
	return value
}

// reverseExp 对应 ExcelUtil.reverseByExp：把中文标签还原成取值，未命中返回原值。
func reverseExp(value, exp string) string {
	if value == "" || exp == "" {
		return value
	}
	for _, item := range strings.Split(exp, ",") {
		kv := strings.SplitN(item, "=", 2)
		if len(kv) != 2 {
			continue
		}
		if kv[1] == value {
			return kv[0]
		}
	}
	return value
}

// ---------------------------------------------------------------------------
// 导出：SysUser / SysRole / SysPost
// JAVA 对照: @Excel 注解的列与 readConverterExp
// ---------------------------------------------------------------------------

// exportUsers 对应 SysUserController.export。
func (s *service) exportUsers(ctx context.Context, q userQuery) (string, error) {
	rows, _, err := s.selectUserList(ctx, q, web.PageDomain{})
	if err != nil {
		return "", err
	}
	headers := []string{
		"用户序号", "用户编码", "登录名称", "用户名称", "用户类型", "用户邮箱", "手机号码",
		"用户性别", "帐号状态", "最后登录IP", "最后登录时间", "证书Id", "证书实体Id",
		"业务id", "业务名称", "单位名称", "租户单位id", "租户单位名称", "角色编码",
		"部门名称", "部门负责人",
	}
	data := make([][]any, 0, len(rows))
	for _, u := range rows {
		deptName, leader := "", ""
		if u.Dept != nil {
			deptName, leader = model.Str(u.Dept.DeptName), model.Str(u.Dept.Leader)
		}
		data = append(data, []any{
			u.UserID, u.UserNo, model.Str(u.UserName), model.Str(u.NickName),
			// JAVA 对照: readConverterExp="1=机构用户2专家3供应商"（缺少分隔逗号，
			// Java 实际把整串当成 1 的标签，这里忠实复刻）。
			convertExp(model.Str(u.UserType), "1=机构用户2专家3供应商"),
			model.Str(u.Email), model.Str(u.Phonenumber),
			convertExp(model.Str(u.Sex), "0=男,1=女,2=未知"),
			convertExp(model.Str(u.Status), "0=正常,1=停用"),
			model.Str(u.LoginIP), excelDate(u.LoginDate),
			model.Str(u.CertID), model.Str(u.CertEntityID), model.Str(u.BussID), model.Str(u.BussName), model.Str(u.EpsName),
			u.TenantID, model.Str(u.TenantName), model.Str(u.RoleCode), deptName, leader,
		})
	}
	return writeExcel(s.app, "用户数据", headers, data)
}

// exportRoles 对应 SysRoleController.export。
func (s *service) exportRoles(ctx context.Context, q roleQuery, lu *model.LoginUser) (string, error) {
	rows, err := s.selectRoleList(ctx, q, lu)
	if err != nil {
		return "", err
	}
	headers := []string{"角色序号", "角色名称", "角色权限", "角色排序", "数据范围", "角色状态"}
	data := make([][]any, 0, len(rows))
	for i := range rows {
		r := rows[i]
		data = append(data, []any{
			r.RoleID, model.Str(r.RoleName), model.Str(r.RoleKey), model.Str(r.RoleSort),
			convertExp(model.Str(r.DataScope), "1=所有数据权限,2=自定义数据权限,3=本部门数据权限,4=本部门及以下数据权限"),
			convertExp(model.Str(r.Status), "0=正常,1=停用"),
		})
	}
	return writeExcel(s.app, "角色数据", headers, data)
}

// exportPosts 对应 SysPostController.export。
func (s *service) exportPosts(ctx context.Context, q postQuery) (string, error) {
	rows, _, err := s.selectPostList(ctx, q, web.PageDomain{})
	if err != nil {
		return "", err
	}
	headers := []string{"岗位序号", "岗位编码", "岗位名称", "岗位排序", "状态"}
	data := make([][]any, 0, len(rows))
	for i := range rows {
		p := rows[i]
		data = append(data, []any{
			p.PostID, model.Str(p.PostCode), model.Str(p.PostName), model.Str(p.PostSort),
			convertExp(model.Str(p.Status), "0=正常,1=停用"),
		})
	}
	return writeExcel(s.app, "岗位数据", headers, data)
}

// ---------------------------------------------------------------------------
// 导入模板 / 导入解析
// JAVA 对照: ExcelUtil.importTemplateExcel("用户数据") / importExcel(file.getInputStream())
// ---------------------------------------------------------------------------

// importUserHeaders 对应 SysUser 中 type != EXPORT 的 @Excel 列（共 18 列）。
var importUserHeaders = []string{
	"用户序号", "用户编码", "部门编号", "登录名称", "用户名称", "用户类型",
	"用户邮箱", "手机号码", "用户性别", "帐号状态", "证书Id", "证书实体Id",
	"业务id", "业务名称", "单位名称", "租户单位id", "租户单位名称", "角色编码",
}

// userImportTemplate 对应 SysUserController.importTemplate。
func (s *service) userImportTemplate() (string, error) {
	f := excelize.NewFile()
	defer func() { _ = f.Close() }()
	if err := f.SetSheetName("Sheet1", "用户数据"); err != nil {
		return "", err
	}
	for i, h := range importUserHeaders {
		cell, err := excelize.CoordinatesToCellName(i+1, 1)
		if err != nil {
			return "", err
		}
		if err := f.SetCellValue("用户数据", cell, h); err != nil {
			return "", err
		}
	}
	filename := encodingFilename("用户数据")
	dir := s.app.Cfg.RuoYi.DownloadPath()
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	if err := f.SaveAs(filepath.Join(dir, filename)); err != nil {
		return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	return filename, nil
}

// parseUserImport 按表头名解析上传的 xlsx（ExcelUtil.importExcel 的等价实现）。
func parseUserImport(r io.Reader) ([]*userBody, error) {
	f, err := excelize.OpenReader(r)
	if err != nil {
		return nil, web.NewServiceError("导入Excel失败：%s", err.Error())
	}
	defer func() { _ = f.Close() }()
	sheets := f.GetSheetList()
	if len(sheets) == 0 {
		return nil, web.NewServiceError("导入Excel失败：工作表为空")
	}
	rows, err := f.GetRows(sheets[0])
	if err != nil {
		return nil, web.NewServiceError("导入Excel失败：%s", err.Error())
	}
	if len(rows) == 0 {
		return nil, web.NewServiceError("导入用户数据不能为空！")
	}
	index := make(map[string]int, len(rows[0]))
	for i, h := range rows[0] {
		index[strings.TrimSpace(h)] = i
	}
	cell := func(row []string, name string) string {
		i, ok := index[name]
		if !ok || i >= len(row) {
			return ""
		}
		return strings.TrimSpace(row[i])
	}
	out := make([]*userBody, 0, len(rows))
	for _, row := range rows[1:] {
		empty := true
		for _, v := range row {
			if strings.TrimSpace(v) != "" {
				empty = false
				break
			}
		}
		// DIFF: Java 会把完全空白的行也尝试入库；Go 跳过全空行，避免产生空账号。
		if empty {
			continue
		}
		b := &userBody{}
		if v := cell(row, "用户序号"); v != "" {
			if n, err := parseIDString(v); err == nil {
				b.UserID = &n
			}
		}
		if v := cell(row, "用户编码"); v != "" {
			if n, err := parseIDString(v); err == nil {
				b.UserNo = &n
			}
		}
		if v := cell(row, "部门编号"); v != "" {
			if n, err := parseIDString(v); err == nil {
				b.DeptID = &n
			}
		}
		setStr := func(p **string, v string) { *p = strPtr(v) }
		setStr(&b.UserName, cell(row, "登录名称"))
		setStr(&b.NickName, cell(row, "用户名称"))
		setStr(&b.UserType, reverseExp(cell(row, "用户类型"), "1=机构用户2专家3供应商"))
		setStr(&b.Email, cell(row, "用户邮箱"))
		setStr(&b.Phonenumber, cell(row, "手机号码"))
		setStr(&b.Sex, reverseExp(cell(row, "用户性别"), "0=男,1=女,2=未知"))
		setStr(&b.Status, reverseExp(cell(row, "帐号状态"), "0=正常,1=停用"))
		setStr(&b.CertID, cell(row, "证书Id"))
		setStr(&b.CertEntityID, cell(row, "证书实体Id"))
		setStr(&b.BussID, cell(row, "业务id"))
		setStr(&b.BussName, cell(row, "业务名称"))
		setStr(&b.EpsName, cell(row, "单位名称"))
		if v := cell(row, "租户单位id"); v != "" {
			if n, err := parseIDString(v); err == nil {
				b.TenantID = &n
			}
		}
		out = append(out, b)
	}
	return out, nil
}

// parseIDString 解析 Excel 数值单元格（excelize 以字符串返回，可能带小数点）。
func parseIDString(raw string) (int64, error) {
	raw = strings.TrimSpace(raw)
	if i := strings.IndexByte(raw, '.'); i >= 0 {
		raw = raw[:i]
	}
	var n int64
	_, err := fmt.Sscanf(raw, "%d", &n)
	return n, err
}
