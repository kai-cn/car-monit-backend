// JAVA 对照: com.ruoyi.common.utils.ImportSysUtil（读 xlsx / 校验头部）
// 类/职责: Excel 导入辅助
// 对应 Go 文件: internal/modules/manager/excel_util.go
//
// DIFF: Java 用 XSSFWorkbook 读取；Go 用 excelize 读取第一个 sheet。
package manager

import (
	"io"
	"strings"

	"github.com/xuri/excelize/v2"

	"car-monit-go/internal/web"
)

// readXlsxRows 读取第一个 sheet 的单元格为字符串矩阵，行下标与表格里一致。
//
// JAVA 对照: POI 的 sheet.getRow(i) 对「没有 <row> 元素」的行返回 null，导入链路据此 break。
// GetRows 会把整行空值的行裁掉，行号就对不上了，所以走 Rows 迭代器：缺行补一条 nil。
func readXlsxRows(r io.Reader) ([][]string, error) {
	f, err := excelize.OpenReader(r)
	if err != nil {
		return nil, web.NewServiceError("读取Excel失败，请确认文件格式！")
	}
	defer func() { _ = f.Close() }()
	sheets := f.GetSheetList()
	if len(sheets) == 0 {
		return nil, web.NewServiceError("读取Excel失败，请确认文件格式！")
	}
	it, err := f.Rows(sheets[0])
	if err != nil {
		return nil, web.NewServiceError("读取Excel失败，请确认文件格式！")
	}
	defer func() { _ = it.Close() }()
	var rows [][]string
	for i := 0; it.Next(); i++ {
		cells, err := it.Columns()
		if err != nil {
			return nil, web.NewServiceError("读取Excel失败，请确认文件格式！")
		}
		if len(cells) == 0 {
			// 缺行（或没有任何单元格的行）：POI 侧 getRow(i) == null
			rows = append(rows, nil)
			continue
		}
		rows = append(rows, cells)
	}
	return rows, nil
}

// sameHeader 对应 colVdaExcel07：逐列比较表头（忽略首尾空白）。
func sameHeader(row []string, headers []string) bool {
	if len(row) < len(headers) {
		return false
	}
	for i, want := range headers {
		if strings.TrimSpace(row[i]) != want {
			return false
		}
	}
	return true
}
